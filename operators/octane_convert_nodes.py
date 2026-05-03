import os
import re
import bpy
from bpy.types import Operator, Panel, Menu
from bpy.utils import register_class, unregister_class


# Fixed per-category metadata: attr_name → (is_greyscale, socket_name, default_keywords)
# attr_name matches the fields on OctaneConvertTagsPreferences in __init__.py
_CATEGORY_DEFS = {
    'albedo':         (False, 'Albedo',           "diffuse diff albedo color col basecolor base bc"),
    'roughness':      (True,  'Roughness',        "rough roughness rgh gloss glossiness"),
    'metallic':       (True,  'Metallic',         "metal metallic metalness mtl"),
    'normal':         (False, 'Normal',           "normal nrm nor nml"),
    'bump':           (True,  'Bump',             "bump bmp"),
    'displacement':   (True,  'Displacement',     "height displacement disp"),
    'opacity':        (True,  'Opacity',          "opacity alpha transparency trans"),
    'emission':       (False, 'Emission',         "emission emissive emit"),
    'specular':       (True,  'Specular',         "spec specular"),
    'subsurface':     (False, 'Subsurface color', "sss subsurface"),
    'greyscale_only': (True,  None,               "ao ambientocclusion occlusion cavity mask thickness"),
}


def _get_convert_tags():
    """Return the OctaneConvertTagsPreferences instance, or None."""
    for addon in bpy.context.preferences.addons.values():
        if hasattr(addon.preferences, 'octane_convert_tags'):
            return addon.preferences.octane_convert_tags
    return None


def _build_keyword_map():
    """Build keyword → (is_greyscale, socket_name) from prefs, falling back to defaults."""
    tags = _get_convert_tags()
    result = {}
    for attr, (is_grey, socket, defaults) in _CATEGORY_DEFS.items():
        kw_str = defaults
        if tags is not None and hasattr(tags, attr):
            kw_str = getattr(tags, attr) or defaults
        for kw in kw_str.lower().split():
            result[kw] = (is_grey, socket)
    return result


def _parse_stem(image):
    """Return the lowercase filename parts split on common separators."""
    if image is None:
        return []
    raw  = image.filepath or image.name
    stem = os.path.splitext(os.path.basename(raw))[0].lower()
    return re.split(r'[_\-\.\s]+', stem)


def _stem_suffix(image):
    """Return only the last part of the filename stem — where the map type lives."""
    parts = _parse_stem(image)
    return parts[-1] if parts else ''


def _is_greyscale(image, kw_map):
    grey_kws = {kw for kw, (grey, _) in kw_map.items() if grey}
    return _stem_suffix(image) in grey_kws


def _get_socket_name(image, kw_map):
    """Return the Universal Material socket name for this image, or None."""
    entry = kw_map.get(_stem_suffix(image))
    return entry[1] if entry is not None else None


def _get_map_label(image, kw_map):
    """Return a tidy display label derived from the filename suffix, or None."""
    suffix = _stem_suffix(image)
    entry  = kw_map.get(suffix)
    if entry is None:
        return None
    socket = entry[1]
    if socket is not None:
        return socket
    # greyscale_only: no socket — format the keyword itself
    return suffix.upper() if len(suffix) <= 3 else suffix.title()


# RGB sockets that represent linear-space data and need Legacy gamma = 1.0
_LINEAR_SOCKETS = {'Roughness', 'Metallic', 'Specular', 'Bump', 'Normal',
                   'Displacement', 'Opacity'}


def _find_universal_material(node_tree):
    """Return the OctaneUniversalMaterial node wired to the Material Output,
    or the first one found in the tree, or None."""
    for node in node_tree.nodes:
        if node.type == 'OUTPUT_MATERIAL' and node.target == 'ALL':
            surface = node.inputs.get('Surface')
            if surface and surface.is_linked:
                candidate = surface.links[0].from_node
                if candidate.bl_idname == 'OctaneUniversalMaterial':
                    return candidate
    for node in node_tree.nodes:
        if node.bl_idname == 'OctaneUniversalMaterial':
            return node
    return None


