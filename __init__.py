# OPSTYIX TOOLKIT
import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty

from .operators import beat_marker, octane_node_organizer, octane_rename_node, octane_scatter, octane_solo, octane_texture_drop, pulse

bl_info = {
    "name": "OPSTYIX Toolkit",
    "description": "A collection of scripts that makes animating to music just a bit easier :)",
    "author": "OPSTYIX",
    "version": (1, 4, 2),
    "blender": (4, 5, 0),
    "location": "View 3D",
    "warning": "",
    "wiki_url": "",
    "category": "Development"
}

_MODULE_MAP = {
    "enable_beat_marker":           beat_marker,
    "enable_pulse":                 pulse,
    "enable_octane_node_organizer": octane_node_organizer,
    "enable_octane_scatter":        octane_scatter,
    "enable_octane_solo":           octane_solo,
    "enable_octane_texture_drop":   octane_texture_drop,
    "enable_octane_rename_node":    octane_rename_node,
}


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
    _set_module(octane_node_organizer, self.enable_octane_node_organizer)

def _update_octane_scatter(self, context):
    _set_module(octane_scatter, self.enable_octane_scatter)

def _update_octane_solo(self, context):
    _set_module(octane_solo, self.enable_octane_solo)

def _update_octane_texture_drop(self, context):
    _set_module(octane_texture_drop, self.enable_octane_texture_drop)

def _update_octane_rename_node(self, context):
    _set_module(octane_rename_node, self.enable_octane_rename_node)


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
            ]),
        ]

        locked = {"enable_octane_node_organizer"}

        for category, modules in categories:
            layout.label(text=category, icon='DOWNARROW_HLT')
            box = layout.box()
            col = box.column(align=True)
            for prop, desc in modules:
                split = col.split(factor=0.3, align=True)
                split.enabled = prop not in locked
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


def unregister():
    for module in _MODULE_MAP.values():
        try:
            module.unregister()
        except Exception:
            pass
    bpy.utils.unregister_class(OPSTYIXPreferences)


if __name__ == "__main__":
    register()

print("OPSTYIX Toolkit Loaded Successfully!")
