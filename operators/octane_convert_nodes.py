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

_NON_COLOR_SPACE = "Non-Color data"


def _octane_version():
    """Return the OctaneBlender addon version as a tuple, or (0, 0) if unavailable."""
    import sys
    try:
        mod = sys.modules.get("octane")
        if mod is None:
            return (0, 0)
        ver = getattr(mod, "bl_info", {}).get("version", (0, 0))
        return (int(ver[0]), int(ver[1])) if len(ver) >= 2 else (0, 0)
    except Exception:
        return (0, 0)


def _set_linear_node(node):
    """Set Legacy gamma = 1.0 and, on OctaneBlender >= 31.7, Non-Color colorspace."""
    legacy_gamma = node.inputs.get('Legacy gamma')
    if legacy_gamma is not None:
        legacy_gamma.default_value = 1.0
    if _octane_version() >= (31, 7):
        try:
            node.inputs[1].ocio_color_space_name = _NON_COLOR_SPACE
        except Exception:
            pass

# Cycles/EEVEE shader node → Octane equivalent.
# bl_type   : node.type string used to identify the Cycles node
# oct_type  : Octane bl_idname to create
# input_map : {cycles_input_name: octane_input_name}  (unmapped names tried as-is)
# output_map: {cycles_output_name: octane_output_name}
_SHADER_NODE_CONVERSIONS = [
    {
        'bl_type':    'SEPRGB',                  # ShaderNodeSeparateRGB (Blender ≤ 3.x)
        'oct_type':   'OctaneChannelPicker',
        'input_map':  {'Image': 'Texture'},
        'output_map': {'R': 'Texture out', 'G': 'Texture out', 'B': 'Texture out'},
    },
    {
        'bl_type':    'SEPARATE_COLOR',          # ShaderNodeSeparateColor (Blender 4.x)
        'oct_type':   'OctaneChannelPicker',
        'input_map':  {'Color': 'Texture'},
        'output_map': {'Red': 'Texture out', 'Green': 'Texture out', 'Blue': 'Texture out'},
    },
    {
        'bl_type':        'DISPLACEMENT',        # ShaderNodeDisplacement
        'oct_type':       'OctaneTextureDisplacement',
        'input_map':      {'Height': 'Texture'},
        'output_map':     {},
        'uni_mat_socket': 'Displacement',        # wire output to UM instead of Material Output
        'lod_from_image': True,                  # auto-set Level of detail from texture filename
    },
    {
        'bl_type':         'MIX_RGB',            # ShaderNodeMixRGB (Blender ≤ 3.x)
        'oct_type':        'OctaneCyclesMixColorNodeWrapper',
        'input_map':       {},
        'input_idx_map':   {'Color1': 6, 'Color2': 7},
        'output_map':      {},
        'copy_blend_type': True,
    },
    {
        'bl_type':         'MIX',                # ShaderNodeMix with RGBA (Blender 4.x)
        'oct_type':        'OctaneCyclesMixColorNodeWrapper',
        'input_map':       {},
        'input_idx_map':   {'A': 6, 'B': 7},
        'output_map':      {},
        'copy_blend_type': True,
    },
]

# Fast lookup: bl_type → conversion entry
_SHADER_NODE_CONVERSION_MAP = {c['bl_type']: c for c in _SHADER_NODE_CONVERSIONS}


def _wire_dangling_converted_nodes(node_tree, uni_mat, wire_node, kw_map):
    """Wire converted shader nodes (e.g. Channel Picker) that have no outgoing
    connections to the Universal Material.

    Traces forward from Octane image nodes so it works even when the incoming
    link to the converted node failed due to a socket name mismatch.
    """
    if uni_mat is None:
        return 0

    converted_types = {c['oct_type'] for c in _SHADER_NODE_CONVERSIONS}
    octane_img_types = {'OctaneRGBImage', 'OctaneGreyscaleImage'}
    linked_from      = {link.from_node for link in node_tree.links}
    wired = 0

    for img_node in node_tree.nodes:
        if img_node.bl_idname not in octane_img_types:
            continue
        if not getattr(img_node, 'image', None):
            continue

        socket_name = _get_socket_name(img_node.image, kw_map)
        if not socket_name:
            continue

        # Follow outgoing links from this image node to any converted node
        # that has no further outgoing connections.
        for link in node_tree.links:
            if link.from_node != img_node:
                continue
            conv_node = link.to_node
            if conv_node.bl_idname not in converted_types:
                continue
            if conv_node in linked_from:
                continue  # already wired somewhere

            tex_out = conv_node.outputs.get('Texture out') or (
                conv_node.outputs[0] if conv_node.outputs else None
            )
            if tex_out is None:
                continue

            target = wire_node.inputs.get(socket_name)
            if target is None:
                continue

            node_tree.links.new(target, tex_out)
            linked_from.add(conv_node)  # prevent double-wiring
            wired += 1

    return wired