def _convert_node(node_tree, old_node, uni_mat=None, kw_map=None):
    """Replace a Cycles/EEVEE TEX_IMAGE node with the correct Octane equivalent.

    If uni_mat is supplied, also wires the new node into the matching socket.
    Returns the new node, or None if conversion failed.
    """
    if kw_map is None:
        kw_map = _build_keyword_map()
    image     = old_node.image
    greyscale = _is_greyscale(image, kw_map)
    node_type = 'OctaneGreyscaleImage' if greyscale else 'OctaneRGBImage'

    # Save destinations of every outgoing link before the node is removed.
    to_sockets = [
        link.to_socket
        for link in node_tree.links
        if link.from_node == old_node
    ]

    new_node          = node_tree.nodes.new(type=node_type)
    new_node.location = old_node.location.copy()
    new_node.label    = _get_map_label(image, kw_map) or old_node.label

    if image is not None:
        new_node.image = image

    socket_name = _get_socket_name(image, kw_map)
    if greyscale or socket_name in _LINEAR_SOCKETS:
        legacy_gamma = new_node.inputs.get('Legacy gamma')
        if legacy_gamma is not None:
            legacy_gamma.default_value = 1.0

    node_tree.nodes.remove(old_node)

    tex_out = new_node.outputs.get('Texture out') or (
        new_node.outputs[0] if new_node.outputs else None
    )

    if tex_out:
        # Restore any pre-existing outgoing connections
        for to_socket in to_sockets:
            try:
                node_tree.links.new(tex_out, to_socket)
            except Exception:
                pass

        # Wire into the Universal Material if one is present
        if uni_mat is not None:
            socket_name = _get_socket_name(image, kw_map)
            if socket_name:
                target = uni_mat.inputs.get(socket_name)
                if target is not None:
                    node_tree.links.new(target, tex_out)

    return new_node


# ─── Operators ────────────────────────────────────────────────────────────────

