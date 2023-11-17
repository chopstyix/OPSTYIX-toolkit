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

from .operators import scatter

from .operators.mat_nodeautoname import register_mat_nodeautoname, unregister_mat_nodeautoname
from .operators.original import register_original, unregister_original
# from .operators.scatter import register_scatter, unregister_scatter
from .operators.kitbash3d import register_kitbash3d, unregister_kitbash3d
from .operators.vp_emissive import register_vp_emissive, unregister_vp_emissive
from .operators.outliner import register_outliner, unregister_outliner

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

class OpstyixPrefs(AddonPreferences):
    bl_idname = __name__
    base_color: StringProperty (
        name = 'Base Color',
        default = 'albedo color colour diffuse basemap',
        description = 'Naming Components for Base Color maps')

def register():
    register_mat_nodeautoname()
    register_original()
    scatter.register()
    register_kitbash3d()
    register_vp_emissive()
    register_outliner()

    #//register_overlay()

def unregister():      
    unregister_mat_nodeautoname()
    unregister_original()
    # unregister_scatter()
    scatter.unregister()
    unregister_kitbash3d()
    unregister_vp_emissive()
    unregister_outliner()
    #//unregister_overlay()

if __name__ == "__main__":
    register()

print("OPSTYIX Toolkit Loaded Successfully!")