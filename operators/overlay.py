# bl_info = {
#     "name": "Stats",
#     "description": "Show Stats in Viewport",
#     "author": "Alex,AFWS",
#     "version": (0, 0, 1),
#     "blender": (2, 80, 0),
#     "location": "View3D",
#     "category": "3D View"
# }

import bpy
import blf

font_info = {
    "font_id": 0,
    "handler": None,
}
ofsetX=0
ofsetY=0
font_id = font_info["font_id"]
dimentions=0

bpy.utils.unregister_class(bpy.types.VIEW3D_PT_overlay_guides)
print("Unregistered Overlay Class")
def register_overlay():
    # set the font drawing routine to run every frame
    font_info["handler"] = bpy.types.SpaceView3D.draw_handler_add(
        draw_callback_px, (None, None), 'WINDOW', 'POST_PIXEL')
    blf.size(font_id, getValue("textSize"), 32)

def draw_callback_px(self, context):
     if bpy.context.space_data.overlay.show_overlays:
        if bpy.data.window_managers["WinMan"].stats_toggle:

            level = 5
            r = 0.0
            g = 0.0
            b = 0.0
            a = 0.9
            
            blf.enable(font_id , blf.SHADOW )
            blf.shadow(font_id, level, r, g, b, a)
            blf.shadow_offset(font_id, 1, -1)
            dimentions=getValue("distanceBetweenInfo")
            information=getDataFromSelectedObjects()
            ofsetX=bpy.context.area.regions[2].width+getValue("LocX")-20
            ofsetY=bpy.context.area.regions[0].height+getValue("LocY")-20
            if(bpy.context.scene.render.engine=="CYCLES"):
                area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
                space = next(space for space in area.spaces if space.type == 'VIEW_3D')
                if space.shading.type == 'RENDERED': 
                    ofsetY=ofsetY+10
            blf.size(font_id, getValue("textSize"), 32)
            if bpy.context.mode != "EDIT_MESH":
                blf.color(font_id,getValue("sStatColor")[0],getValue("sStatColor")[1],getValue("sStatColor")[2],getValue("AlphaSlider"))
                dimentions2=(blf.dimensions(font_id,formatedStr(getDataFromSelectedObjects()[2]))[0])/2
                blf.position(font_id,ofsetX+20,bpy.context.area.height-(100+ofsetY), 1)     
                blf.draw(font_id,"Faces:")
                blf.position(font_id,ofsetX+20+dimentions-dimentions2+getValue("textSize"),bpy.context.area.height-(100+ofsetY), 1)   
                blf.draw(font_id,formatedStr(getDataFromSelectedObjects()[2]))
            
                dimentions1=(blf.dimensions(font_id,formatedStr(getDataFromSelectedObjects()[1]))[0])/2
                blf.position(font_id,ofsetX+20,bpy.context.area.height-(130+ofsetY), 1)
                blf.draw(font_id,"Edges:")
                blf.position(font_id,ofsetX+20+dimentions-dimentions1+getValue("textSize"),bpy.context.area.height-(130+ofsetY), 1)   
                blf.draw(font_id,formatedStr(getDataFromSelectedObjects()[1]))

                dimentions0=(blf.dimensions(font_id,formatedStr(getDataFromSelectedObjects()[0]))[0])/2
                blf.position(font_id,ofsetX+20,bpy.context.area.height-(160+ofsetY), 1)
                blf.draw(font_id,"Verts:")
                blf.position(font_id,ofsetX+20+dimentions-dimentions0+getValue("textSize"),bpy.context.area.height-(160+ofsetY), 1)   
                blf.draw(font_id,formatedStr(getDataFromSelectedObjects()[0]))

            if bpy.context.mode == "EDIT_MESH":
                facesCount=getEditDataFromSelectedObjects(3)
                edgesCount=getEditDataFromSelectedObjects(2)
                vertsCount=getEditDataFromSelectedObjects(1)

                facesCountLen=blf.dimensions(font_id,str(facesCount[0]))
                edgesCountLen=blf.dimensions(font_id,str(edgesCount[0]))
                vertsCountLen=blf.dimensions(font_id,str(vertsCount[0]))

                blf.color(font_id,getValue("sStatColor")[0],getValue("sStatColor")[1],getValue("sStatColor")[2],getValue("AlphaSlider"))
                blf.position(font_id,ofsetX+20,bpy.context.area.height-(100+ofsetY), 1)     
                blf.draw(font_id,"Faces:")
                if bpy.context.scene.tool_settings.mesh_select_mode[2]:
                    blf.color(font_id,getValue("HighlightColor")[0],getValue("HighlightColor")[1],getValue("HighlightColor")[2],getValue("selAlphaSlider"))
                else:
                    blf.color(font_id,getValue("sStatColor")[0],getValue("sStatColor")[1],getValue("sStatColor")[2],getValue("AlphaSlider"))  
                blf.position(font_id,ofsetX+20+dimentions-facesCountLen[0]+getValue("textSize"),bpy.context.area.height-(100+ofsetY), 1)   
                blf.draw(font_id,str(facesCount[0]))
                blf.color(font_id,getValue("sStatColor")[0],getValue("sStatColor")[1],getValue("sStatColor")[2],getValue("AlphaSlider"))
                blf.position(font_id,ofsetX+20+dimentions+getValue("textSize"),bpy.context.area.height-(100+ofsetY), 1) 
                blf.draw(font_id,"/"+str(facesCount[1]))

                
                blf.position(font_id,ofsetX+20,bpy.context.area.height-(130+ofsetY), 1)
                blf.draw(font_id,"Edges:")
                if bpy.context.scene.tool_settings.mesh_select_mode[1]:
                    blf.color(font_id,getValue("HighlightColor")[0],getValue("HighlightColor")[1],getValue("HighlightColor")[2],getValue("selAlphaSlider"))
                else:
                    blf.color(font_id,getValue("sStatColor")[0],getValue("sStatColor")[1],getValue("sStatColor")[2],getValue("AlphaSlider"))  
                blf.position(font_id,ofsetX+20+dimentions-edgesCountLen[0]+getValue("textSize"),bpy.context.area.height-(130+ofsetY), 1)   
                blf.draw(font_id,str(edgesCount[0]))
                blf.color(font_id,getValue("sStatColor")[0],getValue("sStatColor")[1],getValue("sStatColor")[2],getValue("AlphaSlider"))
                blf.position(font_id,ofsetX+20+dimentions+getValue("textSize"),bpy.context.area.height-(130+ofsetY), 1)
                blf.draw(font_id,"/"+str(edgesCount[1]))


                
                blf.position(font_id,ofsetX+20,bpy.context.area.height-(160+ofsetY), 1)
                blf.draw(font_id,"Verts:")
                if bpy.context.scene.tool_settings.mesh_select_mode[0]:
                    blf.color(font_id,getValue("HighlightColor")[0],getValue("HighlightColor")[1],getValue("HighlightColor")[2],getValue("selAlphaSlider"))
                else:
                    blf.color(font_id,getValue("sStatColor")[0],getValue("sStatColor")[1],getValue("sStatColor")[2],getValue("AlphaSlider"))   
                blf.position(font_id,ofsetX+20+dimentions-vertsCountLen[0]+getValue("textSize"),bpy.context.area.height-(160+ofsetY), 1)   
                blf.draw(font_id,str(vertsCount[0]))
                blf.color(font_id,getValue("sStatColor")[0],getValue("sStatColor")[1],getValue("sStatColor")[2],getValue("AlphaSlider"))
                blf.position(font_id,ofsetX+20+dimentions+getValue("textSize"),bpy.context.area.height-(160+ofsetY), 1) 
                blf.draw(font_id,"/"+str(vertsCount[1]))


                #statistic
            length=len(bpy.context.scene.statistics(bpy.context.view_layer).split("|"))
            memInfo=bpy.context.scene.statistics(bpy.context.view_layer).split("|")[length-2]
            blf.color(font_id,getValue("sStatColor")[0],getValue("sStatColor")[1],getValue("sStatColor")[2],getValue("AlphaSlider"))    
            blf.position(font_id,ofsetX+15,bpy.context.area.height-(190+ofsetY), 1) 
            blf.draw(font_id,str(memInfo))

