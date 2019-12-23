#   BLEND2HALO2
#
#   Installation:   To properly install this addon to Blender, drop it in your
#
#                   /.../Blender Foundation/Blender/<version>/scripts/addons/
#
#                   directory. Then in Blender, open a User Preferences panel,
#
#                   select the Add-ons tab at the top, select the Import-Export
#
#                   category to the left, scroll to find Import-Export: blend2halo2,
#
#                   and check the box on the very right side of the label. Press
#
#                   the Save User Settings button at the bottom right if you
#
#                   would like the addon to be enabled on startup for Blender.
#
#   Description:    This script will export your file into a Halo 2 Asset file
#
#                   comatable with H2Tool.  
#   
#   Scene Setup:    Create a simple mesh object and name it "b_levelroot" (no
#
#                   quotes).  Parent all of the mesh objects directly to
#
#                   b_levelroot.  Then YOU MUST UV unwrap every mesh, including
#
#                   the b_levelroot object.  YOU MUST apply a material to every
#
#                   exported object, including the b_levelroot object.  Finally,
#
#                   YOU MUST convert all polygons to triangles.  Ounce you have
#
#                   done all of this, go to File -> Export -> Halo 2 Asset.  If
#
#                   succesfull, this script will compile a .ass file compatible
#
#                   with the Halo 2 Tool!
#
#   Instanced Geo   This script does support instanced geometry, just put the %
#
#                   symbol in front of the name, and name the instances with
#
#                   the reference name (with %) then two numbers! So
#
#                   instances of %tree would be %tree01, %tree02, and so on!
#
#                   (no commas). Be careful! Any object name with two numbers
#
#                   at the end will be refered as an instance object!
#
#   Credits         Big thanks to zekilk (cyboryxmen) for making the original
#
#                   HCE exporter script for Blender! I referenced it many
#
#                   times while making this!
#
#   Contact         Email me at: davefeedback1@gmail.com
#
#                   Post on forum.halomaps.org
#
#                   Post on blenderartists.org
#
#   Disclaimer     This script was never optimized to make it user friendly!
#
#                  It will export if you follow the instructions. Feel free
#
#                  to modify it and use it as you wish.



bl_info = {
    'name': 'blend2halo2',
    'author': 'Dave Barnes',
    'version': (0, 1, 1),
    'blender': (2, 74, 0),
    'location': 'File > Export > Halo 2 Asset (.ass)',
    'description': 'Import-Export Halo asset file (.ass)',
    'warning': '',
    'category': 'Import-Export'}
    

#Import relavant modules

import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
import os
import getpass
import mathutils

#Define functions and classes

def get_sceneRoot():
    dec0 = '0.0000000000'
    dec1 = '1.0000000000'
    return (
        ';INSTANCE 0' +
        '\n-1' +
        '\n\"Scene Root\"' +
        '\n-1' +
        '\n-1' +
        '\n0' +
        '\n%s\t%s\t%s\t%s' % (dec0, dec0, dec0, dec1) +
        '\n%s\t%s\t%s' % (dec0, dec0, dec0) +
        '\n%s' % (dec1) +
        '\n%s\t%s\t%s\t%s' % (dec0, dec0, dec0, dec1) +
        '\n%s\t%s\t%s' % (dec0, dec0, dec0) +
        '\n%s' % (dec1)
        )

def get_levelRoot():
    try:
        return bpy.data.objects['b_levelroot']
    except:
        print('Error: You need to parent all export geometry to an object named \"b_levelroot\".')

def get_child_list(parent):
    child_list = []
    for child in parent.children:
        child_list.append(child)
    return child_list

def get_materials_name_list(obj_list, inst_list):
    materials_list = []
    for obj in obj_list:
        for mat in obj.material_slots:
            if mat.name not in materials_list:
                materials_list.append(mat.name)
    for obj in inst_list:
        for mat in obj.material_slots:
            if mat.name not in materials_list:
                materials_list.append(mat.name)
    return materials_list