def _remove_normal_map_nodes(node_tree, uni_mat=None, wire_node=None):
    """Delete native Normal Map nodes, bypassing them by rewiring their
    Color input directly to whatever the Normal output was connected to.
    When the Normal output has no connections (e.g. the BSDF was already
    replaced), wire the source texture directly to the Universal Material's
    Normal socket instead."""
    normal_map_nodes = [n for n in node_tree.nodes if n.type == 'NORMAL_MAP']
    for nm_node in normal_map_nodes:
        color_input   = nm_node.inputs.get('Color')
        normal_output = nm_node.outputs.get('Normal')
        if color_input is None or normal_output is None:
            node_tree.nodes.remove(nm_node)
            continue

        from_socket = color_input.links[0].from_socket if color_input.links else None
        to_sockets  = [link.to_socket for link in normal_output.links]

        node_tree.nodes.remove(nm_node)

        if from_socket is None:
            continue

        if to_sockets:
            for to_socket in to_sockets:
                try:
                    node_tree.links.new(to_socket, from_socket)
                except Exception:
                    pass
        elif uni_mat is not None:
            target_node = wire_node or uni_mat
            normal_socket = target_node.inputs.get('Normal')
            if normal_socket is not None:
                try:
                    node_tree.links.new(normal_socket, from_socket)
                except Exception:
                    pass


def _add_shared_transform(node_tree, nodes):
    """Create a shared OctaneTransformValue + OctaneMeshUVProjection and wire
    them to every node in *nodes*. Positioned to the left of the node column."""
    if not nodes:
        return

    min_x = min(n.location.x for n in nodes)
    avg_y = sum(n.location.y for n in nodes) / len(nodes)

    try:
        transform_node = node_tree.nodes.new(type='OctaneTransformValue')
    except RuntimeError:
        return
    transform_node.location = (min_x - 320, avg_y + 100)
    transform_out = transform_node.outputs.get('Transform out') or (
        transform_node.outputs[0] if transform_node.outputs else None
    )

    try:
        projection_node = node_tree.nodes.new(type='OctaneMeshUVProjection')
    except RuntimeError:
        return
    projection_node.location = (min_x - 320, avg_y - 300)
    projection_out = projection_node.outputs.get('Projection out') or (
        projection_node.outputs[0] if projection_node.outputs else None
    )

    for node in nodes:
        if transform_out is not None:
            uv_input = node.inputs.get('UV transform')
            if uv_input is not None:
                node_tree.links.new(uv_input, transform_out)
        if projection_out is not None:
            proj_input = node.inputs.get('Projection')
            if proj_input is not None:
                node_tree.links.new(proj_input, projection_out)


def _align_nodes_vertically(nodes, y_step=475):
    """Stack nodes into a single column, preserving their relative top-to-bottom order."""
    if not nodes:
        return
    sorted_nodes = sorted(nodes, key=lambda n: n.location.y, reverse=True)
    col_x = min(n.location.x for n in sorted_nodes)
    col_y = sorted_nodes[0].location.y
    for i, node in enumerate(sorted_nodes):
        node.location.x = col_x
        node.location.y = col_y - i * y_step


_BLEND_TYPE_MAP = {
    'MIX':          'Mix',
    'DARKEN':       'Darken',
    'MULTIPLY':     'Multiply',
    'BURN':         'Burn',
    'LIGHTEN':      'Lighten',
    'SCREEN':       'Screen',
    'DODGE':        'Dodge',
    'ADD':          'Add',
    'OVERLAY':      'Overlay',
    'SOFT_LIGHT':   'Soft Light',
    'LINEAR_LIGHT': 'Linear Light',
    'DIFFERENCE':   'Difference',
    'EXCLUSION':    'Exclusion',
    'SUBTRACT':     'Subtract',
    'DIVIDE':       'Divide',
    'HUE':          'Hue',
    'SATURATION':   'Saturation',
    'COLOR':        'Color',
    'VALUE':        'Value',
}

