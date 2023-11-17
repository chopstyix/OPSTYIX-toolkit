# OPSTYIX TOOLKIT
import bpy

from bpy.types import AddonPreferences
from bpy.props import (
    FloatProperty,
    EnumProperty,
    BoolProperty,
    IntProperty,
    StringProperty,
    FloatVectorProperty,
    CollectionProperty,
)

from .operators import beat_marker, octane_node_organizer

bl_info = {
    "name": "OPSTYIX Toolkit",
    "description": "A collection of scripts that makes animating to music just a bit easier :)",
    "author": "OPSTYIX",
    "version": (1, 1),
    "blender": (4, 1, 0),
    "location": "View 3D",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "category": "Development"
}

def register():
    beat_marker.register()
    octane_node_organizer.register()

def unregister():      
    beat_marker.unregister()
    octane_node_organizer.unregister()

if __name__ == "__main__":
    register()

print("OPSTYIX Toolkit Loaded Successfully!")