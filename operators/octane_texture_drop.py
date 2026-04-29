import bpy

GREYSCALE_KEYWORDS = {
    'roughness', 'bump', 'displacement',
    'specular', 'opacity', 'ao', 'metalness', 'metallic',
}

_node_cache = {}   # {mat.as_pointer(): set of node names}
_converting = False
_timer_pending = False


def _should_be_greyscale(image_name):
    lower = image_name.lower()
    return any(kw in lower for kw in GREYSCALE_KEYWORDS)


def _convert_to_greyscale(node_tree, node):
    image      = node.image
    image_name = image.name if image else ''
    location   = node.location.copy()
    label      = node.label

    new_node          = node_tree.nodes.new('OctaneGreyscaleImage')
    new_node.location = location
    new_node.image    = image
    if label:
        new_node.label = label

    legacy_gamma = new_node.inputs.get('Legacy gamma')
    if legacy_gamma is not None:
        legacy_gamma.default_value = 1.0

    node_tree.nodes.remove(node)
    print(f"OPSTYIX: converted '{label or image_name}' → OctaneGreyscaleImage")


def _init_cache():
    for mat in bpy.data.materials:
        if mat.use_nodes and mat.node_tree:
            _node_cache[mat.as_pointer()] = {n.name for n in mat.node_tree.nodes}
    return None


def _deferred_check():
    """Runs in the main loop timer where bpy.data is fully accessible."""
    global _converting, _timer_pending
    _timer_pending = False

    if _converting:
        return None

    to_convert = []

    for mat in bpy.data.materials:
        if not mat.use_nodes or not mat.node_tree:
            continue

        ptr           = mat.as_pointer()
        nodes         = mat.node_tree.nodes
        current_names = {n.name for n in nodes}
        cached_names  = _node_cache.get(ptr, None)

        if cached_names is None:
            _node_cache[ptr] = current_names
            continue

        new_names = current_names - cached_names
        _node_cache[ptr] = current_names

        for name in new_names:
            node = nodes.get(name)
            if node and node.bl_idname == 'OctaneRGBImage' and node.image:
                if _should_be_greyscale(node.image.name):
                    to_convert.append((mat.node_tree, node))

    if to_convert:
        _converting = True
        try:
            for node_tree, node in to_convert:
                _convert_to_greyscale(node_tree, node)
        finally:
            _converting = False

        for mat in bpy.data.materials:
            if mat.use_nodes and mat.node_tree:
                _node_cache[mat.as_pointer()] = {n.name for n in mat.node_tree.nodes}

    return None  # returning None unregisters the timer


def _on_depsgraph_update(scene, depsgraph):
    global _timer_pending
    if _timer_pending or _converting:
        return
    _timer_pending = True
    bpy.app.timers.register(_deferred_check, first_interval=0.0)


def register():
    bpy.app.timers.register(_init_cache, first_interval=0.0)
    if _on_depsgraph_update not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update)


def unregister():
    if _on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update)
    _node_cache.clear()
