# OPSTYIX TOOLKIT
import bpy

from .operators.mat_nodeautoname import register_mat_nodeautoname, unregister_mat_nodeautoname
from .operators.original import register_original, unregister_original
from .operators.scatter import register_scatter, unregister_scatter
from .operators.kitbash3d import register_kitbash3d, unregister_kitbash3d
from .operators.vp_emissive import register_vp_emissive, unregister_vp_emissive

#TODO: Needs work
#//from .operators.overlay import register_overlay, unregister_overlay

bl_info = {
    "name": "OPSTYIX Toolkit",
    "description": "A batch of tools that help develop my workflow :)",
    "author": "OPSTYIX",
    "version": (1, 0),
    "blender": (3, 4, 0),
    "location": "View 3D",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "category": "Development"
}

def register():
    register_mat_nodeautoname()
    register_original()
    register_scatter()
    register_kitbash3d()
    register_vp_emissive()
    #//register_overlay()

def unregister():
    unregister_mat_nodeautoname()
    unregister_original()
    unregister_scatter()
    unregister_kitbash3d()
    unregister_vp_emissive()
    #//unregister_overlay()

if __name__ == "__main__":
    register()

print("OPSTYIX Toolkit Loaded Successfully!")