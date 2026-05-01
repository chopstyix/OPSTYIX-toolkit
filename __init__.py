# OPSTYIX TOOLKIT
import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty

from .operators import beat_marker, octane_node_organizer, octane_rename_node, octane_scatter, octane_solo, octane_swap_image_node, octane_texture_drop, pulse

bl_info = {
    "name": "OPSTYIX Toolkit",
    "description": "A collection of scripts that makes animating to music just a bit easier :)",
    "author": "OPSTYIX",
    "version": (1, 5, 0),
    "blender": (5, 0, 0),
    "location": "View 3D",
    "warning": "",
    "wiki_url": "",
    "category": "Development"
}

_MODULE_MAP = {
    "enable_beat_marker":            beat_marker,
    "enable_pulse":                  pulse,
    "enable_octane_node_organizer":  octane_node_organizer,
    "enable_octane_scatter":         octane_scatter,
    "enable_octane_solo":            octane_solo,
    "enable_octane_texture_drop":    octane_texture_drop,
    "enable_octane_rename_node":     octane_rename_node,
    "enable_octane_swap_image_node": octane_swap_image_node,
}

_OCTANE_MODULES = {
    "enable_octane_node_organizer",
    "enable_octane_scatter",
    "enable_octane_solo",
    "enable_octane_texture_drop",
    "enable_octane_rename_node",
    "enable_octane_swap_image_node",
}

# Stable owner object for msgbus subscription lifetime
_msgbus_owner = object()


def _is_octane():
    scene = getattr(bpy.context, "scene", None)
    return scene is not None and scene.render.engine == "octane"


def _set_module(module, enabled):
    try:
        if enabled:
            module.register()
        else:
            module.unregister()
    except Exception as e:
        print(f"OPSTYIX: module toggle error — {e}")


def _update_beat_marker(self, context):
    _set_module(beat_marker, self.enable_beat_marker)

def _update_pulse(self, context):
    _set_module(pulse, self.enable_pulse)

def _update_octane_node_organizer(self, context):
    _set_module(octane_node_organizer, self.enable_octane_node_organizer and _is_octane())

def _update_octane_scatter(self, context):
    _set_module(octane_scatter, self.enable_octane_scatter and _is_octane())

def _update_octane_solo(self, context):
    _set_module(octane_solo, self.enable_octane_solo and _is_octane())

def _update_octane_texture_drop(self, context):
    _set_module(octane_texture_drop, self.enable_octane_texture_drop and _is_octane())

def _update_octane_rename_node(self, context):
    _set_module(octane_rename_node, self.enable_octane_rename_node and _is_octane())

def _update_octane_swap_image_node(self, context):
    _set_module(octane_swap_image_node, self.enable_octane_swap_image_node and _is_octane())


def _on_engine_change():
    """Called by msgbus whenever scene.render.engine changes."""
    addon = bpy.context.preferences.addons.get(__name__)
    if addon is None:
        return
    prefs = addon.preferences
    is_oct = _is_octane()
    for key in _OCTANE_MODULES:
        module = _MODULE_MAP[key]
        enabled = getattr(prefs, key)
        _set_module(module, enabled and is_oct)


def _subscribe_engine():
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.RenderSettings, "engine"),
        owner=_msgbus_owner,
        args=(),
        notify=_on_engine_change,
    )


@bpy.app.handlers.persistent
def _load_post_handler(_):
    _subscribe_engine()
    _on_engine_change()


