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

bl_info = {
    "name": "Blend2Halo2 ASS",
    "author": "Dave Barnes (Aerial Dave), modified by General_101",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "File > Export",
    "description": "Exports Halo 2 Amalgam Scene Specification File (.ass)",
    "warning": "",
    "wiki_url": "https://num0005.github.io/h2codez_docs/w/Blender%20Guides/Blender%20Map%20Making%20Tutorial.%20post%202.8.html",
    "support": 'COMMUNITY',
    "category": "Import-Export"}

if "bpy" in locals():
    import importlib
    if "export_ass" in locals():
        importlib.reload(export_ass)

import bpy
import sys
import argparse

from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        )

from bpy.types import (
        Operator,
        Panel,
        PropertyGroup,
        )

from bpy.props import (
        BoolProperty,
        EnumProperty,
        PointerProperty,
        StringProperty,
        )

class ASS_ObjectProps(Panel):
    bl_label = "ASS Object Properties"
    bl_idname = "ASS_PT_ObjectPanel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        obj = context.object
        ass = obj.ass

        row = layout.row()
        row.prop(ass, "Object_Type")

        row = layout.row()
        row.prop(ass, "XREF_path")
        
class ASS_ObjectPropertiesGroup(PropertyGroup):
    Object_Type: EnumProperty(
        name="Object Type:",
        description="Select object type to write mesh as",
        default = "MESH",
        items=[ ('SPHERE', "Sphere", ""),
                ('BOX', "Box", ""),
                ('PILL', "Pill", ""),
                ('MESH', "Mesh", ""),
               ]
        )

    XREF_path: StringProperty(
        name="XREF Object",
        description="Select a path to a .MAX file",
        subtype="FILE_PATH"
    )        

class ExportASS(Operator, ExportHelper):
    """Write an ASS file"""
    bl_idname = 'export_scene.ass'
    bl_label = 'Export ASS'

    filename_ext = '.ass'

    ass_version: EnumProperty(
        name="Version:",
        description="What version to use for the model file",
        default="2",
        items=[ ('1', "1", "Non-functional"),
                ('2', "2", ""),
               ]
        )
        
    triangulate_faces: BoolProperty(
        name ="Triangulate faces",
        description = "Automatically triangulate all faces (recommended)",
        default = True,
        )

    split_flat: BoolProperty(
        name ="Split edges of flat shaded faces",
        description = "Automatically split edges of flat shaded faces (recommended)",
        default = True,
        )

    filter_glob: StringProperty(
        default="*.ass",
        options={'HIDDEN'},
        )        

    def execute(self, context):
        from . import export_ass
        if '--' in sys.argv:
            argv = sys.argv[sys.argv.index('--') + 1:]
            parser = argparse.ArgumentParser()
            parser.add_argument('-arg1', '--filepath', dest='filepath', metavar='FILE', required = True)
            parser.add_argument('-arg2', '--ass_version', dest='ass_version', type=str, default="2")            
            parser.add_argument('-arg3', '--triangulate_faces', dest='triangulate_faces', action='store_true')
            args = parser.parse_known_args(argv)[0]
            print('filepath: ', args.filepath)
            print('ass_version: ', args.ass_version)
            print('triangulate_faces: ', args.triangulate_faces)

        if len(self.filepath) == 0:
            self.filepath = args.filepath
            self.ass_version = args.ass_version
            self.triangulate_faces = args.triangulate_faces
 
        return export_ass.write_file(context, self.filepath, self.report, self.ass_version, triangulate_faces=self.triangulate_faces, split_flat=self.split_flat)

def menu_func_export(self, context):
    self.layout.operator(ExportASS.bl_idname, text='Halo 2 Amalgam Scene Specification (.ass)')

classesass = (
    ASS_ObjectPropertiesGroup,
    ASS_ObjectProps,
    ExportASS
)

def register():
    for clsass in classesass:
        bpy.utils.register_class(clsass)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.Object.ass = PointerProperty(type=ASS_ObjectPropertiesGroup, name="ASS Properties", description="ASS Object properties")

def unregister():
    for clsass in reversed(classesass):
        bpy.utils.unregister_class(clsass)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    del bpy.types.Object.ass

if __name__ == '__main__':
    register()
