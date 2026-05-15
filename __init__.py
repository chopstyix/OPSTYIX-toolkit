# OPSTYIX TOOLKIT
import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, PointerProperty, StringProperty

from .operators import beat_marker, lens_shift, object_utils, octane_convert_nodes, octane_node_organizer, octane_rename_node, octane_scatter, octane_solo, octane_swap_image_node, octane_texture_drop, pulse

bl_info = {
    "name": "OPSTYIX Toolkit",
    "description": "A collection of scripts that makes animating to music just a bit easier :)",
    "author": "OPSTYIX",
    "version": (1, 5, 0),
    "blender": (4, 5, 0),
    "location": "View 3D",
    "warning": "",
    "wiki_url": "",
    "category": "Development"
}

_MODULE_MAP = {
    "enable_beat_marker":             beat_marker,
    "enable_pulse":                   pulse,
    "enable_lens_shift":              lens_shift,
    "enable_object_utils":            object_utils,
    "enable_octane_node_organizer":   octane_node_organizer,
    "enable_octane_scatter":          octane_scatter,
    "enable_octane_solo":             octane_solo,
    "enable_octane_texture_drop":     octane_texture_drop,
    "enable_octane_rename_node":      octane_rename_node,
    "enable_octane_swap_image_node":  octane_swap_image_node,
    "enable_octane_convert_nodes":    octane_convert_nodes,
}

