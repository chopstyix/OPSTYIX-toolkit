#* FILE IMPORT
import bpy
                       
from bpy.types import (Operator)

class OPSTYIX_OT_Node(Operator):
    bl_idname = "opstyix.kb3d_organize"
    bl_label  = "Organize Assets"
    def execute(self, context):
        scene = context.scene

        #Get selected objects
        selected = bpy.context.selected_objects

        #Loop over selected objects
        for obj in selected:

            #Check if object is an empty
            if obj.type == 'EMPTY':
                if len(obj.children) == 0: # TBD
                    bpy.data.collections[obj.name].objects.link(obj) # TBD
                    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True) # Applies transformation

                #Create a new collection variable with Empty's name
                new_collection = bpy.data.collections.new(obj.name.replace('_grp',''))

                # Remove object from collection
                #bpy.ops.object.collection_unlink()

                #Add the collection to the scene
                bpy.context.scene.collection.children.link(new_collection)

                #Move the object's children to the new collection
                new_collection.objects.link(obj)
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
                for child in obj.children:
                    new_collection.objects.link(child)
                    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)


                #Deselect objects
                bpy.ops.object.select_all(action='DESELECT')
                #old_select = selected
                bpy.data.objects[obj.name].select_set(True)
                # Set cursor position to empty
                bpy.ops.view3d.snap_cursor_to_selected()
                # Instance offset from cursor
                new_collection.instance_offset = scene.cursor.location

            #Loop over deleting old empty objects
        for obj in selected:
            if obj.type == 'EMPTY':
                bpy.data.objects.remove(obj)

        #Now we remove the default collection from the file to avoid some strange issues with linking/hierarchy
        name = "OBJECTS"
        remove_collection_objects = False

        coll = bpy.data.collections.get(name)

        if coll:
            if remove_collection_objects:
                obs = [o for o in coll.objects if o.users == 1]
                while obs:
                    bpy.data.objects.remove(obs.pop())

            bpy.data.collections.remove(coll)

        #Finally we loop over the Collections and mark them as assets.
        # for i, collection in enumerate(bpy.data.collections):
        #     collection.asset_mark()

        return {'FINISHED'}

def register_kitbash3d():
    # from bpy.utils import register_class
    # for cls in classes:
    #     register_class(cls)
    bpy.utils.register_class(OPSTYIX_OT_Node)

def unregister_kitbash3d():
    # from bpy.utils import unregister_class
    # for cls in classes:
    #     unregister_class(cls)
    bpy.utils.unregister_class(OPSTYIX_OT_Node)


#*  RUN ON LOAD
print("kitbash3d.py loaded")