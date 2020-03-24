# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; version 2
#  of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
"""Utils function.

Most functions here will be deprecated"""

import math

import bmesh
import bpy
import mathutils

from . import global_def, geometry

def InitBMesh():
    """Init global bmesh."""
    global_def.bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
    global_def.bm.faces.ensure_lookup_table()
    # uvlayer = bm.loops.layers.uv.active

    global_def.uvlayer = global_def.bm.loops.layers.uv.verify()
    #global_def.bm.faces.layers.tex.verify()


def update():
    """Update mesh in blender."""
    bmesh.update_edit_mesh(bpy.context.edit_object.data, False, False)
    # bm.to_mesh(bpy.context.object.data)
    # bm.free()