_OCTANE_MODULES = {
    "enable_octane_node_organizer",
    "enable_octane_scatter",
    "enable_octane_solo",
    "enable_octane_texture_drop",
    "enable_octane_rename_node",
    "enable_octane_swap_image_node",
    "enable_octane_convert_nodes",
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

def _update_lens_shift(self, context):
    _set_module(lens_shift, self.enable_lens_shift)

def _update_object_utils(self, context):
    _set_module(object_utils, self.enable_object_utils)

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

def _update_octane_convert_nodes(self, context):
    _set_module(octane_convert_nodes, self.enable_octane_convert_nodes and _is_octane())


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


class OctaneConvertTagsPreferences(bpy.types.PropertyGroup):
    albedo: StringProperty(
        name="Albedo / Base Color",
        description="Space-separated keywords that identify albedo/diffuse/base-color textures",
        default="diffuse diff albedo color col basecolor base bc",
    )
    roughness: StringProperty(
        name="Roughness",
        description="Space-separated keywords that identify roughness/gloss textures",
        default="rough roughness rgh gloss glossiness",
    )
    metallic: StringProperty(
        name="Metallic",
        description="Space-separated keywords that identify metallic/metalness textures",
        default="metal metallic metalness mtl",
    )
    normal: StringProperty(
        name="Normal",
        description="Space-separated keywords that identify normal map textures",
        default="normal nrm nor nml",
    )
    bump: StringProperty(
        name="Bump",
        description="Space-separated keywords that identify bump map textures",
        default="bump bmp",
    )
    displacement: StringProperty(
        name="Displacement",
        description="Space-separated keywords that identify displacement/height textures",
        default="height displacement disp",
    )
    opacity: StringProperty(
        name="Opacity",
        description="Space-separated keywords that identify opacity/alpha textures",
        default="opacity alpha transparency trans",
    )
    emission: StringProperty(
        name="Emission",
        description="Space-separated keywords that identify emission textures",
        default="emission emissive emit",
    )
    specular: StringProperty(
        name="Specular",
        description="Space-separated keywords that identify specular textures",
        default="spec specular",
    )
    subsurface: StringProperty(
        name="Subsurface",
        description="Space-separated keywords that identify subsurface/SSS textures",
        default="sss subsurface",
    )
    greyscale_only: StringProperty(
        name="Greyscale (no socket)",
        description="Keywords for greyscale textures that have no Universal Material socket (AO, cavity, mask…)",
        default="ao ambientocclusion occlusion cavity mask thickness",
    )


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
    enable_lens_shift: BoolProperty(
        name="Lens Shift",
        description="Adds Lens Shift V/H controls with framing compensation to the Camera Data Properties panel",
        default=True,
        update=_update_lens_shift,
    )
    enable_object_utils: BoolProperty(
        name="Object Utilities",
        description="Adds extra options to the 3D Viewport right-click menu",
        default=True,
        update=_update_object_utils,
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
    enable_octane_convert_nodes: BoolProperty(
        name="Octane Convert Nodes",
        description="Converts selected Cycles/EEVEE Image Texture nodes to Octane RGB or Greyscale nodes",
        default=True,
        update=_update_octane_convert_nodes,
    )
    show_octane_convert_tags: BoolProperty(
        name="Edit texture detection tags",
        description="Expand to customise the filename keywords used when converting nodes",
        default=False,
    )
    octane_convert_tags: PointerProperty(type=OctaneConvertTagsPreferences)

    def draw(self, context):
        layout = self.layout

        categories = [
            ("General Tools", [
                ("enable_beat_marker",  "Creates beat-synced timeline markers"),
                ("enable_pulse",        "Inserts beat-driven keyframes in the Graph Editor"),
                ("enable_lens_shift",   "Adds Lens Shift controls to the Camera Data Properties panel"),
                ("enable_object_utils", "Adds extra options to the 3D Viewport right-click menu"),
            ]),
            ("Octane Specific Tools", [
                ("enable_octane_node_organizer",  "Organizes Octane material node trees (Coming Soon)"),
                ("enable_octane_scatter",         "Builds Octane Scatter on Surface node graphs"),
                ("enable_octane_solo",            "Solos an Octane texture node for isolated preview"),
                ("enable_octane_texture_drop",    "Auto-converts dragged textures to the correct Octane image node type"),
                ("enable_octane_rename_node",     "Right-click any image node to rename it to its texture filename"),
                ("enable_octane_swap_image_node", "Right-click any image node to swap between RGB and Greyscale"),
                ("enable_octane_convert_nodes",   "Converts selected Cycles/EEVEE Image Texture nodes to Octane equivalents"),
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

        # ── Texture tag editor (Convert Nodes) ───────────────────────────────
        layout.label(text="Convert Nodes — Texture Detection Tags", icon='DOWNARROW_HLT')
        box = layout.box()
        col = box.column(align=True)
        col.prop(self, "show_octane_convert_tags",
                 text="Edit texture detection tags", toggle=True)
        if self.show_octane_convert_tags:
            tags = self.octane_convert_tags
            col.separator(factor=0.5)
            for attr, label in (
                ("albedo",         "Albedo / Base Color"),
                ("roughness",      "Roughness"),
                ("metallic",       "Metallic"),
                ("normal",         "Normal"),
                ("bump",           "Bump"),
                ("displacement",   "Displacement"),
                ("opacity",        "Opacity"),
                ("emission",       "Emission"),
                ("specular",       "Specular"),
                ("subsurface",     "Subsurface"),
                ("greyscale_only", "Greyscale (no socket)"),
            ):
                row = col.split(factor=0.25, align=True)
                row.label(text=label)
                row.prop(tags, attr, text="")
        layout.separator(factor=0.5)


def register():
    bpy.utils.register_class(OctaneConvertTagsPreferences)
    bpy.utils.register_class(OPSTYIXPreferences)
    prefs = bpy.context.preferences.addons[__name__].preferences
    if prefs.enable_beat_marker:
        beat_marker.register()
    if prefs.enable_pulse:
        pulse.register()
    if prefs.enable_lens_shift:
        lens_shift.register()
    if prefs.enable_object_utils:
        object_utils.register()

    bpy.app.handlers.load_post.append(_load_post_handler)
    _subscribe_engine()
    _on_engine_change()  # register octane modules if engine is already Octane
    # bpy.context.scene may be None during addon load; retry once context is ready
    bpy.app.timers.register(_on_engine_change, first_interval=0.1)


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
    bpy.utils.unregister_class(OctaneConvertTagsPreferences)


if __name__ == "__main__":
    register()

print("OPSTYIX Toolkit Loaded Successfully!")
