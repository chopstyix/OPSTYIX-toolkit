import os
import bpy
import bpy.utils.previews

from bpy.utils import register_class, unregister_class
from bpy.types import Operator, Panel


# ─── State ────────────────────────────────────────────────────────────────────

_solo_state = {
    'old_input':    None,
    'inside_group': False,
    'group_socket': None,
    'material_solo': False,
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _find_from_socket(to_socket):
    """Return the socket that feeds into to_socket, or None."""
    if not to_socket.is_linked:
        return None
    node_tree = to_socket.id_data
    for link in node_tree.links:
        if link.to_socket == to_socket:
            return link.from_socket
    return None


def _find_to_socket(from_socket):
    """Return the socket that from_socket feeds into, or None."""
    if not from_socketW.is_linked:
        return None
    node_tree = from_socket.id_data
    for link in node_tree.links:
        if link.from_socket == from_socket:
            return link.to_socket
    return None


def _hide_unused_sockets(node, keep_inputs=(), keep_outputs=()):
    """Hide all sockets on node except those whose names are in the keep sets."""
    for socket in node.inputs:
        socket.hide = socket.name not in keep_inputs
    for socket in node.outputs:
        socket.hide = socket.name not in keep_outputs


def _get_group_output_node(node_tree):
    """Return the GROUP_OUTPUT node in node_tree, or None."""
    for node in node_tree.nodes:
        if node.type == 'GROUP_OUTPUT':
            return node
    return None


def _get_or_create_material_output(node_tree):
    """Return the first Material Output node targeted to All, creating one if needed."""
    for node in node_tree.nodes:
        if node.type == 'OUTPUT_MATERIAL' and node.target == 'ALL':
            return node
    mat_out = node_tree.nodes.new('ShaderNodeOutputMaterial')
    mat_out.target = 'ALL'
    return mat_out


def _solo_is_active(context):
    """Return True if any solo mode is currently active."""
    if _solo_state['material_solo']:
        return True
    obj = context.active_object
    if obj is None:
        return False
    mat = getattr(obj, "active_material", None)
    if mat is None or mat.node_tree is None:
        return False
    return 'O_SM_DIFF' in mat.node_tree.nodes


# ─── Operators ────────────────────────────────────────────────────────────────

class OPSTYIX_OT_OctaneSolo(Operator):
    bl_idname      = "opstyix.octane_solo"
    bl_label       = "Solo Texture Node"
    bl_description = (
        "Solo the active Octane texture node — routes it through a temporary "
        "emission setup so you can preview it in isolation.\n\n"
        "Run again on any node to exit solo mode and restore the original output."
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
        active_node = context.active_node
        obj         = context.active_object
        if obj is None or obj.active_material is None:
            self.report({'WARNING'}, "No active material.")
            return {'CANCELLED'}

        node_tree = obj.active_material.node_tree

        mat_out = _get_or_create_material_output(node_tree)

        # ── Exit material solo ────────────────────────────────────────────────
        if _solo_state['material_solo']:
            if _solo_state['old_input'] is not None:
                node_tree.links.new(
                    mat_out.inputs['Surface'],
                    _solo_state['old_input'],
                )
            _solo_state['old_input']     = None
            _solo_state['material_solo'] = False
            return {'FINISHED'}

        # ── Exit texture emission solo ─────────────────────────────────────────
        if 'O_SM_DIFF' in node_tree.nodes:
            node_tree.nodes.remove(node_tree.nodes['O_SM_DIFF'])
            node_tree.nodes.remove(node_tree.nodes['O_SM_EM'])

            if _solo_state['inside_group'] and _solo_state['group_socket'] is not None:
                try:
                    context.active_node.id_data.interface.remove(
                        item=_solo_state['group_socket']
                    )
                except Exception:
                    pass

            if _solo_state['old_input'] is not None:
                node_tree.links.new(
                    mat_out.inputs['Surface'],
                    _solo_state['old_input'],
                )

            _solo_state['old_input']    = None
            _solo_state['inside_group'] = False
            _solo_state['group_socket'] = None
            return {'FINISHED'}

        # ── Enter solo mode ───────────────────────────────────────────────────
        if active_node is None:
            self.report({'WARNING'}, "No active node selected.")
            return {'CANCELLED'}

        if not active_node.outputs:
            self.report({'WARNING'}, "Active node has no outputs.")
            return {'CANCELLED'}

        # ── Material node path ────────────────────────────────────────────────
        mat_out_socket = next(
            (s for s in active_node.outputs if s.name == 'Material out'), None
        )
        if mat_out_socket is not None:
            _solo_state['old_input'] = _find_from_socket(mat_out.inputs['Surface'])
            node_tree.links.new(mat_out.inputs['Surface'], mat_out_socket)
            _solo_state['material_solo'] = True
            return {'FINISHED'}

        # ── Texture node path — requires OctaneTextureOutSocket ───────────────
        if active_node.outputs[0].bl_idname != 'OctaneTextureOutSocket':
            self.report({'WARNING'}, "Active node must have an Octane texture or material output.")
            return {'CANCELLED'}

        # Anchor solo nodes below the Material Output node
        anchor_x = mat_out.location.x
        anchor_y = mat_out.location.y - 280

        # Create diffuse shell
        diff_node          = node_tree.nodes.new(type='OctaneDiffuseMaterial')
        diff_node.name     = 'O_SM_DIFF'
        diff_node.location = (anchor_x, anchor_y)
        diff_node.hide     = True
        diff_node.inputs['Diffuse'].default_value = (0.0, 0.0, 0.0)

        # Derive emission power from camera imager exposure so the solo
        # preview is calibrated: power = 1 / exposure.
        try:
            exposure = context.scene.oct_view_cam.imager.exposure
            em_power = 1.0 / exposure if exposure != 0.0 else 1.0
        except Exception:
            em_power = 1.0

        # Create emission node stacked below the diffuse node
        em_node          = node_tree.nodes.new(type='OctaneTextureEmission')
        em_node.name     = 'O_SM_EM'
        em_node.location = (anchor_x, anchor_y - 50)
        em_node.hide     = True
        em_node.inputs['Power'].default_value                         = em_power
        em_node.inputs['Visible on diffuse'].default_value            = False
        em_node.inputs['Visible on specular'].default_value           = False
        em_node.inputs['Visible on scattering volumes'].default_value = False
        em_node.inputs['Cast shadows'].default_value                  = False
        em_node.inputs['Surface brightness'].default_value            = True

        node_tree.links.new(diff_node.inputs['Emission'], em_node.outputs['Emission out'])

        # Save original surface connection
        _solo_state['old_input'] = _find_from_socket(mat_out.inputs['Surface'])
        node_tree.links.new(mat_out.inputs['Surface'], diff_node.outputs['Material out'])

        # Handle group node context
        group_output = _get_group_output_node(active_node.id_data)
        _solo_state['inside_group'] = False

        if group_output is not None:
            _solo_state['inside_group'] = True
            _solo_state['group_socket'] = active_node.id_data.interface.new_socket(
                name='SM_GROUPOUT', in_out='OUTPUT'
            )
            active_node.id_data.links.new(
                active_node.outputs['Texture out'],
                group_output.inputs['SM_GROUPOUT'],
            )
            node_tree.links.new(
                context.material.node_tree.nodes.active.outputs['SM_GROUPOUT'],
                node_tree.nodes['O_SM_EM'].inputs['Texture'],
            )
        else:
            node_tree.links.new(
                em_node.inputs['Texture'],
                node_tree.nodes.active.outputs[0],
            )

        # Hide unused sockets now that all links are in place
        _hide_unused_sockets(diff_node,
            keep_inputs=('Emission',),
            keep_outputs=('Material out',),
        )
        _hide_unused_sockets(em_node,
            keep_inputs=('Texture', 'Power'),
            keep_outputs=('Emission out',),
        )

        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


# ─── Panel ────────────────────────────────────────────────────────────────────

class OPSTYIX_PT_OctaneSolo(Panel):
    bl_label       = "OPSTYIX Solo Tool"
    bl_space_type  = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category    = 'OPSTYIX'

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == 'octane'

    def draw_header(self, context):
        self.layout.label(icon_value=custom_icons["opstyix_icon"].icon_id)

    def draw(self, context):
        layout     = self.layout
        solo_active = _solo_is_active(context)

        if solo_active:
            row = layout.row()
            row.scale_y = 1.4
            row.operator(
                "opstyix.octane_solo",
                text="Exit Solo",
                icon='HIDE_ON',
            )
        else:
            row = layout.row()
            row.scale_y = 1.4
            row.operator(
                "opstyix.octane_solo",
                text="Solo Texture Node",
                icon='HIDE_OFF',
            )

        col = layout.column(align=True)
        col.enabled = False
        col.label(text="Ctrl+Shift+LMB — Solo node", icon='MOUSE_LMB')


# ─── Global Variable ──────────────────────────────────────────────────────────
custom_icons = None

# ─── Keymaps ──────────────────────────────────────────────────────────────────
addon_keymaps = []

# ─── Registration ─────────────────────────────────────────────────────────────

CLASSES = [
    OPSTYIX_OT_OctaneSolo,
    OPSTYIX_PT_OctaneSolo,
]


def register():
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    addon_path = os.path.dirname(__file__)
    icons_dir  = os.path.join(addon_path, "..", "icons")
    custom_icons.load(
        "opstyix_icon", os.path.join(icons_dir, "opstyix_icon.png"), "IMAGE"
    )

    for cls in CLASSES:
        register_class(cls)

    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km  = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        kmi = km.keymap_items.new(
            'opstyix.octane_solo', 'LEFTMOUSE', 'PRESS',
            ctrl=True, alt=False, shift=True, repeat=False,
        )
        addon_keymaps.append((km, kmi))


def unregister():
    global custom_icons
    bpy.utils.previews.remove(custom_icons)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for cls in reversed(CLASSES):
        unregister_class(cls)


print("octane_solo.py loaded")
