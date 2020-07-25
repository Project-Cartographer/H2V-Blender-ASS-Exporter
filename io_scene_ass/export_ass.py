# ##### BEGIN MIT LICENSE BLOCK #####
#
# MIT License
#
# Copyright (c) 2020 Dave Barnes and Steven Garcia
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# ##### END MIT LICENSE BLOCK #####

import os
import bpy
import socket

from decimal import *
from getpass import getuser

def unhide_all_collections():
    for collection_viewport in bpy.context.view_layer.layer_collection.children:
        collection_viewport.hide_viewport = False

    for collection_hide in bpy.data.collections:
        collection_hide.hide_select = False
        collection_hide.hide_viewport = False
        collection_hide.hide_render = False

def unhide_all_objects():
    for obj in bpy.context.view_layer.objects:
        obj.hide_set(False)
        obj.hide_select = False
        obj.hide_viewport = False
        obj.hide_render = False

def write_file(context, filepath, report, ass_version, triangulate_faces, split_flat):
    unhide_all_collections()
    unhide_all_objects()

    object_list = list(bpy.context.scene.objects)

    material_list = []
    node_list = []
    original_node_list = []
    geometry_list = []
    original_geometry_list = []
    instance_geometry_list = []
    original_instance_geometry_list = []
    unique_instance_geometry_list = []
    original_unique_instance_geometry_list = []

    version = int(ass_version)

    for obj in object_list:
        assigned_materials_list = []
        if obj.name[0:2].lower() == 'b_':
            modifier_list = []
            if triangulate_faces:
                for modifier in obj.modifiers:
                    modifier.show_render = True
                    modifier.show_viewport = True
                    modifier.show_in_editmode = True
                    modifier_list.append(modifier.type)

                if not 'TRIANGULATE' in modifier_list:
                    obj.modifiers.new("Triangulate", type='TRIANGULATE')

                depsgraph = context.evaluated_depsgraph_get()
                obj_for_convert = obj.evaluated_get(depsgraph)
                me = obj_for_convert.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
                node_list.append(me)
                original_node_list.append(obj)
                
            else:
                node_list.append(obj.to_mesh(preserve_all_data_layers=True))
                original_node_list.append(obj)            

        elif obj.name[0:1].lower() == '%':
            mesh_name = obj.data.name
            print(obj.data.name)
            if not obj.data.name in unique_instance_geometry_list:
                unique_instance_geometry_list.append(obj.data.name)

            obj.data = obj.data.copy()
            
            modifier_list = []
            if triangulate_faces:
                for modifier in obj.modifiers:
                    modifier.show_render = True
                    modifier.show_viewport = True
                    modifier.show_in_editmode = True
                    modifier_list.append(modifier.type)

                if not 'TRIANGULATE' in modifier_list:
                    obj.modifiers.new("Triangulate", type='TRIANGULATE')

                depsgraph = context.evaluated_depsgraph_get()
                obj_for_convert = obj.evaluated_get(depsgraph)
                me = obj_for_convert.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
                instance_geometry_list.append([me, mesh_name])
                original_instance_geometry_list.append([obj, mesh_name])

            else:
                instance_geometry_list.append([obj.to_mesh(preserve_all_data_layers=True), mesh_name])
                original_instance_geometry_list.append([obj, mesh_name]) 

        elif obj.type== 'MESH':
            modifier_list = []
            if triangulate_faces:
                for modifier in obj.modifiers:
                    modifier.show_render = True
                    modifier.show_viewport = True
                    modifier.show_in_editmode = True
                    modifier_list.append(modifier.type)

                if not 'TRIANGULATE' in modifier_list:
                    obj.modifiers.new("Triangulate", type='TRIANGULATE')

                depsgraph = context.evaluated_depsgraph_get()
                obj_for_convert = obj.evaluated_get(depsgraph)
                me = obj_for_convert.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
                geometry_list.append(me)
                original_geometry_list.append(obj)

            else:
                geometry_list.append(obj.to_mesh(preserve_all_data_layers=True))
                original_geometry_list.append(obj)

        if len(obj.material_slots)!= 0:
            for f in obj.data.polygons:
                slot = obj.material_slots[f.material_index]
                mat = slot.material
                if mat is not None:
                    if mat not in assigned_materials_list:
                        assigned_materials_list.append(mat)

            for slot in obj.material_slots:
                if slot.material not in material_list and slot.material in assigned_materials_list:
                    material_list.append(slot.material)

    mesh_data_name_list = []
    unique_instance_object_list = []
    original_mesh_data_name_list = []
    original_unique_instance_object_list = []    
    for instance_geo in instance_geometry_list:
        if not instance_geo[1] in mesh_data_name_list:
            mesh_data_name_list.append(instance_geo[1])
            unique_instance_object_list.append(instance_geo[0])
            
    for instance_geo in original_instance_geometry_list:
        if not instance_geo[1] in original_mesh_data_name_list:
            original_mesh_data_name_list.append(instance_geo[1])
            original_unique_instance_object_list.append(instance_geo[0])            

    obdata = [bpy.data.meshes.new('Scene Root')]
    
    joined_geometry_list = node_list + geometry_list + unique_instance_object_list
    joined_orignal_geometry_list = original_node_list + original_geometry_list + original_unique_instance_object_list
    joined_instance_list = obdata + node_list + geometry_list + instance_geometry_list
    
    joined_geometry_count = len(joined_geometry_list)
    joined_instance_count = len(joined_instance_list)
    joined_orignal_geometry_count = len(joined_orignal_geometry_list)
    material_count = len(material_list)
    geometry_count = len(geometry_list)

    file = open(filepath, 'w',)

    #write header
    file.write(
        ';### HEADER ###' +
        '\n%s' % (ass_version) +
        '\n"BLENDER"' +
        '\n"%s.%s"' % (bpy.app.version[0], bpy.app.version[1]) +
        '\n"%s"' % (getuser()) +
        '\n"%s"\n' % (socket.gethostname().upper())
    )

    #write materials
    file.write(
        '\n;### MATERIALS ###' +
        '\n%s\n' % (material_count)
    )

    for material in material_list:
        material_effect_name = ''
        file.write(
            '\n;MATERIAL %s' % (material_list.index(material)) +
            '\n"%s"' % (material.name) +
            '\n"%s"\n' % (material_effect_name)
        )

    #write objects
    file.write(
        '\n;### OBJECTS ###' +
        '\n%s\n' % (joined_geometry_count)
    )

    for geometry in joined_geometry_list:   
        item_index = int(joined_geometry_list.index(geometry))
        original_geo = joined_orignal_geometry_list[item_index]
        xref_filepath = bpy.path.abspath(original_geo.ass.XREF_path)
        vertex_count = len(geometry.polygons) * 3
        triangle_count = len(geometry.polygons)
        geometry_material_count = len(original_geo.material_slots)
        assigned_geometry_materials_list = []
        if geometry_material_count != 0:
            for f in geometry.polygons:            
                mat = bpy.data.materials[geometry.materials[f.material_index].name]
                if mat is not None:
                    if mat not in assigned_geometry_materials_list:
                        assigned_geometry_materials_list.append(mat)

        assigned_geometry_materials_count = len(assigned_geometry_materials_list)
        if xref_filepath != "":
            xref_objectname = original_geo.name

        else:
            xref_objectname = ""

        if original_geo.ass.Object_Type == 'MESH':
            file.write(
                '\n;OBJECT %s' %  (joined_geometry_list.index(geometry)) +
                '\n"%s"' % (original_geo.ass.Object_Type) +
                '\n"%s"' % (xref_filepath) +
                '\n"%s"' % (xref_objectname) +
                '\n%s' % (vertex_count)
            )

            for poly in geometry.polygons:
                for indice in poly.loop_indices:
                    pos = geometry.vertices[geometry.loops[indice].vertex_index].co
                    norm = geometry.vertices[geometry.loops[indice].vertex_index].normal
                    uv = geometry.uv_layers.active.data[geometry.loops[indice].index].uv

                    pos_x = Decimal(pos[0]).quantize(Decimal('1.0000000000'))
                    pos_y = Decimal(pos[1]).quantize(Decimal('1.0000000000'))
                    pos_z = Decimal(pos[2]).quantize(Decimal('1.0000000000'))

                    norm_i = Decimal(norm[0]).quantize(Decimal('1.0000000000'))
                    norm_j = Decimal(norm[1]).quantize(Decimal('1.0000000000'))
                    norm_k = Decimal(norm[2]).quantize(Decimal('1.0000000000'))

                    node_influence_count = 0
                    tex_coord_count = 1

                    tex_u = Decimal(uv[0]).quantize(Decimal('1.0000000000'))
                    tex_v = Decimal(uv[1]).quantize(Decimal('1.0000000000'))

                    file.write(
                        '\n%0.10f\t%0.10f\t%0.10f' % (pos_x, pos_y, pos_z) +
                        '\n%0.10f\t%0.10f\t%0.10f' % (norm_i, norm_j, norm_k) +
                        '\n%s' % (node_influence_count) +
                        '\n%s' % (tex_coord_count) +
                        '\n%0.10f\t%0.10f' % (tex_u, tex_v)
                    )

            #write polygons
            file.write(
                '\n%s' % (triangle_count)
            )

            for poly in geometry.polygons:
                triangle_material = -1
                if geometry_material_count != 0:
                    triangle_material = material_list.index(bpy.data.materials[geometry.materials[poly.material_index].name])

                file.write(
                    '\n%s' % (triangle_material)
                )

                for indice in poly.loop_indices:
                    file.write(
                        '\n%s' % (indice)
                    )

        elif original_geo.ass.Object_Type == 'SPHERE':
            material_index = -1
            if assigned_geometry_materials_count != 0:
                material_index = material_list.index(assigned_geometry_materials_list[0])

            if assigned_geometry_materials_count > 1:
                report({'WARNING'}, "Sphere object %s has more than one material assigned to it's faces. Please use only one material." % (original_geo.name))

            assigned_geometry_materials_list.clear()

            scale = original_geo.dimensions

            scale_x = Decimal(scale[0]).quantize(Decimal('1.0000000000'))
            scale_y = Decimal(scale[1]).quantize(Decimal('1.0000000000'))
            scale_z = Decimal(scale[2]).quantize(Decimal('1.0000000000'))

            sphere_radius = (scale_x/2)
            if not scale_x == scale_y == scale_z:
                report({'WARNING'}, "Scale for object %s is not uniform. Resolve this or understand that what shows up ingame may be different from your scene." % (original_geo.name))

            file.write(
                '\n;OBJECT %s' %  (joined_geometry_list.index(geometry)) +
                '\n"%s"' % (original_geo.ass.Object_Type) +
                '\n"%s"' % (xref_filepath) +
                '\n"%s"' % (xref_objectname) +
                '\n%s' % (material_index) +
                '\n%0.10f' % (sphere_radius)
                )

        elif original_geo.ass.Object_Type == 'BOX':
            material_index = -1
            if assigned_geometry_materials_count != 0:
                material_index = material_list.index(assigned_geometry_materials_list[0])

            if assigned_geometry_materials_count > 1:
                report({'WARNING'}, "Box object %s has more than one material assigned to it's faces. Please use only one material." % (original_geo.name))

            assigned_geometry_materials_list.clear()

            scale = original_geo.dimensions

            scale_x = Decimal(scale[0]).quantize(Decimal('1.0000000000'))
            scale_y = Decimal(scale[1]).quantize(Decimal('1.0000000000'))
            scale_z = Decimal(scale[2]).quantize(Decimal('1.0000000000'))
            
            scale_x_extent = scale_x/2
            scale_y_extent = scale_y/2
            scale_z_extent = scale_z/2

            file.write(
                '\n;OBJECT %s' %  (joined_geometry_list.index(geometry)) +
                '\n"%s"' % (original_geo.ass.Object_Type) +
                '\n"%s"' % (xref_filepath) +
                '\n"%s"' % (xref_objectname) +
                '\n%s' % (material_index) +
                '\n%0.10f\t%0.10f\t%0.10f' % (scale_z_extent, scale_x_extent, scale_y_extent)
                )

        elif original_geo.ass.Object_Type == 'PILL':
            material_index = -1
            if assigned_geometry_materials_count != 0:
                material_index = material_list.index(assigned_geometry_materials_list[0])

            if assigned_geometry_materials_count > 1:
                report({'WARNING'}, "Box object %s has more than one material assigned to it's faces. Please use only one material." % (original_geo.name))

            assigned_geometry_materials_list.clear()

            scale = original_geo.dimensions

            scale_x = Decimal(scale[0]).quantize(Decimal('1.0000000000'))
            scale_y = Decimal(scale[1]).quantize(Decimal('1.0000000000'))
            scale_z = Decimal(scale[2]).quantize(Decimal('1.0000000000'))

            if (scale_x * 2) < scale_y:
                pill_height = (scale_x * 2)/2
                report({'WARNING'}, "Pill object %s's Y scale is less than the value of scale X doubled. Please use only a value that is double your X scale" % (original_geo.name))                

            else:
                pill_height = scale_y/2

            pill_radius = scale_x/2

            file.write(
                '\n;OBJECT %s' %  (joined_geometry_list.index(geometry)) +
                '\n"%s"' % (original_geo.ass.Object_Type) +
                '\n"%s"' % (xref_filepath) +
                '\n"%s"' % (xref_objectname) +
                '\n%s' % (material_index) +
                '\n%0.10f' % (pill_height) +
                '\n%0.10f' % (pill_radius)
                )

        file.write(
            '\n'
        )
        
    #write instances
    file.write(
        '\n;### INSTANCES ###' +
        '\n%s\n' % (joined_instance_count)
    ) 

    for instance in joined_instance_list:
        object_index = -1
        unique_instance_ID = -1
        parent_instance_ID = -1      
        inheritance_flag = 0        
        if not instance.name == 'Scene Root':
            object_index = joined_instance_list.index(instance) - 1
            unique_instance_ID = joined_instance_list.index(instance) - 1
            parent_instance_ID = joined_instance_list.index(instance) - 1
            
        bone_matrix = node.matrix_world

        if node.parent:
            bone_matrix = node.parent.matrix_local @ node.matrix_world
            
        pos  = bone_matrix.translation
        quat = bone_matrix.to_quaternion()        
        if isinstance(instance, list):
            if not instance[1] == None:
                inheritance_flag = 1         
        
        local_quat_i = Decimal(0).quantize(Decimal('1.0000000000'))
        local_quat_j = Decimal(0).quantize(Decimal('1.0000000000'))
        local_quat_k = Decimal(1).quantize(Decimal('1.0000000000'))
        local_quat_w = Decimal(0).quantize(Decimal('1.0000000000'))
        
        local_pos_x = Decimal(0).quantize(Decimal('1.0000000000'))
        local_pos_y = Decimal(0).quantize(Decimal('1.0000000000'))
        local_pos_z = Decimal(0).quantize(Decimal('1.0000000000'))
        
        local_scale_x = Decimal(0).quantize(Decimal('1.0000000000'))
        local_scale_y = Decimal(0).quantize(Decimal('1.0000000000'))
        local_scale_z = Decimal(0).quantize(Decimal('1.0000000000'))        
        
        pivot_quat_i = Decimal(0).quantize(Decimal('1.0000000000'))
        pivot_quat_j = Decimal(0).quantize(Decimal('1.0000000000'))
        pivot_quat_k = Decimal(1).quantize(Decimal('1.0000000000'))
        pivot_quat_w = Decimal(0).quantize(Decimal('1.0000000000'))
        
        pivot_pos_x = Decimal(0).quantize(Decimal('1.0000000000'))
        pivot_pos_y = Decimal(0).quantize(Decimal('1.0000000000'))
        pivot_pos_z = Decimal(0).quantize(Decimal('1.0000000000'))
        
        pivot_scale_x = Decimal(0).quantize(Decimal('1.0000000000'))
        pivot_scale_y = Decimal(0).quantize(Decimal('1.0000000000'))
        pivot_scale_z = Decimal(0).quantize(Decimal('1.0000000000'))          
        
        file.write(
            '\n;INSTANCE %s' % (joined_instance_list.index(instance)) +
            '\n%s' % (object_index) +
            '\n\"%s\"' % (instance.name) +
            '\n%s' % (unique_instance_ID) +
            '\n%s' % (parent_instance_ID) +
            '\n%s' % (inheritance_flag) +
            '\n%0.10f\t%0.10f\t%0.10f\t%0.10f' % (local_quat_i, local_quat_j, local_quat_k, local_quat_w) +
            '\n%0.10f\t%0.10f\t%0.10f' % (local_pos_x, local_pos_y, local_pos_z) +
            '\n%0.10f' % (local_scale_x) +
            '\n%0.10f\t%0.10f\t%0.10f\t%0.10f' % (pivot_quat_i, pivot_quat_j, pivot_quat_k, pivot_quat_w) +
            '\n%0.10f\t%0.10f\t%0.10f' % (pivot_pos_x, pivot_pos_y, pivot_pos_z) +
            '\n%0.10f\n' % (pivot_scale_x)
            )
            
    file.close()
    return {'FINISHED'}

if __name__ == '__main__':
    bpy.ops.export_scene.ass()
