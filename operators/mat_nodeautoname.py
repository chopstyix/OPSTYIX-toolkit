import bpy

from bpy.types import (Panel,
                       Menu,
                       Operator,
                       AddonPreferences,
                       PropertyGroup,
                       )

def node_switch(type: str, list: list, index: int) -> list:
  bpy.ops.node.select_all(action='DESELECT')
  list[index].select = True
  # Switch node type to Universal Material
  if type == "RGB":
    bpy.ops.node.nw_swtch_node_type(to_type='OctaneRGBImage')
  elif type == "Greyscale":
    bpy.ops.node.nw_swtch_node_type(to_type='OctaneGreyscaleImage')  
  elif type == "Universal":
    bpy.ops.node.nw_swtch_node_type(to_type='OctaneUniversalMaterial')
  # Update list 'n'
  del list[index]
  list.insert(index,bpy.context.selected_nodes[0])
  return list

#TODO: Determine a better class name
class OPSTYIX_OT_MAT_NodeAutoname(Operator):
    bl_idname = "opstyix.material_nodeautoname"
    bl_label  = "Auto-Name Nodes"

    def execute(self, context):
      #* Run when used
      print("Running Operator...")

      #* Dictionary
      albedo_list = ['albedo','color','colour','diffuse','basemap']
      ambientocclusion_list = ['ao']
      transmission_list = ['transmission','translucency']
      metallic_list = ['metallic','metalness'] # Refrain from using 'metal', it causes some funkiness
      glossy_list = ['glossy','glossiness']
      specular_list = ['specular']
      roughness_list = ['roughness']
      opacity_list = ['opacity','alpha']
      bump_list = ['bump']
      normal_list = ['normal','nmap']
      displacement_list = ['height','displacement']
      emission_list = ['emission','emissive']
      refraction_list = ['refraction']

      #sss_list = ['sss']
      
      #* Setup
      active_material = bpy.context.active_object.active_material 
      node_tree = active_material.node_tree

      #TODO: Optimize Code Support Node Switching; Too many if statements lol
      #* OCTANE RENDER
      if bpy.context.scene.render.engine == 'octane':
        n = context.selected_nodes

        #* CONVERSION AND MATERIALS
        transformation_node = node_tree.nodes.new('Octane2DTransformation')        
        #TODO: Support other material nodes such as Diffuse, Metallic, Standard Materials along with Layers
        # Search for Principled BSDF and convert to Universal Material, Node Wrangler Required
        for idx,x in enumerate(n):
          print(f"Detected {n[idx].bl_label}.")
          if n[idx].bl_label == 'Universal material':
            print("Detected Universal Material")
            universal_mat = n[idx]            
          elif n[idx].bl_label == 'Principled BSDF':
            n = node_switch("Universal",n,idx)
            universal_mat = n[idx]               
          elif n[idx].bl_label == 'Image Texture' or n[idx].bl_label == 'Image Tex' or n[idx].bl_label == 'Float Image Tex':
            print(f"Detected {n[idx].bl_label}, converting node.")
            n[idx].hide = False
            n = node_switch("RGB",n,idx)
            try:
              node_tree.links.remove(n[idx].outputs[0].links[0])
            except:
              print("Node has no connections!")
          elif n[idx].bl_label == 'RGB image' or n[idx].bl_label == 'Grayscale image':
            print(f"Detected {n[idx].bl_label}.")
          else:              
            print("Deleting unused nodes")
            #node_tree.nodes.remove(n[idx])
            del n[idx]

        if 'universal_mat' in locals():
            universal_mat.inputs['Specular'].default_value = 0.5
            universal_mat.inputs['Roughness'].default_value = 0.5  

        # Detect the type of texture map and update the label
        for idx,x in enumerate(n):
          if n[idx].bl_label == 'RGB image' or n[idx].bl_label == 'Grayscale image':
            file_name_old = n[idx].image.name
            file_name = n[idx].image.name.lower() 

            # Albedo and Viewport Texture
            if any(word in file_name for word in albedo_list):
              albedo_tex = n[idx]
              bpy.ops.node.select_all(action='DESELECT')
              albedo_tex.select = True
              # Duplicate image texture and switch type to Blender's native image texture node
              try:
                if node_tree.nodes["Viewport Texture"].label == "Viewport Texture":
                  print("Viewport Texture is present")
              except:
                viewport_texture = node_tree.nodes.new('ShaderNodeTexImage')
                viewport_texture.name = "Viewport Texture"
                viewport_texture.label = "Viewport Texture"
                viewport_texture.image = bpy.data.images[file_name_old]
              albedo_tex.label = "Albedo"  
              albedo_tex.width = 140.0

            # Ambient Occlusion
            elif any(word in file_name for word in ambientocclusion_list):
              ao_tex = n[idx]       
              ao_tex.label = "Ambient Occlusion"
              ao_tex.width = 140.0              
              mult_node = node_tree.nodes.new('OctaneMultiplyTexture')
              mult_node.label = "Mult."
              mult_node.hide = True
              mult_node.width = 100.0

            # Transmission
            elif any(word in file_name for word in transmission_list):
              transmission_tex = n[idx]       
              transmission_tex.label = "Transmission"
              transmission_tex.width = 140.0

            # Metallic 
            elif any(word in file_name for word in metallic_list):           
              n = node_switch("Greyscale",n,idx)              
              metallic_tex = n[idx]              
              metallic_tex.label = "Metallic"
              metallic_tex.inputs[2].default_value = 1.0 
              metallic_tex.width = 140.0

            # Specular            
            elif any(word in file_name for word in specular_list):      
              n = node_switch("Greyscale",n,idx)              
              specular_tex = n[idx]        
              specular_tex.label = "Specular"  
              specular_tex.inputs[2].default_value = 1.0
              specular_tex.width = 140.0                            

            # Roughness         
            elif any(word in file_name for word in roughness_list): 
              n = node_switch("Greyscale",n,idx)              
              roughness_tex = n[idx]             
              roughness_tex.label = "Roughness"
              roughness_tex.inputs[2].default_value = 1.0
              roughness_tex.width = 140.0                            

            # Glossy
            elif any(word in file_name for word in glossy_list):              
              n = node_switch("Greyscale",n,idx)              
              roughness_tex = n[idx]
              roughness_tex.label = "Glossy"
              roughness_tex.inputs[2].default_value = 1.0
              roughness_tex.inputs[3].default_value = True
              roughness_tex.width = 140.0                            

            # Opacity  
            elif any(word in file_name for word in opacity_list):   
              n = node_switch("Greyscale",n,idx)                         
              opacity_tex = n[idx]
              opacity_tex.label = "Opacity"
              opacity_tex.inputs[2].default_value = 1.0
              opacity_tex.width = 140.0                            
            
            # Bump
            elif any(word in file_name for word in bump_list):              
              n = node_switch("Greyscale",n,idx)              
              bump_tex = n[idx]
              bump_tex.label = "Bump"
              bump_tex.inputs[0].default_Value = 0.5
              bump_tex.inputs[2].default_value = 1.0
              bump_tex.width = 140.0                            

            # Normal  
            elif any(word in file_name for word in normal_list):              
              normal_tex = n[idx]
              normal_tex.label = "Normal" 
              normal_tex.inputs[2].default_value = 1.0
              normal_tex.width = 140.0                               

            # Displacement  
            elif any(word in file_name for word in displacement_list):              
              n = node_switch("Greyscale",n,idx)              
              displacement_tex = n[idx]
              displacement_tex.label = "Displacement"   
              displacement_tex.inputs[2].default_value = 1.0
              displacement_tex.width = 140.0                            
              tex_displace_node = node_tree.nodes.new('OctaneTextureDisplacement')
              tex_displace_node.inputs[1].default_value = 0.5
              tex_displace_node.inputs[2].default_value = '2048x2048'
              tex_displace_node.inputs[3].default_value = 1.0
              tex_displace_node.width = 140.0                               

            # Emission
            elif any(word in file_name for word in emission_list):              
              emission_tex = n[idx]
              emission_tex.label = "Emission"   
              emission_tex.width = 140.0                 
              if 'universal_mat' in locals(): 
                tex_emission_node = node_tree.nodes.new('OctaneTextureEmission')
                tex_emission_node.inputs['Power'].default_value = 1.0
            
            # Refraction Texture
            elif any(word in file_name for word in refraction_list):
              n = node_switch("Greyscale",n,idx)              
              refraction_tex = n[idx]
              refraction_tex.label = "Refraction"
              refraction_tex.inputs[2].default_value = 1.0
              refraction_tex.width = 140.0                               

        #* NODE ORGANIZATION
        bpy.ops.node.select_all(action='DESELECT')
        for idx,x in enumerate(n):
          if n[idx].bl_label == 'RGB image' or n[idx].bl_label == 'Grayscale image' or n[idx].bl_label == 'Image Texture':
            n[idx].select = True
        node_tree.nodes.active = n[0]

        if n[0].hide == False:
          bpy.ops.node.hide_toggle()
          bpy.ops.node.hide_socket_toggle()

        # Organization Settings
        padding_y = 38
        padding_x = 350
        curr_pos = n[0].location
        universal_flag = False
        transmission_flag = False


        if 'transmission_tex' in locals():
          if 'universal_mat' in locals():
            universal_flag = True
            transmission_tex.location = [(universal_mat.location.x - padding_x), universal_mat.location.y]
            node_tree.links.new(transmission_tex.outputs[0], universal_mat.inputs['Transmission'])                
          curr_pos = [transmission_tex.location.x, (transmission_tex.location.y - padding_y)]
          node_tree.links.new(transformation_node.outputs[0], transmission_tex.inputs['UV transform'])
          transmission_flag = True

        if 'albedo_tex' in locals():
          if 'universal_mat' in locals():
            node_tree.links.new(albedo_tex.outputs[0], universal_mat.inputs['Albedo'])              
            if universal_flag == False:
              albedo_tex.location = [(universal_mat.location.x - padding_x), universal_mat.location.y]
            else:
              albedo_tex.location = curr_pos
          if transmission_flag == True:
            albedo_tex.location = curr_pos
          curr_pos = [albedo_tex.location.x, (albedo_tex.location.y - padding_y)]
          node_tree.links.new(transformation_node.outputs[0], albedo_tex.inputs['UV transform'])

        if 'ao_tex' in locals():
          ao_tex.location = curr_pos
          mult_node.location = [ao_tex.location.x + 220, (ao_tex.location.y + (padding_y/2))]
          curr_pos = [ao_tex.location.x, (ao_tex.location.y - padding_y)]
          # if 'albedo_mat' in locals():
          #   node_tree.links.remove(albedo_tex.outputs[0].links[0])
          node_tree.links.new(albedo_tex.outputs[0], mult_node.inputs['Texture 1'])
          node_tree.links.new(ao_tex.outputs[0], mult_node.inputs['Texture 2']) 
          node_tree.links.new(transformation_node.outputs[0], ao_tex.inputs['UV transform'])                   
          if 'universal_mat' in locals():
            node_tree.links.new(mult_node.outputs[0], universal_mat.inputs['Albedo'])              


        if 'metallic_tex' in locals():         
          if 'albedo_tex' in locals():
            metallic_tex.location = curr_pos
          elif 'universal_mat' in locals():
            metallic_tex.location = [(universal_mat.location.x - padding_x), universal_mat.location.y]
          else:
            print("'albedo_tex' or 'universal_mat' not found")
          metallic_tex.location = curr_pos
          curr_pos = [metallic_tex.location.x, (metallic_tex.location.y - padding_y)] 
          node_tree.links.new(transformation_node.outputs[0], metallic_tex.inputs['UV transform'])
          if 'universal_mat' in locals():
            node_tree.links.new(metallic_tex.outputs[0], universal_mat.inputs['Metallic'])            

        if 'specular_tex' in locals():
          specular_tex.location = curr_pos
          curr_pos = [specular_tex.location.x, (specular_tex.location.y - padding_y)]
          node_tree.links.new(transformation_node.outputs[0], specular_tex.inputs['UV transform'])          
          if 'universal_mat' in locals():
            node_tree.links.new(specular_tex.outputs[0], universal_mat.inputs['Specular'])     

        if 'roughness_tex' in locals():
          roughness_tex.location = curr_pos
          curr_pos = [roughness_tex.location.x, (roughness_tex.location.y - padding_y)]
          node_tree.links.new(transformation_node.outputs[0], roughness_tex.inputs['UV transform'])          
          if 'universal_mat' in locals():
            node_tree.links.new(roughness_tex.outputs[0], universal_mat.inputs['Roughness'])     

        if 'opacity_tex' in locals():
          opacity_tex.location = curr_pos
          curr_pos = [opacity_tex.location.x, (opacity_tex.location.y - padding_y)]
          node_tree.links.new(transformation_node.outputs[0], opacity_tex.inputs['UV transform'])          
          if 'universal_mat' in locals():
            node_tree.links.new(opacity_tex.outputs[0], universal_mat.inputs['Opacity'])     

        if 'bump_tex' in locals():
          bump_tex.location = curr_pos
          curr_pos = [bump_tex.location.x, (bump_tex.location.y - padding_y)]
          node_tree.links.new(transformation_node.outputs[0], bump_tex.inputs['UV transform'])          
          if 'universal_mat' in locals():
            node_tree.links.new(bump_tex.outputs[0], universal_mat.inputs['Bump'])     

        if 'normal_tex' in locals():
          normal_tex.location = curr_pos
          curr_pos = [normal_tex.location.x, (normal_tex.location.y - padding_y)]
          node_tree.links.new(transformation_node.outputs[0], normal_tex.inputs['UV transform'])          
          if 'universal_mat' in locals():
            node_tree.links.new(normal_tex.outputs[0], universal_mat.inputs['Normal'])     

        if 'displacement_tex' in locals():
          displacement_tex.location = curr_pos
          curr_pos = [displacement_tex.location.x, (displacement_tex.location.y - padding_y)]
          node_tree.links.new(transformation_node.outputs[0], displacement_tex.inputs['UV transform'])
          node_tree.links.new(displacement_tex.outputs[0], tex_displace_node.inputs['Texture'])                            

        if 'emission_tex' in locals():
          emission_tex.location = curr_pos
          curr_pos = [emission_tex.location.x, (emission_tex.location.y - padding_y)]          
          node_tree.links.new(transformation_node.outputs[0], emission_tex.inputs['UV transform'])
          node_tree.links.new(emission_tex.outputs[0], tex_emission_node.inputs['Texture'])                   
          if 'universal_mat' in locals():
            node_tree.links.new(tex_emission_node.outputs[0], universal_mat.inputs['Emission'])   

        # Texture Transformation
        if 'albedo_tex' in locals():
          transformation_node.location = [(albedo_tex.location.x - 250), albedo_tex.location.y]
        else:
          transformation_node.location = [n[0].location.x - 150, n[0].location.y]

        # Texture Displacement
        if 'displacement_tex' in locals() and 'emission_tex' in locals():
          tex_displace_node.location = [emission_tex.location.x, (emission_tex.location.y - padding_y - 20)]        
          tex_emission_node.location = [transformation_node.location.x, tex_displace_node.location.y]                  
        elif 'displacement_tex' in locals():
          tex_displace_node.location = [displacement_tex.location.x, (displacement_tex.location.y - padding_y - 20)]
        elif 'emission_tex' in locals():
          tex_emission_node.location = [emission_tex.location.x, emission_tex.location.y - padding_y - 20]           

        #* Select 'Viewport Texture' node so it appears in texture view
        if 'viewport_texture' in locals():
          node_tree.nodes.active = viewport_texture
          viewport_texture.location = [albedo_tex.location.x, albedo_tex.location.y + (padding_y*2)]
          viewport_texture.hide = True

        #* Deselect all items
        bpy.ops.node.select_all(action='DESELECT')

        #* Create Material Output Node
        if 'universal_mat' in locals():
          if (node_tree.nodes['Material Output'].target == 'ALL'):
            node_tree.nodes.remove(node_tree.nodes['Material Output'])
          output_octane = node_tree.nodes.new('ShaderNodeOutputMaterial')
          output_octane.target = 'octane'
          output_octane.is_active_output = True
          output_octane.location = [(universal_mat.location.x + 250), universal_mat.location.y]
          node_tree.links.new(universal_mat.outputs[0],output_octane.inputs['Surface'])          

      #* CYCLES/EEVEE RENDER
      else:
        n = context.selected_nodes
        
        for idx,x in enumerate(n):
          print(n[idx].type)
          if n[idx].type == 'BSDF_PRINCIPLED':
            print("Assigned Principled BDSF")
            principled_node = n[idx]

        #* Create Mapping Nodes
        texture_coord_node = node_tree.nodes.new('ShaderNodeTexCoord')            
        mapping_node = node_tree.nodes.new('ShaderNodeMapping')
        node_tree.links.new(texture_coord_node.outputs['UV'], mapping_node.inputs['Vector'])

        for idx,x in enumerate(n):
          if n[idx].type == 'TEX_IMAGE':
            file_name = n[idx].image.name.lower()

            # Albedo            
            if any(word in file_name for word in albedo_list):
              n[idx].label = "Albedo"
              albedo_tex = n[idx]            
              # node_tree.links.new(mapping_node.outputs[0], albedo_tex.inputs['Vector'])           
              # if 'principled_node' in locals():              
              #   node_tree.links.new(albedo_tex.outputs[0], principled_node.inputs['Base Color'])
              
            # Ambient Occlusion
            elif any(word in file_name for word in ambientocclusion_list):
              n[idx].label = "Ambient Occlusion"
              bpy.data.images[n[idx].image.name].colorspace_settings.name = 'Non-Color'                 
              ao_tex = n[idx]
              mixcolor_node = node_tree.nodes.new('ShaderNodeMix')
              mixcolor_node.data_type = 'RGBA'
              mixcolor_node.blend_type = 'MULTIPLY'
              mixcolor_node.inputs[0].default_value = 1.0
              mixcolor_node.hide = True

              #node_tree.links.new(mapping_node.outputs[0], ao_tex.inputs['Vector'])

              # if 'albedo_tex' in locals():
              #   try:
              #     node_tree.links.remove(albedo_tex.outputs[0].links[0])
              #   except:
              #     print('albedo_tex: No existing links')
              #   node_tree.links.new(albedo_tex.outputs[0], mixcolor_node.inputs[4])                
              # node_tree.links.new(ao_tex.outputs[0], mixcolor_node.inputs[3])
              # if 'principled_node' in locals():              
              #   node_tree.links.new(mixcolor_node.outputs[0], principled_node.inputs['Base Color'])

            # Transmission
            elif any(word in file_name for word in transmission_list):
              n[idx].label = "Transmission"
              transmission_tex = n[idx]
              # node_tree.links.new(mapping_node.outputs[0], transmission_tex.inputs['Vector'])                  
              # if 'principled_node' in locals():              
              #   node_tree.links.new(transmission_tex.outputs[0], principled_node.inputs['Transmission'])

            # Metallic
            elif any(word in file_name for word in metallic_list):
              n[idx].label = "Metallic"
              bpy.data.images[n[idx].image.name].colorspace_settings.name = 'Non-Color'
              metallic_tex = n[idx]
              # node_tree.links.new(mapping_node.outputs[0], metallic_tex.inputs['Vector'])    
              # if 'principled_node' in locals():
              #   node_tree.links.new(metallic_tex.outputs[0], principled_node.inputs['Metallic'])
            
            # Specular
            elif any(word in file_name for word in specular_list):
              n[idx].label = "Specular"
              specular_tex = n[idx]
              bpy.data.images[n[idx].image.name].colorspace_settings.name = 'Non-Color'   
              # node_tree.links.new(mapping_node.outputs[0], specular_tex.inputs['Vector'])       
              # if 'principled_node' in locals(): 
              #   node_tree.links.new(specular_tex.outputs[0], principled_node.inputs['Specular']) 

            # Roughness                               
            elif any(word in file_name for word in roughness_list):
              n[idx].label = "Roughness"
              roughness_tex = n[idx]
              bpy.data.images[n[idx].image.name].colorspace_settings.name = 'Non-Color'
              # node_tree.links.new(mapping_node.outputs[0], roughness_tex.inputs['Vector'])    
              # if 'principled_node' in locals():              
              #   node_tree.links.new(roughness_tex.outputs[0], principled_node.inputs['Roughness']) 

            # Glossy      
            elif any(word in file_name for word in glossy_list):
              n[idx].label = "Glossiness"
              roughness_tex = n[idx]
              bpy.data.images[n[idx].image.name].colorspace_settings.name = 'Non-Color'   
              # node_tree.links.new(mapping_node.outputs[0], roughness_tex.inputs['Vector'])    
              # if 'principled_node' in locals():                     
              #   node_tree.links.new(roughness_tex.outputs[0], principled_node.inputs['Roughness']) #TODO: Include code to invert color                  
            
            # Refraction
            elif any(word in file_name for word in refraction_list):
              n[idx].label = "Refraction"
              refraction_tex = n[idx]
              refraction_node = node_tree.nodes.new('ShaderNodeBsdfRefraction')
              bpy.data.images[n[idx].image.name].colorspace_settings.name = 'Non-Color'
              # node_tree.links.new(mapping_node.outputs[0], refraction_tex.inputs['Vector'])    
              # node_tree.links.new(refraction_tex.outputs[0], refraction_node.inputs['Color'])

              if 'principled_node' in locals():
                mix_node = node_tree.nodes.new('ShaderNodeMixShader')
                fresnel_node = node_tree.nodes.new('ShaderNodeFresnel')              
                # node_tree.links.new(fresnel_node.outputs[0], mix_node.inputs[0])
                # node_tree.links.new(refraction_node.outputs[0], mix_node.inputs[1])
                # node_tree.links.new(principled_node.outputs[0], mix_node.inputs[2])                

            # Opacity
            elif any(word in file_name for word in opacity_list):
              n[idx].label = "Opacity"
              opacity_tex = n[idx]
              bpy.data.images[n[idx].image.name].colorspace_settings.name = 'Non-Color'
              # node_tree.links.new(mapping_node.outputs[0], opacity_tex.inputs['Vector'])
              active_material.blend_method = 'CLIP'

              # if 'principled_node' in locals():                       
              #   node_tree.links.new(opacity_tex.outputs[0], principled_node.inputs['Alpha']) 

            # Emission
            elif any(word in file_name for word in emission_list):
              n[idx].label = "Emission"
              emission_tex = n[idx]
              # node_tree.links.new(mapping_node.outputs[0], emission_tex.inputs['Vector'])    
              # if 'principled_node' in locals():                       
                # node_tree.links.new(emission_tex.outputs[0], principled_node.inputs['Emission']) 
        
            # Normal
            elif any(word in file_name for word in normal_list):
              n[idx].label = "Normal"
              normal_tex = n[idx]
              bpy.data.images[n[idx].image.name].colorspace_settings.name = 'Non-Color'
              # node_tree.links.new(mapping_node.outputs[0], normal_tex.inputs['Vector'])
              normal_node = node_tree.nodes.new('ShaderNodeNormalMap')
              normal_node.hide = True                         
              # node_tree.links.new(normal_tex.outputs[0], normal_node.inputs['Color'])
              # if 'principled_node' in locals():
              #   node_tree.links.new(normal_node.outputs[0], principled_node.inputs['Normal'])

            # Bump  
            elif any(word in file_name for word in bump_list):
              n[idx].label = "Bump"
              bump_tex = n[idx]
              bpy.data.images[n[idx].image.name].colorspace_settings.name = 'Non-Color'
              # node_tree.links.new(mapping_node.outputs[0], bump_tex.inputs['Vector'])    
              # if 'principled_node' in locals():                
              #   bump_node = node_tree.nodes.new('ShaderNodeNormalBump')                           
              #   node_tree.links.new(opacity_tex.outputs[0], principled_node.inputs['Normal'])               
              #node_tree.links.new(bump_tex.outputs[0], node_2.inputs['Normal'])   #TODO: Connect to Bump/Normal Nodes            

            # Displacment
            elif any(word in file_name for word in displacement_list):
              n[idx].label = "Displacement"
              displacement_tex = n[idx]
              bpy.data.images[n[idx].image.name].colorspace_settings.name = 'Non-Color'
              active_material.cycles.displacement_method = 'BOTH'                    
              # node_tree.links.new(mapping_node.outputs[0], displacement_tex.inputs['Vector'])    
              displacement_node = node_tree.nodes.new('ShaderNodeDisplacement')
              displacement_node.hide = True
              # node_tree.links.new(displacement_tex.outputs[0], displacement_node.inputs['Height'])

        #* Deselect all
        bpy.ops.node.select_all(action='DESELECT')

        #* Select all Image Nodes
        for idx,x in enumerate(n):
          if n[idx].bl_label == 'RGB image' or n[idx].bl_label == 'Grayscale image' or n[idx].bl_label == 'Image Texture':
            n[idx].select = True
            n[idx].hide = True

        #* Select one of the nodes as active
        node_tree.nodes.active = n[0]

        #* Organize texture nodes by stacking and aligning
        padding_y = 38
        padding_x = 450
        curr_x = 0
        curr_y = 0

        #* Organize Nodes and create links
        if 'refraction_tex' in locals():
          if 'principled_node' in locals():
            refraction_node.location = [principled_node.location.x,(principled_node.location.y + 200)]            
            refraction_tex.location = [(refraction_node.location.x - padding_x), refraction_node.location.y]
            fresnel_node.location = [refraction_node.location.x, (refraction_node.location.y + 125)]
            mix_node.location = [(refraction_node.location.x + 300), refraction_node.location.y]        
            node_tree.links.new(mapping_node.outputs[0], refraction_tex.inputs['Vector'])    
            node_tree.links.new(refraction_tex.outputs[0], refraction_node.inputs['Color'])
            node_tree.links.new(fresnel_node.outputs[0], mix_node.inputs[0])
            node_tree.links.new(refraction_node.outputs[0], mix_node.inputs[1])
            node_tree.links.new(principled_node.outputs[0], mix_node.inputs[2])    


        if 'albedo_tex' in locals():
          if 'principled_node' in locals():
            albedo_tex.location = [(principled_node.location.x - padding_x), (principled_node.location.y)]
            if 'mixcolor_node' in locals():
              node_tree.links.new(albedo_tex.outputs[0], mixcolor_node.inputs[6])
              node_tree.links.new(mixcolor_node.outputs[2], principled_node.inputs['Base Color'])
            else:
              node_tree.links.new(albedo_tex.outputs[0], principled_node.inputs['Base Color'])      
          curr_pos = [albedo_tex.location.x, (albedo_tex.location.y - padding_y)]
          node_tree.links.new(mapping_node.outputs[0], albedo_tex.inputs['Vector'])    
        
        if 'ao_tex' in locals():
          ao_tex.location = curr_pos
          mixcolor_node.location = [(ao_tex.location.x + 260), (ao_tex.location.y + (padding_y/2))]
          curr_pos = [ao_tex.location.x, (ao_tex.location.y - padding_y)]
          node_tree.links.new(ao_tex.outputs[0], mixcolor_node.inputs[7])
          node_tree.links.new(mapping_node.outputs[0], ao_tex.inputs['Vector'])    

        if 'metallic_tex' in locals():
          metallic_tex.location = curr_pos
          curr_pos = [metallic_tex.location.x, (metallic_tex.location.y - padding_y)]
          if 'principled_node' in locals():
            node_tree.links.new(metallic_tex.outputs[0], principled_node.inputs['Metallic'])
          node_tree.links.new(mapping_node.outputs[0], metallic_tex.inputs['Vector'])            

        if 'roughness_tex' in locals():
          roughness_tex.location = curr_pos
          curr_pos = [roughness_tex.location.x, (roughness_tex.location.y - padding_y)]
          if 'principled_node' in locals():          
            node_tree.links.new(roughness_tex.outputs[0], principled_node.inputs['Roughness'])
          node_tree.links.new(mapping_node.outputs[0], roughness_tex.inputs['Vector'])            

        if 'opacity_tex' in locals():
          opacity_tex.location = curr_pos
          curr_pos = [opacity_tex.location.x, (opacity_tex.location.y - padding_y)]
          if 'principled_node' in locals():          
            node_tree.links.new(opacity_tex.outputs[0], principled_node.inputs['Alpha'])
          node_tree.links.new(mapping_node.outputs[0], opacity_tex.inputs['Vector'])            

        if 'bump_tex' in locals():
          bump_tex.location = curr_pos
          curr_pos = [bump_tex.location.x, (bump_tex.location.y - padding_y)]
          #node_tree.links.new(bump_tex.outputs[0], principled_node.inputs['Metallic']) #TODO: Support Bump Tex

        if 'emission_tex' in locals():
          emission_tex.location = curr_pos
          curr_pos = [emission_tex.location.x, (emission_tex.location.y - padding_y)]
          if 'principled_node' in locals():          
            node_tree.links.new(emission_tex.outputs[0], principled_node.inputs['Emission'])
            principled_node.inputs['Emission Strength'].default_value = 10.0
          node_tree.links.new(mapping_node.outputs[0], emission_tex.inputs['Vector'])            

        if 'displacement_tex' in locals():
          displacement_tex.location = curr_pos
          displacement_node.location = [displacement_tex.location.x, (displacement_tex.location.y - padding_y)]
          curr_pos = [displacement_tex.location.x, (displacement_tex.location.y - padding_y)]
          if 'principled_node' in locals():          
            node_tree.links.new(displacement_tex.outputs[0], displacement_node.inputs['Height'])
          node_tree.links.new(mapping_node.outputs[0], displacement_tex.inputs['Vector'])            

        if 'normal_tex' in locals():
          normal_tex.location = [curr_pos[0], (curr_pos[1] - 300)]
          normal_node.location = [normal_tex.location.x, normal_tex.location.y - padding_y]
          node_tree.links.new(normal_tex.outputs[0], normal_node.inputs['Color'])
          if 'principled_node' in locals():                
            node_tree.links.new(normal_node.outputs[0], principled_node.inputs['Normal'])    
          node_tree.links.new(mapping_node.outputs[0], normal_tex.inputs['Vector'])            

        #* Organize Texture Coordinate and Mapping Node    
          mapping_node.location = [(albedo_tex.location.x - 200), albedo_tex.location.y]
          texture_coord_node.location = [(mapping_node.location.x - 180), mapping_node.location.y] 

        #* Deselect all items
        bpy.ops.node.select_all(action='DESELECT')
        node_tree.nodes.active = albedo_tex

        #* Create Material Output Node
        if 'principled_node' in locals():
          # Render Output for Cycles
          output_cycles = node_tree.nodes.new('ShaderNodeOutputMaterial')
          output_cycles.target = 'CYCLES'
          output_cycles.location = [(principled_node.location.x + 300), principled_node.location.y]

          # Render Output for Cycles
          output_eevee = node_tree.nodes.new('ShaderNodeOutputMaterial')
          output_eevee.target = 'EEVEE'
          output_eevee.location = [(principled_node.location.x + 300), principled_node.location.y - 200]

          node_tree.links.new(principled_node.outputs[0],output_cycles.inputs['Surface'])          
          node_tree.links.new(principled_node.outputs[0],output_eevee.inputs['Surface'])       

      return {'FINISHED'}

#* REGISTER
#* Add all classes below, it will automatically register and unregister

def register_mat_nodeautoname():
    bpy.utils.register_class(OPSTYIX_OT_MAT_NodeAutoname)
    
def unregister_mat_nodeautoname():
    bpy.utils.unregister_class(OPSTYIX_OT_MAT_NodeAutoname)

#* RUN ON LOAD
print("mat_nodeautoname.py loaded")