def getValue(name):
    return getattr(bpy.context.preferences.addons[__name__].preferences,name)

def formatedStr(intputInt):
    return str(format(intputInt,',d'))

def getEditDataFromSelectedObjects(mode):
    # mode 3-faces 2-edges 1-vertices
    return bpy.context.scene.statistics(bpy.context.view_layer).split("|")[mode].split(":")[1].split("/")

def getDataFromSelectedObjects():
    sum = [0,0,0]
    for object in bpy.context.selected_objects:
        if object.type == "MESH":
            depsgraph=bpy.context.evaluated_depsgraph_get()
            object_eval=object.evaluated_get(depsgraph)
            mesh_eval=object_eval.data
            sum[2]+=len(mesh_eval.polygons)
            sum[1]+=len(mesh_eval.edges)
            sum[0]+=len(mesh_eval.vertices)
    return sum

def guides_with_new_settings(self, context):
    layout = self.layout

    view = context.space_data
    scene = context.scene

    overlay = view.overlay
    shading = view.shading
    display_all = overlay.show_overlays

    col = layout.column()
    col.label(text="Guides")

    col = layout.column()
    col.active = display_all

    split = col.split()
    sub = split.column()

    row = sub.row()
    row_el = row.column()
    row_el.prop(overlay, "show_ortho_grid", text="Grid")
    grid_active = (
        view.region_quadviews or
        (view.region_3d.is_orthographic_side_view and not view.region_3d.is_perspective)
    )
    row_el.active = grid_active
    row.prop(overlay, "show_floor", text="Floor")

    if overlay.show_floor or overlay.show_ortho_grid:
        sub = col.row(align=True)
        sub.active = (
            (overlay.show_floor and not view.region_3d.is_orthographic_side_view) or
            (overlay.show_ortho_grid and grid_active)
        )
        sub.prop(overlay, "grid_scale", text="Scale")
        sub = sub.row(align=True)
        sub.active = scene.unit_settings.system == 'NONE'
        sub.prop(overlay, "grid_subdivisions", text="Subdivisions")

    sub = split.column()
    row = sub.row()
    row.label(text="Axes")

    subrow = row.row(align=True)
    subrow.prop(overlay, "show_axis_x", text="X", toggle=True)
    subrow.prop(overlay, "show_axis_y", text="Y", toggle=True)
    subrow.prop(overlay, "show_axis_z", text="Z", toggle=True)

    split = col.split()
    sub = split.column()
    sub.prop(overlay, "show_text", text="Text Info")
    sub = split.column()
    sub.prop(overlay, "show_cursor", text="3D Cursor")

    if shading.type == 'MATERIAL':
        col.prop(overlay, "show_look_dev")

    split = col.split()
    sub = split.column()
    sub.prop(overlay, "show_annotation", text="Annotations")

    #Add my new setting here
    sub = split.column()        
    sub.prop(context.window_manager, "stats_toggle", text="Statistics")
 
class sampleTextPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    textSize:bpy.props.IntProperty(name="Size",description="Size of the text of statistics",default=28,min=1,max=66)
    LocX:bpy.props.IntProperty(name="X position",description="x position",default=18,min=1,max=2000)
    LocY:bpy.props.IntProperty(name="Y position",description="y position",default=20,min=1,max=2000)
    distanceBetweenInfo:bpy.props.IntProperty(name="Indent",description="Indent between info and digits",default=66,min=10,max=1000)

    sStatColor:bpy.props.FloatVectorProperty(name="StatColor",description="Color", default=(1,1,1),subtype='COLOR',min=0,max=1)
    HighlightColor:bpy.props.FloatVectorProperty(name="HighlightColor",description="Color", default=(0,1,0),subtype='COLOR',min=0,max=1)
    AlphaSlider:bpy.props.FloatProperty(name="Alpha",description="Transparent of the text",default=0.82,min=0.1,max=1)
    selAlphaSlider:bpy.props.FloatProperty(name="selAlpha",description="Transparent of the selected text",default=1,min=0.1,max=1)
    # pin:bpy.props.EnumProperty(
    # items=[
    #     ('left', 'To left side', 'Pin to left side', '', 0),
    #     ('right', 'To right side', 'Pin to right side', '', 1),
    # ],
    # default='left'
    # )
 
    def draw(self, context):
        layout = self.layout
        globalStatBox = layout.box()
        globalStatBox.label(text="Main Options")
        # row = globalStatBox.row(align=False)
        # row.prop(self,"pin",text="Pin")
        row = globalStatBox.row(align=True)
        row.prop(self, 'textSize')
        row.prop(self, 'LocX')
        row.prop(self, 'LocY')
        row.prop(self, 'distanceBetweenInfo')

        colorStatBox = layout.box()
        colorStatBox.label(text="View settings")
        rowColors = colorStatBox.row(align=True)
        rowColors.prop(self, 'sStatColor',text="Color")
        rowColors.prop(self, 'AlphaSlider',text="Alpha")
        rowColors = colorStatBox.row(align=True)
        rowColors.prop(self, 'HighlightColor',text="Highlight")
        rowColors.prop(self, 'selAlphaSlider',text="Alpha")



def register_overlay():
    font_info["handler"] = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, (None, None), 'WINDOW', 'POST_PIXEL')
    bpy.utils.register_class(sampleTextPreferences)
    bpy.types.VIEW3D_PT_overlay.append(guides_with_new_settings)

    bpy.types.WindowManager.stats_toggle = bpy.props.BoolProperty(
        name = "Toggle Stats",
        default = True
      )
    
def unregister_overlay(): 
    bpy.types.SpaceView3D.draw_handler_remove(font_info["handler"],'WINDOW')   
    bpy.utils.unregister_class(sampleTextPreferences)

    bpy.types.VIEW3D_PT_overlay.remove(guides_with_new_settings)
    del bpy.types.WindowManager.stats_toggle