_LOD_FROM_FILENAME = [
    (r'(?<![0-9])16[Kk](?![0-9])', 16384),
    (r'(?<![0-9])8[Kk](?![0-9])',   8192),
    (r'(?<![0-9])4[Kk](?![0-9])',   4096),
    (r'(?<![0-9])2[Kk](?![0-9])',   2048),
    (r'(?<![0-9])1[Kk](?![0-9])',   1024),
    (r'(?<![0-9])512(?![0-9])',       512),
]

def _detect_lod(image):
    """Return a LOD integer (e.g. 2048) from the image filename, or None."""
    if image is None:
        return None
    import re
    name = image.name
    for pattern, lod in _LOD_FROM_FILENAME:
        if re.search(pattern, name):
            return lod
    return None


def _replace_shader_node(node_tree, old_node, conversion, uni_mat=None, wire_node=None):
    """Replace old_node using the given conversion entry.
    Preserves incoming and outgoing connections via the socket name maps.
    When conversion has 'uni_mat_socket', the new node's first output is wired
    to that socket on the Universal Material instead of restoring old outgoing links.
    Returns the new node, or None on failure.
    """
    input_map        = conversion.get('input_map',       {})
    input_idx_map    = conversion.get('input_idx_map',   {})
    output_map       = conversion.get('output_map',      {})
    uni_mat_socket   = conversion.get('uni_mat_socket')
    lod_from_image   = conversion.get('lod_from_image',   False)
    copy_blend_type  = conversion.get('copy_blend_type',  False)

    # Save everything needed from old_node before it is removed
    saved_blend_type = getattr(old_node, 'blend_type', None) if copy_blend_type else None

    incoming = [
        (link.from_socket, link.to_socket.name)
        for link in node_tree.links if link.to_node == old_node
    ]
    outgoing = [
        (link.from_socket.name, link.to_socket)
        for link in node_tree.links if link.from_node == old_node
    ]

    try:
        new_node = node_tree.nodes.new(type=conversion['oct_type'])
    except RuntimeError:
        return None

    new_node.location = old_node.location.copy()
    new_node.label    = old_node.label
    node_tree.nodes.remove(old_node)

    for from_socket, old_name in incoming:
        if old_name in input_idx_map:
            idx = input_idx_map[old_name]
            new_input = new_node.inputs[idx] if idx < len(new_node.inputs) else None
        else:
            new_name  = input_map.get(old_name, old_name)
            new_input = new_node.inputs.get(new_name) or (
                new_node.inputs[0] if new_node.inputs else None
            )
        if new_input is not None:
            try:
                node_tree.links.new(new_input, from_socket)
            except Exception:
                pass

    if uni_mat_socket and uni_mat is not None:
        target_node   = wire_node or uni_mat
        target_socket = target_node.inputs.get(uni_mat_socket)
        new_output    = new_node.outputs[0] if new_node.outputs else None
        if target_socket is not None and new_output is not None:
            try:
                node_tree.links.new(target_socket, new_output)
            except Exception:
                pass
    else:
        for old_name, to_socket in outgoing:
            new_name   = output_map.get(old_name, old_name)
            new_output = new_node.outputs.get(new_name) or (
                new_node.outputs[0] if new_node.outputs else None
            )
            if new_output is not None:
                try:
                    node_tree.links.new(to_socket, new_output)
                except Exception:
                    pass

    if lod_from_image:
        image = next(
            (fs.node.image for fs, _ in incoming if hasattr(fs.node, 'image')),
            None,
        )
        lod = _detect_lod(image)
        if lod is not None:
            lod_input = new_node.inputs.get('Level of detail')
            if lod_input is not None:
                try:
                    lod_input.default_value = lod
                except Exception:
                    pass

    if copy_blend_type and saved_blend_type is not None:
        if new_node.inputs:
            try:
                new_node.inputs[0].default_value = _BLEND_TYPE_MAP.get(saved_blend_type, saved_blend_type)
            except Exception:
                pass

    return new_node


