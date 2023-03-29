class NWAddPrincipledSetup(Operator, NWBase, ImportHelper):
    bl_idname = "opstyix.hdri_setup"
    bl_label = "HDRI Setup" # Updated Label for accuracy - OPSTYIX
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    directory: StringProperty(
        name='Directory',
        subtype='DIR_PATH',
        default='',
        description='Folder to search in for image files'
    )
    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    relative_path: BoolProperty(
        name='Relative Path',
        description='Select the file relative to the blend file',
        default=True
    )

    order = [
        "filepath",
        "files",
    ]

    def draw(self, context):
        layout = self.layout
        layout.alignment = 'LEFT'

        layout.prop(self, 'relative_path')

    @classmethod
    def poll(cls, context):
        valid = False
        if nw_check(context):
            space = context.space_data
            if space.tree_type == 'ShaderNodeTree':
                valid = True
        return valid


    ###
    ### For octane's shaders
    ###

    def execute_octane(self, context):
        # Check if everything is ok
        if not self.directory:
            self.report({'INFO'}, 'No Folder Selected')
            return {'CANCELLED'}
        if not self.files[:]:
            self.report({'INFO'}, 'No Files Selected')
            return {'CANCELLED'}

        nodes, links = get_nodes_links(context)
        active_node = nodes.active

        # Octane shader's names
        # ShaderNodeOctUniversalMat
        # ShaderNodeOctMetalMat
        # ShaderNodeOctToonMat
        # ShaderNodeOctSpecularMat
        # ShaderNodeOctDiffuseMat
        # ShaderNodeOctGlossyMat
        # ShaderNodeOctHairMat

        if not (active_node and active_node.bl_idname in ['OctaneUniversalMaterial', 
                                                          'OctaneMetallicMaterial',
                                                          'OctaneToonMaterial',
                                                          'OctaneSpecularMaterial',
                                                          'OctaneDiffuseMaterial',
                                                          'OctaneGlossyMaterial',
                                                          'OctaneHairMaterial']):
            self.report({'INFO'}, 'Select Shader Node')
            return {'CANCELLED'}

        # Helper_functions
        def split_into__components(fname):
            # Split filename into components
            # 'WallTexture_diff_2k.002.jpg' -> ['Wall', 'Texture', 'diff', 'k']
            # Remove extension
            fname = path.splitext(fname)[0]
            # Remove digits
            fname = ''.join(i for i in fname if not i.isdigit())
            # Separate CamelCase by space
            fname = re.sub("([a-z])([A-Z])","\g<1> \g<2>",fname)
            # Replace common separators with SPACE
            seperators = ['_', '.', '-', '__', '--', '#']
            for sep in seperators:
                fname = fname.replace(sep, ' ')

            components = fname.split(' ')
            components = [c.lower() for c in components]
            return components

        # Filter textures names for texturetypes in filenames
        # [Socket Name, [abbreviations and keyword list], Filename placeholder]
        tags = context.preferences.addons[__name__].preferences.principled_tags
        normal_abbr = tags.normal.split(' ')
        bump_abbr = tags.bump.split(' ')
        gloss_abbr = tags.gloss.split(' ')
        rough_abbr = tags.rough.split(' ')
        socketnames = [
        ['Displacement', tags.displacement.split(' '), None],
        ['Albedo color', tags.base_color.split(' '), None],
        ['Albedo', tags.base_color.split(' '), None],
        ['Diffuse', tags.base_color.split(' '), None],
        ['Medium', tags.sss_color.split(' '), None],
        ['Metallic', tags.metallic.split(' '), None],
        ['Specular', tags.specular.split(' '), None],
        ['Roughness', rough_abbr + gloss_abbr, None],
        ['Bump', bump_abbr, None],
        ['Normal', normal_abbr, None],
        ]

        # Look through texture_types and set value as filename of first matched file
        def match_files_to_socket_names():
            for sname in socketnames:
                for file in self.files:
                    fname = file.name
                    filenamecomponents = split_into__components(fname)
                    matches = set(sname[1]).intersection(set(filenamecomponents))
                    # TODO: ignore basename (if texture is named "fancy_metal_nor", it will be detected as metallic map, not normal map)
                    if matches:
                        sname[2] = fname
                        break

        match_files_to_socket_names()
        # Remove socketnames without found files
        socketnames = [s for s in socketnames if s[2]
                       and path.exists(self.directory+s[2])]
        if not socketnames:
            self.report({'INFO'}, 'No matching images found')
            print('No matching images found')
            return {'CANCELLED'}

        # Don't override path earlier as os.path is used to check the absolute path
        import_path = self.directory
        if self.relative_path:
            if bpy.data.filepath:
                import_path = bpy.path.relpath(self.directory)
            else:
                self.report({'WARNING'}, 'Relative paths cannot be used with unsaved scenes!')
                print('Relative paths cannot be used with unsaved scenes!')

        # Add found images
        print('\nMatched Textures:')
        texture_nodes = []
        texture_node = None
        disp_texture = None
        normal_node = None
        roughness_node = None
        for i, sname in enumerate(socketnames):
            if not sname[0] in active_node.inputs:
                continue

            # DISPLACEMENT NODES
            if sname[0] == 'Displacement':
                disp_texture = nodes.new(type='ShaderNodeOctFloatImageTex')
                disp_texture.inputs[2].default_value = 1 # OPSTYIX Patch
                img = bpy.data.images.load(path.join(import_path, sname[2]))
                disp_texture.image = img
				
                disp_texture.label = 'Displacement'
                #if disp_texture.image:
                #    disp_texture.image.colorspace_settings.is_data = True

                # Add displacement offset nodes
                settings = context.preferences.addons[__name__].preferences
                disp_node = nodes.new(type=settings.texture_setup_displacement)
                disp_node.location = active_node.location + Vector((-200, -1110))
                link = links.new(disp_node.inputs[0], disp_texture.outputs[0])

                # TODO Turn on true displacement in the material
                # Too complicated for now

                # Find output node
                output_node = [n for n in nodes if n.bl_idname == 'ShaderNodeOutputMaterial']
                if output_node:
                    if not output_node[0].inputs[2].is_linked:
                        link = links.new(active_node.inputs[sname[0]], disp_node.outputs[0])

                continue

            if not active_node.inputs[sname[0]].is_linked:
                # No texture node connected -> add texture node with new image
                texture_node = None

                if sname[0] in ['Metallic', 'Roughness', 'Specular']:
                    texture_node = nodes.new(type='ShaderNodeOctFloatImageTex')
                    texture_node.inputs[2].default_value = 1  # Set Gamma to 1. OPSTYIX Patch
                else:
                    texture_node = nodes.new(type='ShaderNodeOctImageTex')
                img = bpy.data.images.load(path.join(import_path, sname[2]))
                texture_node.image = img

                # NORMAL NODES
                if sname[0] == 'Normal':
                    link = links.new(active_node.inputs[sname[0]], texture_node.outputs[0])
                    normal_node_texture = texture_node
                    normal_node_texture.inputs[2].default_value = 1

                elif sname[0] == 'Roughness':
                    # Test if glossy or roughness map
                    fname_components = split_into__components(sname[2])
                    match_rough = set(rough_abbr).intersection(set(fname_components))
                    match_gloss = set(gloss_abbr).intersection(set(fname_components))

                    if match_rough:
                        # If Roughness nothing to to
                        link = links.new(active_node.inputs[sname[0]], texture_node.outputs[0])

                    elif match_gloss:
                        # If Gloss Map add invert node
                        invert_node = nodes.new(type='ShaderNodeOctInvertTex')
                        link = links.new(invert_node.inputs[0], texture_node.outputs[0])

                        link = links.new(active_node.inputs[sname[0]], invert_node.outputs[0])
                        roughness_node = texture_node

                else:
                    # This is a simple connection Texture --> Input slot
                    link = links.new(active_node.inputs[sname[0]], texture_node.outputs[0])

                # Use non-color for all but 'Albedo color' Textures
                #if not sname[0] in ['Albedo color'] and texture_node.image:
                    #texture_node.image.colorspace_settings.is_data = True

            else:
                # If already texture connected. add to node list for alignment
                texture_node = active_node.inputs[sname[0]].links[0].from_node

            if texture_node is not None:
                # This are all connected texture nodes
                texture_nodes.append(texture_node)
                texture_node.label = sname[0]

        if disp_texture:
            texture_nodes.append(disp_texture)

        # Alignment
        for i, texture_node in enumerate(texture_nodes):
            offset = Vector((-580, (i * -320) + 250))
            texture_node.location = active_node.location + offset

        if normal_node:
            # Extra alignment if normal node was added
            normal_node.location = normal_node_texture.location + Vector((300, 0))

        if roughness_node:
            # Alignment of invert node if glossy map
            invert_node.location = roughness_node.location + Vector((300, 0))

        # # Add texture input + mapping
        # mapping = nodes.new(type='ShaderNodeOctFullTransform')
        # mapping.location = active_node.location + Vector((-1150, 0))
        # if len(texture_nodes) > 1:
            # # If more than one texture add reroute node in between
            # reroute = nodes.new(type='NodeReroute')
            # tex_coords = Vector((texture_nodes[0].location.x, sum(n.location.y for n in texture_nodes)/len(texture_nodes)))
            # reroute.location = tex_coords + Vector((-50, -120))
            # for texture_node in texture_nodes:
                # link = links.new(texture_node.inputs[4], reroute.outputs[0])
            # link = links.new(reroute.inputs[0], mapping.outputs[0])

            # texture_nodes.append(reroute)
        # else:
            # link = links.new(texture_nodes[0].inputs[0], mapping.outputs[0])

        # Connect texture_coordiantes to mapping node
        #texture_input = nodes.new(type='ShaderNodeOctFullTransform')
        #texture_input.location = mapping.location + Vector((-200, 0))
        #link = links.new(mapping.inputs[0], texture_input.outputs[2])

        # Just to be sure
        active_node.select = False
        nodes.update()
        links.update()
        force_update(context)
        return {'FINISHED'}
    