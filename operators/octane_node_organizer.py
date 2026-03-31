import bpy

from bpy.types import Operator

# Function to format the name based on texture keywords
def format_texture_name(image_name):
    # Define keyword mappings
    keyword_map = {
        "albedo|diffuse|base color": "Albedo",  # Group variations of "Albedo"
        "roughness": "Roughness",
        "bump": "Bump",
        "specular": "Specular",
        "displacement": "Displacement",
        "normal": "Normal",
        "transmission": "Transmission",
        "opacity": "Opacity",
    }
    
    # Convert the image name to lowercase for case-insensitive matching
    lower_name = image_name.lower()
    
    # Check for keywords in the image name
    for keyword, formatted_name in keyword_map.items():
        if keyword in lower_name:
            return formatted_name
    
    # If no keyword matches, use the original image name
    return image_name.title()  # Convert to title case for better presentation

# Function to check if the texture should be RGB or Greyscale
def determine_texture_type(image_name):
    # Define keywords that suggest a Greyscale texture
    greyscale_keywords = ['roughness', 'bump', 'displacement', 'specular']
    
    # Convert the image name to lowercase for case-insensitive matching
    lower_name = image_name.lower()
    
    # Check if any of the greyscale keywords are in the image name
    for keyword in greyscale_keywords:
        if keyword in lower_name:
            return 'Greyscale'  # Suggest Greyscale node
    
    return 'RGB'  # Default to RGB if no Greyscale keywords are found

# Function to rename, relabel, and convert the node type for selected Octane image nodes
def update_selected_octane_image_nodes():
    # Get the active object
    obj = bpy.context.object
    if not obj or not obj.active_material:
        print("No active object or material found.")
        return
    
    # Get the active material's node tree
    mat = obj.active_material
    if not mat.use_nodes:
        print("The active material is not using nodes.")
        return
    
    nodes = mat.node_tree.nodes
    selected_nodes = [node for node in nodes if node.select]  # Get all selected nodes
    
    if not selected_nodes:
        print("No nodes selected.")
        return
    
    renamed_nodes = 0
    
    for node in selected_nodes:
        # Check if the node is an Octane RGB Image, Octane Greyscale Image, or ShaderNodeTexImage node
        if node.bl_idname in {'OctaneRGBImage', 'OctaneGreyscaleImage', 'ShaderNodeTexImage'}:
            image = node.image
            if image:
                # Format the name and relabel the node
                old_name = node.name
                new_name = format_texture_name(image.name)
                node.name = new_name
                node.label = new_name  # Ensure the label is also updated
                print(f"Renamed and relabeled node from '{old_name}' to '{new_name}'.")
                
                # Determine if the texture is RGB or Greyscale
                texture_type = determine_texture_type(image.name)
                
                # Convert node to the appropriate type if it's a 'ShaderNodeTexImage'
                if node.bl_idname == 'ShaderNodeTexImage':
                    if texture_type == 'Greyscale':
                        # Convert to Greyscale node type
                        new_node = node.id_data.nodes.new('OctaneGreyscaleImage')
                        new_node.location = node.location
                        new_node.image = image
                        new_node.name = new_name  # Set the new name for the new node
                        new_node.label = new_name  # Set the new label for the new node
                        
                        # If the texture is opacity, specular, or normal, modify its value to 1.0
                        if 'opacity' in new_name.lower() or 'specular' in new_name.lower() or 'normal' in new_name.lower():
                            new_node.inputs[2].default_value = 1.0
                            print(f"Set value of '{new_name}' to 1.0 (opacity/specular/normal texture).")
                        
                        mat.node_tree.nodes.remove(node)  # Remove the old node
                        print(f"Converted 'ShaderNodeTexImage' node to 'OctaneGreyscaleImage'.")
                    elif texture_type == 'RGB':
                        # Convert to RGB node type
                        new_node = node.id_data.nodes.new('OctaneRGBImage')
                        new_node.location = node.location
                        new_node.image = image
                        new_node.name = new_name  # Set the new name for the new node
                        new_node.label = new_name  # Set the new label for the new node
                        
                        mat.node_tree.nodes.remove(node)  # Remove the old node
                        print(f"Converted 'ShaderNodeTexImage' node to 'OctaneRGBImage'.")
                
                # For existing Octane image nodes, just ensure it's the right type
                elif texture_type == 'Greyscale' and node.bl_idname != 'OctaneGreyscaleImage':
                    # Convert to Greyscale node type
                    new_node = node.id_data.nodes.new('OctaneGreyscaleImage')
                    new_node.location = node.location
                    new_node.image = image
                    new_node.name = new_name  # Set the new name for the new node
                    new_node.label = new_name  # Set the new label for the new node
                    
                    # If the texture is opacity, specular, or normal, modify its value to 1.0
                    if 'opacity' in new_name.lower() or 'specular' in new_name.lower() or 'normal' in new_name.lower():
                        new_node.inputs[2].default_value = 1.0
                        print(f"Set value of '{new_name}' to 1.0 (opacity/specular/normal texture).")
                    
                    mat.node_tree.nodes.remove(node)  # Remove the old node
                    print(f"Converted node to Greyscale. Set value to 1.0.")
                elif texture_type == 'RGB' and node.bl_idname != 'OctaneRGBImage':
                    # Convert to RGB node type
                    new_node = node.id_data.nodes.new('OctaneRGBImage')
                    new_node.location = node.location
                    new_node.image = image
                    new_node.name = new_name  # Set the new name for the new node
                    new_node.label = new_name  # Set the new label for the new node
                    
                    mat.node_tree.nodes.remove(node)  # Remove the old node
                    print(f"Converted node to RGB.")
                
                renamed_nodes += 1
            else:
                print(f"Selected node '{node.name}' does not have an image assigned.")
        else:
            print(f"Node '{node.name}' is not a supported image node.")
    
    if renamed_nodes == 0:
        print("No image nodes were renamed or converted.")
    else:
        print(f"Renamed, relabeled, and possibly converted {renamed_nodes} image nodes.")

class OPSTYIX_OT_OctaneNodeOrganizer(Operator):
    bl_idname = "opstyix.octane_node_autoname"
    bl_label  = "Auto-Name Nodes"

    def execute(self, context):
        
        # Run the function
        update_selected_octane_image_nodes()

        return {'FINISHED'}

#* REGISTER
#* Add all classes below, it will automatically register and unregister

def register():
    bpy.utils.register_class(OPSTYIX_OT_OctaneNodeOrganizer)
    
def unregister():
    bpy.utils.unregister_class(OPSTYIX_OT_OctaneNodeOrganizer)