def _find_universal_material(node_tree):
    """Return (uni_mat, wire_node) where uni_mat is the OctaneUniversalMaterial
    and wire_node is the node whose inputs to connect to.

    When the Universal Material sits directly in node_tree, wire_node == uni_mat.
    When it lives inside a selected group node, wire_node is the group node —
    because Blender cannot link across node trees, so connections must target
    the group's exposed inputs instead.
    Returns (None, None) if not found.
    """
    # Pass 1: prefer the one connected to the Material Output
    for node in node_tree.nodes:
        if node.type == 'OUTPUT_MATERIAL' and node.target == 'ALL':
            surface = node.inputs.get('Surface')
            if surface and surface.is_linked:
                candidate = surface.links[0].from_node
                if candidate.bl_idname == 'OctaneUniversalMaterial':
                    return candidate, candidate
    # Pass 2: any Universal Material directly in the tree
    for node in node_tree.nodes:
        if node.bl_idname == 'OctaneUniversalMaterial':
            return node, node
    # Pass 3: look inside selected group nodes
    for node in node_tree.nodes:
        if node.select and node.type == 'GROUP' and node.node_tree is not None:
            for inner in node.node_tree.nodes:
                if inner.bl_idname == 'OctaneUniversalMaterial':
                    return inner, node  # wire to group node's exposed inputs
    return None, None