class OPSTYIXPreferences(AddonPreferences):
    bl_idname = __name__

    enable_beat_marker: BoolProperty(
        name="Beat Marker",
        description="Enable the Beat Marker module",
        default=True,
        update=_update_beat_marker,
    )
    enable_pulse: BoolProperty(
        name="Pulse",
        description="Enable the Pulse keyframe module",
        default=True,
        update=_update_pulse,
    )
    enable_octane_node_organizer: BoolProperty(
        name="Octane Node Organizer",
        description="Enable the Octane Node Organizer module",
        default=False,
        update=_update_octane_node_organizer,
    )
    enable_octane_scatter: BoolProperty(
        name="Octane Scatter Builder",
        description="Enable the Octane Scatter Builder module",
        default=True,
        update=_update_octane_scatter,
    )
    enable_octane_solo: BoolProperty(
        name="Octane Solo Tool",
        description="Enable the Octane Solo Tool module",
        default=True,
        update=_update_octane_solo,
    )
    enable_octane_texture_drop: BoolProperty(
        name="Octane Texture Drop",
        description="Auto-converts dragged textures to the correct Octane image node type",
        default=True,
        update=_update_octane_texture_drop,
    )
    enable_octane_rename_node: BoolProperty(
        name="Octane Rename Node",
        description="Adds a right-click option to rename an image node to its texture filename",
        default=True,
        update=_update_octane_rename_node,
    )
    enable_octane_swap_image_node: BoolProperty(
        name="Octane Swap Image Node",
        description="Adds a right-click option to swap between RGB and Greyscale image nodes",
        default=True,
        update=_update_octane_swap_image_node,
    )

    def draw(self, context):
        layout = self.layout

        categories = [
            ("General Tools", [
                ("enable_beat_marker", "Creates beat-synced timeline markers"),
                ("enable_pulse",       "Inserts beat-driven keyframes in the Graph Editor"),
            ]),
            ("Octane Specific Tools", [
                ("enable_octane_node_organizer", "Organizes Octane material node trees (Coming Soon)"),
                ("enable_octane_scatter",        "Builds Octane Scatter on Surface node graphs"),
                ("enable_octane_solo",           "Solos an Octane texture node for isolated preview"),
                ("enable_octane_texture_drop",   "Auto-converts dragged textures to the correct Octane image node type"),
                ("enable_octane_rename_node",    "Right-click any image node to rename it to its texture filename"),
                ("enable_octane_swap_image_node", "Right-click any image node to swap between RGB and Greyscale"),
            ]),
        ]

        locked = {"enable_octane_node_organizer"}
        octane_active = _is_octane()

        for category, modules in categories:
            layout.label(text=category, icon='DOWNARROW_HLT')
            box = layout.box()
            col = box.column(align=True)

            is_octane_section = any(prop in _OCTANE_MODULES for prop, _ in modules)
            if is_octane_section and not octane_active:
                col.label(text="Switch render engine to Octane to activate these modules", icon='INFO')

            for prop, desc in modules:
                split = col.split(factor=0.3, align=True)
                split.enabled = prop not in locked and (prop not in _OCTANE_MODULES or octane_active)
                split.prop(self, prop, toggle=True)
                split.label(text=desc)
            layout.separator(factor=0.5)


def register():
    bpy.utils.register_class(OPSTYIXPreferences)
    prefs = bpy.context.preferences.addons[__name__].preferences
    if prefs.enable_beat_marker:
        beat_marker.register()
    if prefs.enable_pulse:
        pulse.register()

    # Octane modules only register if Octane is the active render engine
    is_oct = _is_octane()
    if is_oct:
        if prefs.enable_octane_node_organizer:
            octane_node_organizer.register()
        if prefs.enable_octane_scatter:
            octane_scatter.register()
        if prefs.enable_octane_solo:
            octane_solo.register()
        if prefs.enable_octane_texture_drop:
            octane_texture_drop.register()
        if prefs.enable_octane_rename_node:
            octane_rename_node.register()
        if prefs.enable_octane_swap_image_node:
            octane_swap_image_node.register()

    bpy.app.handlers.load_post.append(_load_post_handler)
    _subscribe_engine()


def unregister():
    bpy.msgbus.clear_by_owner(_msgbus_owner)
    if _load_post_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_load_post_handler)
    for module in _MODULE_MAP.values():
        try:
            module.unregister()
        except Exception:
            pass
    bpy.utils.unregister_class(OPSTYIXPreferences)


if __name__ == "__main__":
    register()

print("OPSTYIX Toolkit Loaded Successfully!")
