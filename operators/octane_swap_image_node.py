import bpy

_RGB_TYPE   = 'OctaneRGBImage'
_GREY_TYPE  = 'OctaneGreyscaleImage'

_SWAP_TYPES = {_RGB_TYPE, _GREY_TYPE}


def _active_swappable_node(context):
    node = getattr(context, 'active_node', None)
    return node if (node and node.bl_idname in _SWAP_TYPES) else None


class OPSTYIX_OT_swap_image_node(bpy.types.Operator):
    bl_idname = "opstyix.swap_image_node"
    bl_label = "Swap RGB ↔ Greyscale"
    bl_description = "Convert this node between OctaneRGBImage and OctaneGreyscaleImage"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _active_swappable_node(context) is not None

    def execute(self, context):
        node = _active_swappable_node(context)
        if node is None:
            return {'CANCELLED'}

        node_tree = context.active_node.id_data
        target_type = _GREY_TYPE if node.bl_idname == _RGB_TYPE else _RGB_TYPE

        image      = node.image
        image_name = image.name if image else ''
        location   = node.location.copy()
        label      = node.label

        # capture output links before removal
        out_links = [
            (link.from_socket.identifier, link.to_socket)
            for link in node.outputs[0].links
        ] if node.outputs else []

        new_node          = node_tree.nodes.new(target_type)
        new_node.location = location
        new_node.image    = image
        if label:
            new_node.label = label

        if target_type == _GREY_TYPE:
            legacy_gamma = new_node.inputs.get('Legacy gamma')
            if legacy_gamma is not None:
                legacy_gamma.default_value = 1.0

        node_tree.nodes.remove(node)

        # reconnect outputs
        if new_node.outputs and out_links:
            out_socket = new_node.outputs[0]
            for _, to_socket in out_links:
                try:
                    node_tree.links.new(out_socket, to_socket)
                except Exception:
                    pass

        # apply color after all node operations
        if target_type == _GREY_TYPE:
            new_node.use_custom_color = True
            new_node.color = (0.35, 0.35, 0.35)
        else:
            new_node.use_custom_color = False

        node_tree.update_tag()
        for area in context.screen.areas:
            if area.type == 'NODE_EDITOR':
                area.tag_redraw()

        direction = "→ Greyscale" if target_type == _GREY_TYPE else "→ RGB"
        print(f"OPSTYIX: swapped '{label or image_name}' {direction}")
        return {'FINISHED'}


def _draw_context_menu(self, context):
    if _active_swappable_node(context) is not None:
        self.layout.separator()
        self.layout.operator(OPSTYIX_OT_swap_image_node.bl_idname)


def register():
    bpy.utils.register_class(OPSTYIX_OT_swap_image_node)
    bpy.types.NODE_MT_context_menu.append(_draw_context_menu)


def unregister():
    bpy.types.NODE_MT_context_menu.remove(_draw_context_menu)
    bpy.utils.unregister_class(OPSTYIX_OT_swap_image_node)