def _convert_node(node_tree, old_node, uni_mat=None, wire_node=None, kw_map=None):
    """Replace a Cycles/EEVEE TEX_IMAGE node with the correct Octane equivalent.

    uni_mat is used for socket name lookup; wire_node is what links are actually
    created on (the group node when the Universal Material lives inside a group).
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
        _set_linear_node(new_node)

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

        # Auto-wire to Universal Material only when the node had no prior outgoing
        # connections — if it was feeding into a processing chain (e.g. Channel Picker)
        # that chain is already restored above and should be left intact.
        if uni_mat is not None and not to_sockets:
            socket_name = _get_socket_name(image, kw_map)
            if socket_name:
                target = (wire_node or uni_mat).inputs.get(socket_name)
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

        uni_mat, wire_node = _find_universal_material(node_tree)
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
            target = wire_node.inputs.get(socket_name)
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
                _set_linear_node(node)
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

        tex_candidates = [
            n for n in node_tree.nodes
            if n.select and n.type == 'TEX_IMAGE'
        ]
        shader_candidates = [
            n for n in node_tree.nodes
            if n.select and n.type in _SHADER_NODE_CONVERSION_MAP
        ]
        if not tex_candidates and not shader_candidates:
            self.report({'WARNING'}, "No convertible Cycles/EEVEE nodes selected.")
            return {'CANCELLED'}

        uni_mat, wire_node = _find_universal_material(node_tree)
        kw_map  = _build_keyword_map()

        rgb_count  = 0
        grey_count = 0
        skip_count = 0
        wired      = 0

        converted_tex_nodes = []
        for old_node in tex_candidates:
            image     = old_node.image
            greyscale = _is_greyscale(image, kw_map)
            new_node  = _convert_node(node_tree, old_node, uni_mat, wire_node, kw_map)
            if new_node is None:
                skip_count += 1
                continue
            converted_tex_nodes.append(new_node)
            if greyscale:
                grey_count += 1
            else:
                rgb_count += 1
            if uni_mat is not None and _get_socket_name(image, kw_map):
                wired += 1

        _align_nodes_vertically(converted_tex_nodes)
        _add_shared_transform(node_tree, converted_tex_nodes)
        _remove_normal_map_nodes(node_tree, uni_mat, wire_node)

        shader_counts = {}
        for old_node in shader_candidates:
            conversion = _SHADER_NODE_CONVERSION_MAP[old_node.type]
            new_node   = _replace_shader_node(node_tree, old_node, conversion, uni_mat, wire_node)
            if new_node is not None:
                label = conversion['oct_type']
                shader_counts[label] = shader_counts.get(label, 0) + 1
            else:
                skip_count += 1

        _wire_dangling_converted_nodes(node_tree, uni_mat, wire_node, kw_map)

        parts = []
        if rgb_count:
            parts.append(f"{rgb_count} → RGB")
        if grey_count:
            parts.append(f"{grey_count} → Greyscale")
        if wired:
            parts.append(f"{wired} wired to Universal Material")
        for oct_type, count in shader_counts.items():
            parts.append(f"{count} → {oct_type}")
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

        _set_linear_node(new_node)

        # Wire to Opacity socket if a Universal Material is present
        uni_mat, wire_node = _find_universal_material(node_tree)
        if uni_mat is not None:
            opacity_socket = wire_node.inputs.get('Opacity')
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


class OPSTYIX_OT_ConvertMaterialToOctane(Operator):
    bl_idname      = "opstyix.convert_material_to_octane"
    bl_label       = "Convert Material to Octane"
    bl_description = (
        "Convert the entire active material from Cycles/EEVEE to Octane. "
        "Replaces Principled BSDF with a Universal Material and converts all "
        "Image Texture nodes to Octane RGB or Greyscale equivalents."
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

        kw_map = _build_keyword_map()

        # ── Replace Principled BSDF(s) with Universal Material(s) ────────────
        principled_nodes = [n for n in node_tree.nodes if n.type == 'BSDF_PRINCIPLED']

        uni_mat    = None
        wire_node  = None
        bsdf_count = 0

        for principled in principled_nodes:
            to_sockets = [
                link.to_socket
                for link in node_tree.links
                if link.from_node == principled
            ]

            new_uni          = node_tree.nodes.new(type='OctaneUniversalMaterial')
            new_uni.location = principled.location.copy()
            new_uni.label    = principled.label
            node_tree.nodes.remove(principled)

            mat_out_socket = new_uni.outputs.get('Material out') or (
                new_uni.outputs[0] if new_uni.outputs else None
            )
            if mat_out_socket:
                for to_socket in to_sockets:
                    try:
                        node_tree.links.new(mat_out_socket, to_socket)
                    except Exception:
                        pass

            if uni_mat is None:
                uni_mat   = new_uni
                wire_node = new_uni
            bsdf_count += 1

        # ── Convert all Image Texture nodes in the tree ───────────────────────
        tex_nodes = [n for n in node_tree.nodes if n.type == 'TEX_IMAGE']

        rgb_count  = 0
        grey_count = 0
        wired      = 0

        converted_tex_nodes = []
        for old_node in tex_nodes:
            image     = old_node.image
            greyscale = _is_greyscale(image, kw_map)
            new_node  = _convert_node(node_tree, old_node, uni_mat, wire_node, kw_map)
            if new_node is None:
                continue
            converted_tex_nodes.append(new_node)
            if greyscale:
                grey_count += 1
            else:
                rgb_count += 1
            if uni_mat is not None and _get_socket_name(image, kw_map):
                wired += 1

        _align_nodes_vertically(converted_tex_nodes)
        _add_shared_transform(node_tree, converted_tex_nodes)
        # ── Remove native Normal Map nodes (Octane wires texture directly) ───
        _remove_normal_map_nodes(node_tree, uni_mat, wire_node)

        # ── Convert other known Cycles shader nodes ───────────────────────────
        shader_counts = {}
        other_nodes = [
            n for n in node_tree.nodes
            if n.type in _SHADER_NODE_CONVERSION_MAP
        ]
        for old_node in other_nodes:
            conversion = _SHADER_NODE_CONVERSION_MAP[old_node.type]
            new_node   = _replace_shader_node(node_tree, old_node, conversion, uni_mat, wire_node)
            if new_node is not None:
                label = conversion['oct_type']
                shader_counts[label] = shader_counts.get(label, 0) + 1

        _wire_dangling_converted_nodes(node_tree, uni_mat, wire_node, kw_map)

        parts = []
        if bsdf_count:
            parts.append(f"{bsdf_count} BSDF → Universal Material")
        if rgb_count:
            parts.append(f"{rgb_count} → RGB")
        if grey_count:
            parts.append(f"{grey_count} → Greyscale")
        if wired:
            parts.append(f"{wired} wired")
        for oct_type, count in shader_counts.items():
            parts.append(f"{count} → {oct_type}")
        if not parts:
            self.report({'WARNING'}, "Nothing to convert.")
            return {'CANCELLED'}

        self.report({'INFO'}, "Converted: " + ", ".join(parts))
        return {'FINISHED'}


# ─── Context Menu ─────────────────────────────────────────────────────────────

class OPSTYIX_OT_SyncMovieFrameDuration(Operator):
    bl_idname      = "opstyix.sync_movie_frame_duration"
    bl_label       = "Sync Movie Frame Duration"
    bl_description = (
        "Set the frame duration on selected Octane image nodes to match "
        "the length of the movie clip loaded in each node"
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

        synced = 0
        skipped = 0

        for node in candidates:
            image = getattr(node, 'image', None)

            if image is None or image.source not in {'MOVIE', 'SEQUENCE'}:
                skipped += 1
                continue

            frame_duration = getattr(image, 'frame_duration', 0)
            if frame_duration < 1:
                skipped += 1
                continue

            try:
                node.frame_duration = frame_duration
            except Exception:
                skipped += 1
                continue
            synced += 1

        parts = []
        if synced:
            parts.append(f"{synced} synced")
        if skipped:
            parts.append(f"{skipped} skipped (no movie clip)")
        self.report({'INFO'}, "Sync Movie Frame Duration: " + ", ".join(parts))
        return {'FINISHED'}


class OPSTYIX_OT_DissolveNode(Operator):
    bl_idname      = "opstyix.dissolve_node"
    bl_label       = "Dissolve Node"
    bl_description = (
        "Remove selected nodes and reconnect their sockets, "
        "preserving the connection chain"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.area is not None
            and context.area.type == 'NODE_EDITOR'
            and bool(context.selected_nodes)
        )

    def execute(self, context):
        node_tree = context.space_data.edit_tree
        if node_tree is None:
            return {'CANCELLED'}

        dissolved = 0

        for node in list(context.selected_nodes):
            # Collect the first linked from_socket for each input, in order
            from_sockets = []
            for inp in node.inputs:
                for link in inp.links:
                    from_sockets.append(link.from_socket)
                    break

            # Collect all to_sockets from all linked outputs, in order
            to_sockets = []
            for out in node.outputs:
                for link in out.links:
                    to_sockets.append(link.to_socket)

            node_tree.nodes.remove(node)

            if not from_sockets or not to_sockets:
                dissolved += 1
                continue

            # Pair each to_socket with the best matching from_socket.
            # Primary: match by index; overflow falls back to the last from_socket.
            for i, to_socket in enumerate(to_sockets):
                from_socket = from_sockets[min(i, len(from_sockets) - 1)]
                try:
                    node_tree.links.new(to_socket, from_socket)
                except Exception:
                    pass

            dissolved += 1

        self.report({'INFO'}, f"Dissolved {dissolved} node(s).")
        return {'FINISHED'}


class OPSTYIX_MT_NodeContextMenu(Menu):
    bl_idname = "OPSTYIX_MT_node_context_menu"
    bl_label  = "OPSTYIX"

    def draw(self, context):
        layout  = self.layout
        node_tree = context.space_data.edit_tree if context.space_data else None
        uni_mat, _ = _find_universal_material(node_tree) if node_tree else (None, None)

        layout.operator("opstyix.convert_material_to_octane",  icon='MATERIAL')
        layout.operator("opstyix.convert_to_octane",          icon='NODE_COMPOSITING')
        row = layout.row()
        row.enabled = uni_mat is not None
        row.operator("opstyix.wire_to_universal_material",    icon='LINKED')
        layout.operator("opstyix.duplicate_as_alpha",         icon='IMAGE_ALPHA')
        layout.operator("opstyix.add_shared_transform",       icon='OBJECT_ORIGIN')
        layout.operator("opstyix.sync_movie_frame_duration",  icon='SEQUENCE')


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
        uni_mat, _ = _find_universal_material(node_tree) if node_tree else (None, None)

        row = layout.row()
        row.scale_y = 1.4
        row.operator(
            "opstyix.convert_material_to_octane",
            text="Convert Material to Octane",
            icon='MATERIAL',
        )

        layout.separator(factor=0.5)

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

        layout.separator(factor=0.5)

        row = layout.row()
        row.scale_y = 1.4
        row.operator(
            "opstyix.sync_movie_frame_duration",
            text="Sync Movie Frame Duration",
            icon='SEQUENCE',
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
    OPSTYIX_OT_ConvertMaterialToOctane,
    OPSTYIX_OT_ConvertToOctane,
    OPSTYIX_OT_DuplicateAsAlpha,
    OPSTYIX_OT_AddSharedTransform,
    OPSTYIX_OT_SyncMovieFrameDuration,
    OPSTYIX_OT_DissolveNode,
    OPSTYIX_MT_NodeContextMenu,
    OPSTYIX_PT_ConvertToOctane,
]

_keymaps = []


def register():
    for cls in CLASSES:
        register_class(cls)
    bpy.types.NODE_MT_context_menu.append(_draw_node_context_menu)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        kmi = km.keymap_items.new(
            'opstyix.dissolve_node', type='X', value='PRESS', ctrl=True
        )
        _keymaps.append((km, kmi))


def unregister():
    for km, kmi in _keymaps:
        km.keymap_items.remove(kmi)
    _keymaps.clear()
    bpy.types.NODE_MT_context_menu.remove(_draw_node_context_menu)
    for cls in reversed(CLASSES):
        unregister_class(cls)


print("octane_convert_nodes.py loaded")
