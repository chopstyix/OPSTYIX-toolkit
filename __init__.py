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

from .operators import beat_marker

bl_info = {
    "name": "OPSTYIX Toolkit",
    "description": "A batch of tools that help develop my workflow :)",
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

def unregister():      
    beat_marker.unregister()

if __name__ == "__main__":
    register()

print("OPSTYIX Toolkit Loaded Successfully!")