class OPSTYIX_OT_WireToUniversalMaterial(Operator):
    bl_idname      = "opstyix.wire_to_universal_material"
    bl_label       = "Wire to Universal Material"
    bl_description = (
        "Connect selected Octane image nodes to their matching sockets on the "
        "Universal Material, based on each node's image filename."
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        sd = context.space_data
        return (
            context.scene.render.engine == 'octane'
            and context.area is not None
            and context.area.type == 'NODE_EDITOR'
            and getattr(sd, 'tree_type', None) == 'ShaderNodeTree'
        )

    def execute(self, context):
        node_tree = context.space_data.edit_tree
        if node_tree is None:
            self.report({'WARNING'}, "No active node tree.")
            return {'CANCELLED'}

        octane_types = {'OctaneRGBImage', 'OctaneGreyscaleImage'}
        candidates = [
            n for n in node_tree.nodes
            if n.select and n.bl_idname in octane_types
        ]
        if not candidates:
            self.report({'WARNING'}, "No Octane image nodes selected.")
            return {'CANCELLED'}

        uni_mat = _find_universal_material(node_tree)
        if uni_mat is None:
            self.report({'WARNING'}, "No Universal Material found in this node tree.")
            return {'CANCELLED'}

        kw_map = _build_keyword_map()
        wired  = 0
        skip   = 0

        for node in candidates:
            image = node.image
            socket_name = _get_socket_name(image, kw_map)
            if not socket_name:
                skip += 1
                continue
            target = uni_mat.inputs.get(socket_name)
            if target is None:
                skip += 1
                continue
            tex_out = node.outputs.get('Texture out') or (
                node.outputs[0] if node.outputs else None
            )
            if tex_out is None:
                skip += 1
                continue
            node_tree.links.new(target, tex_out)
            if socket_name in _LINEAR_SOCKETS:
                legacy_gamma = node.inputs.get('Legacy gamma')
                if legacy_gamma is not None:
                    legacy_gamma.default_value = 1.0
            wired += 1

        parts = []
        if wired:
            parts.append(f"{wired} wired")
        if skip:
            parts.append(f"{skip} skipped (no matching socket)")
        self.report({'INFO'}, "Wire to Universal Material: " + ", ".join(parts))
        return {'FINISHED'}


class OPSTYIX_OT_ConvertToOctane(Operator):
    bl_idname      = "opstyix.convert_to_octane"
    bl_label       = "Convert to Octane Image Nodes"
    bl_description = (
        "Convert selected Cycles/EEVEE Image Texture nodes to Octane RGB or "
        "Greyscale image nodes. If a Universal Material is connected to the "
        "Material Output, each node is also wired to its matching socket."
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        sd = context.space_data
        return (
            context.scene.render.engine == 'octane'
            and context.area is not None
            and context.area.type == 'NODE_EDITOR'
            and getattr(sd, 'tree_type', None) == 'ShaderNodeTree'
        )

    def execute(self, context):
        node_tree = context.space_data.edit_tree
        if node_tree is None:
            self.report({'WARNING'}, "No active node tree.")
            return {'CANCELLED'}

        candidates = [
            n for n in node_tree.nodes
            if n.select and n.type == 'TEX_IMAGE'
        ]
        if not candidates:
            self.report({'WARNING'}, "No Cycles/EEVEE Image Texture nodes selected.")
            return {'CANCELLED'}

        uni_mat = _find_universal_material(node_tree)
        kw_map  = _build_keyword_map()

        rgb_count  = 0
        grey_count = 0
        skip_count = 0
        wired      = 0

        for old_node in candidates:
            image     = old_node.image
            greyscale = _is_greyscale(image, kw_map)
            new_node  = _convert_node(node_tree, old_node, uni_mat, kw_map)
            if new_node is None:
                skip_count += 1
                continue
            if greyscale:
                grey_count += 1
            else:
                rgb_count += 1
            if uni_mat is not None and _get_socket_name(image, kw_map):
                wired += 1

        parts = []
        if rgb_count:
            parts.append(f"{rgb_count} → RGB")
        if grey_count:
            parts.append(f"{grey_count} → Greyscale")
        if wired:
            parts.append(f"{wired} wired to Universal Material")
        if skip_count:
            parts.append(f"{skip_count} skipped")

        self.report({'INFO'}, "Converted: " + ", ".join(parts))
        return {'FINISHED'}


class OPSTYIX_OT_DuplicateAsAlpha(Operator):
    bl_idname      = "opstyix.duplicate_as_alpha"
    bl_label       = "Duplicate as Alpha Node"
    bl_description = (
        "Duplicate the active Octane image node as a Greyscale node reading "
        "the alpha channel. Sets Legacy gamma to 1.0 and wires it to the "
        "Opacity socket of the Universal Material if one is present."
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        sd      = context.space_data
        active  = context.active_node
        return (
            context.scene.render.engine == 'octane'
            and context.area is not None
            and context.area.type == 'NODE_EDITOR'
            and getattr(sd, 'tree_type', None) == 'ShaderNodeTree'
            and active is not None
            and active.bl_idname in {'OctaneRGBImage', 'OctaneGreyscaleImage'}
        )

    def execute(self, context):
        node_tree = context.space_data.edit_tree
        if node_tree is None:
            self.report({'WARNING'}, "No active node tree.")
            return {'CANCELLED'}

        source = context.active_node
        if source is None or source.bl_idname not in {'OctaneRGBImage', 'OctaneGreyscaleImage'}:
            self.report({'WARNING'}, "Active node must be an Octane image node.")
            return {'CANCELLED'}

        new_node          = node_tree.nodes.new(type='OctaneGreyscaleImage')
        new_node.location = (source.location.x, source.location.y - 180)
        if source.image is not None:
            new_node.image = source.image

        base_label        = source.label or (source.image.name if source.image else 'Image')
        new_node.label    = f"{base_label} — Alpha"

        # Select alpha channel if the node exposes a Channel input
        channel = new_node.inputs.get('Channel')
        if channel is not None:
            try:
                channel.default_value = 'A'
            except Exception:
                pass

        legacy_gamma = new_node.inputs.get('Legacy gamma')
        if legacy_gamma is not None:
            legacy_gamma.default_value = 1.0

        # Wire to Opacity socket if a Universal Material is present
        uni_mat = _find_universal_material(node_tree)
        if uni_mat is not None:
            opacity_socket = uni_mat.inputs.get('Opacity')
            tex_out        = new_node.outputs.get('Texture out') or (
                new_node.outputs[0] if new_node.outputs else None
            )
            if opacity_socket is not None and tex_out is not None:
                node_tree.links.new(opacity_socket, tex_out)
                self.report({'INFO'}, "Alpha node created and wired to Opacity.")
                return {'FINISHED'}

        self.report({'INFO'}, "Alpha node created.")
        return {'FINISHED'}


class OPSTYIX_OT_AddSharedTransform(Operator):
    bl_idname      = "opstyix.add_shared_transform"
    bl_label       = "Add Shared Transform & Projection"
    bl_description = (
        "Create a shared 3D Transformation node and a Mesh UV Projection node, "
        "connecting each to all selected Octane image nodes."
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        sd = context.space_data
        return (
            context.scene.render.engine == 'octane'
            and context.area is not None
            and context.area.type == 'NODE_EDITOR'
            and getattr(sd, 'tree_type', None) == 'ShaderNodeTree'
        )

    def execute(self, context):
        node_tree = context.space_data.edit_tree
        if node_tree is None:
            self.report({'WARNING'}, "No active node tree.")
            return {'CANCELLED'}

        octane_types = {'OctaneRGBImage', 'OctaneGreyscaleImage'}
        candidates = [
            n for n in node_tree.nodes
            if n.select and n.bl_idname in octane_types
        ]
        if not candidates:
            self.report({'WARNING'}, "No Octane image nodes selected.")
            return {'CANCELLED'}

        min_x = min(n.location.x for n in candidates)
        avg_y = sum(n.location.y for n in candidates) / len(candidates)

        # ── 3D Transform ──────────────────────────────────────────────────────
        try:
            transform_node = node_tree.nodes.new(type='OctaneTransformValue')
        except RuntimeError as e:
            self.report({'ERROR'}, f"Could not create transform node: {e}")
            return {'CANCELLED'}

        transform_node.location = (min_x - 280, avg_y + 100)

        transform_out = transform_node.outputs.get('Transform out') or (
            transform_node.outputs[0] if transform_node.outputs else None
        )

        # ── Mesh UV Projection ────────────────────────────────────────────────
        try:
            projection_node = node_tree.nodes.new(type='OctaneMeshUVProjection')
        except RuntimeError as e:
            self.report({'ERROR'}, f"Could not create projection node: {e}")
            return {'CANCELLED'}

        projection_node.location = (min_x - 280, avg_y - 300)

        projection_out = projection_node.outputs.get('Projection out') or (
            projection_node.outputs[0] if projection_node.outputs else None
        )

        # ── Wire both to every candidate ──────────────────────────────────────
        transform_count  = 0
        projection_count = 0

        for node in candidates:
            if transform_out is not None:
                uv_input = node.inputs.get('UV transform')
                if uv_input is not None:
                    node_tree.links.new(uv_input, transform_out)
                    transform_count += 1

            if projection_out is not None:
                proj_input = node.inputs.get('Projection')
                if proj_input is not None:
                    node_tree.links.new(proj_input, projection_out)
                    projection_count += 1

        self.report(
            {'INFO'},
            f"Transform → {transform_count} node(s), Projection → {projection_count} node(s)."
        )
        return {'FINISHED'}


# ─── Context Menu ─────────────────────────────────────────────────────────────

class OPSTYIX_MT_NodeContextMenu(Menu):
    bl_idname = "OPSTYIX_MT_node_context_menu"
    bl_label  = "OPSTYIX"

    def draw(self, context):
        layout  = self.layout
        node_tree = context.space_data.edit_tree if context.space_data else None
        uni_mat   = _find_universal_material(node_tree) if node_tree else None

        layout.operator("opstyix.convert_to_octane",          icon='NODE_COMPOSITING')
        row = layout.row()
        row.enabled = uni_mat is not None
        row.operator("opstyix.wire_to_universal_material",    icon='LINKED')
        layout.operator("opstyix.duplicate_as_alpha",         icon='IMAGE_ALPHA')
        layout.operator("opstyix.add_shared_transform",       icon='OBJECT_ORIGIN')


def _draw_node_context_menu(self, context):
    if context.scene.render.engine != 'octane':
        return
    self.layout.separator()
    self.layout.menu("OPSTYIX_MT_node_context_menu", icon='TOOL_SETTINGS')


# ─── Panel ────────────────────────────────────────────────────────────────────

class OPSTYIX_PT_ConvertToOctane(Panel):
    bl_label       = "OPSTYIX Convert Nodes"
    bl_space_type  = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category    = 'OPSTYIX'

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == 'octane'

    def draw(self, context):
        layout = self.layout

        node_tree = context.space_data.edit_tree if context.space_data else None
        uni_mat   = _find_universal_material(node_tree) if node_tree else None

        row = layout.row()
        row.scale_y = 1.4
        row.operator(
            "opstyix.convert_to_octane",
            text="Convert Selected to Octane",
            icon='NODE_COMPOSITING',
        )

        layout.separator(factor=0.5)

        row = layout.row()
        row.scale_y = 1.4
        row.enabled = uni_mat is not None
        row.operator(
            "opstyix.wire_to_universal_material",
            text="Wire to Universal Material",
            icon='LINKED',
        )

        layout.separator(factor=0.5)

        row = layout.row()
        row.scale_y = 1.4
        row.operator(
            "opstyix.duplicate_as_alpha",
            text="Duplicate as Alpha Node",
            icon='IMAGE_ALPHA',
        )

        layout.separator(factor=0.5)

        row = layout.row()
        row.scale_y = 1.4
        row.operator(
            "opstyix.add_shared_transform",
            text="Add Shared Transform & Projection",
            icon='OBJECT_ORIGIN',
        )

        col = layout.column(align=True)
        col.enabled = False
        col.label(text="Select Cycles/EEVEE Image Texture nodes,", icon='INFO')
        col.label(text="then click to convert to Octane equivalents.")
        if uni_mat is not None:
            col.label(text="Universal Material found: will auto-wire.", icon='LINKED')
        else:
            col.label(text="No Universal Material — skipping auto-wire.", icon='UNLINKED')


# ─── Registration ─────────────────────────────────────────────────────────────

CLASSES = [
    OPSTYIX_OT_WireToUniversalMaterial,
    OPSTYIX_OT_ConvertToOctane,
    OPSTYIX_OT_DuplicateAsAlpha,
    OPSTYIX_OT_AddSharedTransform,
    OPSTYIX_MT_NodeContextMenu,
    OPSTYIX_PT_ConvertToOctane,
]


def register():
    for cls in CLASSES:
        register_class(cls)
    bpy.types.NODE_MT_context_menu.append(_draw_node_context_menu)


def unregister():
    bpy.types.NODE_MT_context_menu.remove(_draw_node_context_menu)
    for cls in reversed(CLASSES):
        unregister_class(cls)


print("octane_convert_nodes.py loaded")
