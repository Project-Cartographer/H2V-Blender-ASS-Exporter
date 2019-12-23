#   BLEND2HALO2V2TEST
#
#   Installation:   To properly install this addon to Blender, follow these steps:
#
#                   With Blender open, press Ctrl + Alt + U to open User Preferences. 
#                   
#                   Then go to Add-ons > Install Add-on from File.... browse to open
#
#                   this script.  Then check the box to the left of the blend2halo2
#
#                   Import-Export script.
#
#   Description:    This script will export your file into a Halo 2 Asset file
#
#                   comatable with H2Tool.  
#
#                   THIS IS A TEST RELEASE.  ALWAYS SAVE A COPY OF YOUR WORK
#
#                   BEFORE RUNNING.
#   
#   Scene Setup:    Create a simple mesh object and name it "b_levelroot" (no
#
#                   quotes).  Parent all of the mesh objects directly to
#
#                   b_levelroot.  Then YOU MUST UV unwrap every mesh, including
#
#                   the b_levelroot object.  Ounce you have
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
#                   the reference name (with %) then two or three numbers! So
#
#                   instances of %tree would be %tree01, %tree02, and so on!
#
#                   (no commas). Be careful! Any object name with two numbers
#
#                   at the end will be refered as an instance object!
#
#   Credits         Big thanks to zekilk (cyboryxmen) for making the original
#
#                   HCE exporter script! I referenced it many times while 
#
#                   making this!
#
#   Contact         Email me at: davefeedback1@gmail.com
#
#   Disclaimer     THIS IS A TEST RELEASE.  ALWAYS SAVE A COPY OF YOUR WORK
#
#                   BEFORE RUNNING.
#

bl_info = {
    'name': 'Blend2Halo2',
    'author': 'Dave Barnes (Aerial Dave)',
    'version': (0, 2, 1),
    'blender': (2, 80, 0),
    'location': 'File > Export > Halo 2 Asset (.ass)',
    'description': 'Import-Export Halo asset file (.ass)',
    'warning': '',
    'category': 'Import-Export'}
    

#Import relavant modules

import bpy
import socket
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from os import environ
from getpass import getuser
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

def enable_all_layers():
    bpy.context.view_layer.layer_collection.children

def mesh_tools(obj, triangulate, split):
    print('PRE-DUPLICATE OBJECT: ' + obj.name)
    get_levelRoot().select_set(state = True)
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(state = True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.duplicate(linked=False)
    bpy.context.active_object.name = bpy.context.active_object.name[:-4] + '_blend2h2export'
    new_obj = bpy.context.selected_objects[0]
    print('DUPLICATE OBJECT: ' + new_obj.name)
    bpy.ops.object.mode_set(mode = 'EDIT')
    if triangulate:
        bpy.ops.mesh.select_all(action = 'SELECT')
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    if split:
        bpy.ops.mesh.select_mode(type="FACE")
        bpy.ops.mesh.select_all(action = 'DESELECT')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        for poly in new_obj.data.polygons:
            if poly.use_smooth:
                poly.select = True
        bpy.ops.object.mode_set(mode = 'EDIT')

        try:
            bpy.ops.mesh.separate(type='SELECTED')
        except:
            pass
        bpy.ops.object.mode_set(mode = 'OBJECT')
        act = bpy.context.active_object
        act.modifiers.new(name='edgesplit', type='EDGE_SPLIT')
        #act.modifiers['edgesplit'].split_angle = 30
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier='edgesplit')
        bpy.ops.object.join()
    return bpy.context.active_object #.name[:-15]

def write_asset(context, filepath, triangulate_faces, split_flat):
    enable_all_layers()
    bpy.context.view_layer.objects.active = get_levelRoot()
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    dec0 = '0.0000000000'
    dec1 = '1.0000000000'
    level_root = mesh_tools(
            obj=get_levelRoot(),
            triangulate=triangulate_faces,
            split=split_flat
            )
    object_list = [level_root]
    instance_geometry_list = []
    for child in get_child_list(get_levelRoot()):
        if child.name[-2:].isdigit() == False:
            print('loop: ' + child.name)
            new_child = mesh_tools(
            obj=child,
            triangulate=triangulate_faces,
            split=split_flat
            )
            object_list.append(new_child)
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
        else:
            print('instanced loop: ' + child.name)
            #new_child = mesh_tools(
            #obj=child,
            #triangulate=triangulate_faces,
            #split=split_flat
            #)
            instance_geometry_list.append(child)
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
    materials_list = get_materials_name_list(object_list, instance_geometry_list)
    
    file = open(filepath, 'w',)
    
    #write header
    file.write(
        ';### HEADER ###\n' +
        '2\n' +
        '\"Blender\"\n' +
        '\"%s.%s\"\n' % (bpy.app.version[0], bpy.app.version[1]) +
        '\"%s\"\n' % (getuser()) +
        '\"%s\"\n' % (socket.gethostname())
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
        '\n\""'
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
    objects_to_be_removed = []
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
            '\n\"%s\"' % (obj.name[:-15]) +
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
        objects_to_be_removed.append(obj)
    for obj in instance_geometry_list:
        print(obj.name)
        file.write(
            '\n\n;INSTANCE %s' % (len(object_list) + instance_geometry_list.index(obj) + 1)
            )
        if obj.name[-3].isdigit() == False:
            print('Instanced Format: 01')
            file.write(
                '\n%s' % (object_list.index(bpy.data.objects[obj.name[0:-2] + '_blend2h2export']) +1)
                )
        else:
            if obj.name[-4] == '.':
                print('Instanced Format: .001')
                file.write(
                '\n%s' % (object_list.index(bpy.data.objects[obj.name[0:-4] + '_blend2h2export']) +1)
                )
            else:
                print('Instanced Format: 001')
                file.write(
                '\n%s' % (object_list.index(bpy.data.objects[obj.name[0:-3] + '_blend2h2export']) +1)
                )
        file.write(
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
        #objects_to_be_removed.append(obj)
    for obj in objects_to_be_removed:
        obj.select_set(state = True)
        bpy.ops.object.delete()
    blevelroot = bpy.data.objects['b_levelroot_blend2h2export']
    blevelroot.select_set(state = True)
    bpy.ops.object.delete()
    file.close()
    return {'FINISHED'}

class ExportH2Asset(Operator, ExportHelper):
    bl_idname = 'export_halo2.export'
    bl_label = 'Export Halo 2 Asset File (.ass)'
    triangulate_faces = bpy.props.BoolProperty(
        name ="Triangulate faces",
        description = "Automatically triangulate all faces (recommended)",
        default = True,
        )
    split_flat = bpy.props.BoolProperty(
        name ="Split edges of flat shaded faces",
        description = "Automatically split edges of flat shaded faces (recommended)",
        default = True,
        )
    filename_ext = '.ass'
    filter_glob = StringProperty(default='*.ass', options={'HIDDEN'})
    
    def execute(self, context):
        return write_asset(context, self.filepath, triangulate_faces=self.triangulate_faces, split_flat=self.split_flat)

def menu_func_export(self, context):
    self.layout.operator(ExportH2Asset.bl_idname, text='Halo 2 Asset')

def register():
    bpy.utils.register_class(ExportH2Asset)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportH2Asset)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == '__main__':
    register()