def write_asset(context, filepath):
    bpy.ops.object.mode_set(mode='OBJECT')
    dec0 = '0.0000000000'
    dec1 = '1.0000000000'
    level_root = get_levelRoot()
    object_list = [level_root]
    instance_geometry_list = []
    for child in get_child_list(level_root):
        if child.name[-2:].isdigit() == False:
            object_list.append(child)
        else:
            instance_geometry_list.append(child)
    materials_list = get_materials_name_list(object_list, instance_geometry_list)
    
    file = open(filepath, 'w',)
    
    #write header
    file.write(
        ';### HEADER ###\n' +
        '2\n' +
        '\"Blender\"\n' +
        '\"%s.%s\"\n' % (bpy.app.version[0], bpy.app.version[1]) +
        '\"%s\"\n' % (getpass.getuser()) +
        '\"%s\"\n' % (os.environ['COMPUTERNAME'])
        )
    
    #write materials
    file.write(
        '\n;### MATERIALS ###\n' +
        str(len(materials_list))
        )
    for mat in materials_list:
        file.write(
        '\n\n;MATERIAL %s' % (materials_list.index(mat)) +
        '\n\"%s\"' % (mat) +
        '\n\"%s\"' % (mat)
        )
    
    #write objects
    file.write(
        '\n\n;### OBJECTS ###' +
        '\n%s' % (str(len(object_list)))
        )
    for obj in object_list:
        mesh = obj.data
        vertlist = []
        facelist = []
        file.write(
            '\n\n;OBJECT %s' %  (object_list.index(obj)) +
            '\n\"%s\"' % (obj.type) +
            '\n\"\"' * 2
            )
        
        #write vertices and uv data
        vertcount = 0
        for poly in mesh.polygons:
            for i in poly.loop_indices:
                vertcount += 1
        file.write(
            '\n{0}'.format(len(mesh.polygons) * 3)
            )
        
        for poly in mesh.polygons:
            for i in poly.loop_indices:
                file.write(
                '\n{0[0]:0.10f}\t{0[1]:0.10f}\t{0[2]:0.10f}'.format(mesh.vertices[mesh.loops[i].vertex_index].co) +
                '\n{0:0.10f}\t{1:0.10f}\t{2:0.10f}'.format(
                    mesh.vertices[mesh.loops[i].vertex_index].normal[0] + 0,
                    mesh.vertices[mesh.loops[i].vertex_index].normal[1] + 0,
                    mesh.vertices[mesh.loops[i].vertex_index].normal[2] + 0) +
                '\n0' +
                '\n1' +
                '\n{0[0]:0.10f}\t{0[1]:0.10f}'.format(mesh.uv_layers.active.data[mesh.loops[i].index].uv)
                )
                    
        #write polygons
        file.write(
            '\n{0}'.format(len(mesh.polygons))
            )
        for poly in mesh.polygons:
            file.write(
                    '\n{0}'.format(materials_list.index(mesh.materials[poly.material_index].name))
                    )
            for i in poly.loop_indices:
                file.write(
                    '\n{0}'.format(i)
                    )
    
    object_list.remove(object_list[0])
    
    #write object instances
    file.write(
        '\n\n;### INSTANCES ####\n' +
        str(len(object_list) + len(instance_geometry_list) + 1) +
        '\n\n' + get_sceneRoot()
        )
    for obj in object_list:
        file.write(
            '\n\n;INSTANCE %s' % (object_list.index(obj) + 1) +
            '\n%s' % (object_list.index(obj) +1) +
            '\n\"%s\"' % (obj.name) +
            '\n%s' % (object_list.index(obj) +1) +
            '\n0' +
            '\n0' +
            '\n%s\t%s\t%s\t%s' % (dec0, dec0, dec0, dec1) +
            '\n{0[0]:0.10f}\t{0[1]:0.10f}\t{0[2]:0.10f}'.format(obj.location) +
            '\n{0[0]:0.10f}'.format(obj.scale) +
            '\n{0[1]:0.10f}\t{0[2]:0.10f}\t{0[3]:0.10f}\t{0[0]:0.10f}'.format(obj.rotation_euler.to_quaternion()) +
            '\n%s\t%s\t%s' % (dec0, dec0, dec0) +
            '\n%s' % (dec1)
            )
    for obj in instance_geometry_list:
        file.write(
            '\n\n;INSTANCE %s' % (len(object_list) + instance_geometry_list.index(obj) + 1) +
            '\n%s' % (object_list.index(bpy.data.objects[obj.name[0:-2]]) +1) +
            '\n\"%s\"' % (obj.name) +
            '\n%s' % (len(object_list) + instance_geometry_list.index(obj) + 1) +
            '\n0' +
            '\n0' +
            '\n%s\t%s\t%s\t%s' % (dec0, dec0, dec0, dec1) +
            '\n{0[0]:0.10f}\t{0[1]:0.10f}\t{0[2]:0.10f}'.format(obj.location) +
            '\n{0[0]:0.10f}'.format(obj.scale) +
            '\n{0[1]:0.10f}\t{0[2]:0.10f}\t{0[3]:0.10f}\t{0[0]:0.10f}'.format(obj.rotation_euler.to_quaternion()) +
            '\n%s\t%s\t%s' % (dec0, dec0, dec0) +
            '\n%s' % (dec1)
            )
    file.close()
    return {'FINISHED'}

class ExportH2Asset(Operator, ExportHelper):
    bl_idname = 'export_halo2.export'
    bl_label = 'Export Halo 2 Asset File (.ass)'
    
    filename_ext = '.ass'
    filter_glob = StringProperty(default='*.ass', options={'HIDDEN'})
    
    def execute(self, context):
        return write_asset(context, self.filepath)

def menu_func_export(self, context):
    self.layout.operator(ExportH2Asset.bl_idname, text='Halo 2 Asset')

def register():
    bpy.utils.register_class(ExportH2Asset)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportH2Asset)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == '__main__':
    register()
