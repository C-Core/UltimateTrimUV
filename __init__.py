# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Ultimate Trim UV",
    "author" : "C-Core",
    "description" : "Allows automatic scaling/positioning of UVs on Ultimate Trim based texture sheets",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 2),
    "location" : "UV/Image editor > Tool Panel, UV/Image editor UVs > menu",
    "warning" : "",
    "category" : "UV"
}

import bmesh
import bpy
import mathutils

#Credit goes to Luca Carella for his UV Align Distribution Addon providing uv island selection functionality via the following imports
#https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/UV/UV_Align_Distribution
from . import make_islands, utils

# Trims definition
class TrimDef():
  def __init__(self, variant, height, width = 1024.0, x_offset = 0.0, y_offset = -1.0):
    self.variant = variant
    self.height = height
    self.width = width
    self.x_offset = x_offset
    self.y_offset = y_offset

trimSets = {
  "UltimateTrim":[
    TrimDef('A', 128.0),
    TrimDef('B', 128.0),
    TrimDef('C', 128.0),
    TrimDef('D', 128.0),
    TrimDef('A', 64.0),
    TrimDef('B', 64.0),
    TrimDef('C', 64.0),
    TrimDef('D', 64.0),
    TrimDef('A', 32.0),
    TrimDef('B', 32.0),
    TrimDef('C', 32.0),
    TrimDef('D', 32.0),
    TrimDef('A', 16.0),
    TrimDef('B', 16.0),
    TrimDef('S', 96.0, 96.0, 0.0, 96.0),
    TrimDef('S', 32.0, 32.0, 96.0, 96.0),
    TrimDef('S', 32.0, 32.0, 96.0, 32.0),
    TrimDef('S', 96.0, 96.0, 128.0, 96.0),
    TrimDef('S', 96.0, 32.0, 224.0, 96.0),
    TrimDef('S', 96.0, 256.0, 256.0, 96.0),
    TrimDef('S', 96.0, 512.0, 512.0, 96.0),
  ],
  "Edges":[
    TrimDef('A',  6.0, 1024.0, 0.0, 960.0 + 3.0),
    TrimDef('B',  6.0, 1024.0, 0.0, 832.0 + 3.0),
    TrimDef('C', 26.0, 1024.0, 0.0, 704.0 + 13.0),
    TrimDef('D', 26.0, 1024.0, 0.0, 576.0 + 13.0),
    TrimDef('A',  6.0, 1024.0, 0.0, 448.0 + 3.0),
    TrimDef('B',  6.0, 1024.0, 0.0, 320.0 + 3.0),
    TrimDef('C', 26.0, 1024.0, 0.0, 192.0 + 13.0),
    TrimDef('D', 26.0, 1024.0, 0.0,  64.0 + 13.0),
  ]
}

currentTrimDefs = []

# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def AdjustTrimDefs():
  currentYOffset = 1.0

  for set in trimSets.values():
    for trim in set:
      trim.height /= 1024.0
      trim.width /= 1024.0
      trim.x_offset /= 1024.0
      trim.y_offset /= 1024.0
    
      if trim.y_offset < 0.0:
        trim.y_offset = currentYOffset
        currentYOffset -= trim.height

# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def DistanceToAABB(point, aabbMin, aabbMax):
  clampedPoint = mathutils.Vector((max(aabbMin.x, min(aabbMax.x, point.x)), max(aabbMin.y, min(aabbMax.y, point.y))))
  return (point - clampedPoint).length

# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def FindBestMatch(island, variants):

  centerPoint = island.BBox().center()

  bestIndex = 0
  bestDistance = 10000

  for index in range(len(currentTrimDefs)):
    trimDef = currentTrimDefs[index]
    
    if variants != 'ALL' and trimDef.variant != variants:
      continue
    
    trimMin = mathutils.Vector((trimDef.x_offset, trimDef.y_offset - trimDef.height))
    trimMax = mathutils.Vector((trimDef.x_offset + trimDef.width, trimDef.y_offset))
    
    distance = DistanceToAABB(centerPoint, trimMin, trimMax)
    if distance < bestDistance:
      bestIndex = index
      bestDistance = distance
  
  return currentTrimDefs[bestIndex]

# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def UltimateTrimAlign(props):

  global currentTrimDefs
  currentTrimDefs = trimSets[props.trim_set]

  padding = props.uv_padding / float(props.trim_res)
  
  #Creates UV islands out of the selected elements
  makeIslands = make_islands.MakeIslands()
  selectedIslands = makeIslands.selectedIslands()

  #Loops through selected islands and aligns the top of each island with the top of the trim index
  for island in selectedIslands:
  
    trimDef = currentTrimDefs[props.trim_index] if props.trim_index >= 0 else FindBestMatch(island, props.trim_variants)
  
    trimLeft = trimDef.x_offset + padding 
    trimRight = trimDef.x_offset + trimDef.width - padding
    trimHCenter = trimDef.x_offset + trimDef.width * 0.5
  
    trimTop = trimDef.y_offset - padding
    trimBottom = trimDef.y_offset - trimDef.height + padding
    trimVCenter = trimDef.y_offset - trimDef.height * 0.5
  
    #print("Trim:", trimLeft, trimRight, trimTop, trimBottom)
    #print("Island:", size.width, size.height)
  
    #Scale
    size = island.size()
    
    scaleX = 1.0
    scaleY = 1.0
    if props.scale == 'FIT_X':
      scaleX = (trimRight - trimLeft) / size.width
      scaleY = scaleX
    elif props.scale == 'FIT_Y':
      scaleY = (trimTop - trimBottom) / size.height
      scaleX = scaleY
    elif props.scale == 'FIT_BOTH':
      scaleX = (trimRight - trimLeft) / size.width
      scaleY = (trimTop - trimBottom) / size.height
    elif props.scale == 'SET_X':
      scaleX = props.size_x / size.width
    elif props.scale == 'SET_Y':
      scaleY = props.size_y / size.height
    elif props.scale == 'SET_XY':
      scaleX = props.size_x / size.width
      scaleY = props.size_y / size.height
      
    #print("Scale: ", scaleX, scaleY)
      
    island.scale(scaleX, scaleY)
  
    #Move
    bbox = island.BBox()
    
    moveX = 0.0
    if props.h_align == 'LEFT':
      moveX = trimLeft - bbox.left()
    elif props.h_align == 'CENTER':
      moveX = trimHCenter - bbox.center().x
    elif props.h_align == 'RIGHT':
      moveX = trimRight - bbox.right()

    moveY = 0.0
    if props.v_align == 'TOP':
      moveY = trimTop - bbox.top()
    elif props.v_align == 'CENTER':
      moveY = trimVCenter - bbox.center().y
    elif props.v_align == 'BOTTOM':
      moveY = trimBottom - bbox.bottom()
  
    island.move(mathutils.Vector((moveX, moveY)))

  utils.update()

# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def UltimateEdgeAlign(props):

  global currentTrimDefs
  currentTrimDefs = trimSets[props.trim_set]

  #Creates UV islands out of the selected elements
  makeIslands = make_islands.MakeIslands()
  selectedIslands = makeIslands.selectedIslands()

  #Loops through selected islands and aligns the top of each island with the top of the trim index
  for island in selectedIslands:
  
    trimDef = currentTrimDefs[props.trim_index] if props.trim_index >= 0 else FindBestMatch(island, props.trim_variants)
  
    edgeTop = trimDef.y_offset
    edgeBottom = trimDef.y_offset - trimDef.height

    #Scale
    bbox = island.EdgeBBox()
    bboxHeight = bbox.top() - bbox.bottom()
    
    scaleY = (edgeTop - edgeBottom) / bboxHeight
    scaleX = scaleY
    #print("Scale: ", scaleX, scaleY)
      
    island.scale(scaleX, scaleY)

    #Move
    bbox = island.EdgeBBox()
    
    moveX = 0.0
    moveY = edgeTop - bbox.top()

    island.move(mathutils.Vector((moveX, moveY)))

  utils.update()

# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////
class UltimateTrimUVProps(bpy.types.PropertyGroup):
  setItems = []
  for setName in trimSets:
    setItems.append((setName, setName, ''))

  trim_set: bpy.props.EnumProperty(
    items = setItems,
    name = "Trim Set"
  )

  trim_res: bpy.props.EnumProperty(
    items = [
        ('256', '256', ''),
        ('512', '512', ''),
        ('1024', '1024',''),
        ('2048', '2048',''),
        ('4096', '4096',''),
        ('8192', '8192','')],
    name = "Trim Resolution",
    default = "2048"
  )

  uv_padding: bpy.props.FloatProperty(name = "", default = 1.0, min=0.0,
    description = "Shrinks UV islands to avoid touching trim edges. Prevents UVs from bleeding into neighboring "
    "trims when using lower res textures in realtime applications. Use the 'redo last' panel to tweak interactively"
  )
    
  trim_index: bpy.props.IntProperty(name = "", default = -1, min=-1, max=len(trimSets["UltimateTrim"])-1)
  trim_variants: bpy.props.EnumProperty(
     items=[
        ('ALL', "All", ""),
        ('A', "A", ""), 
        ('B', "B", ""),
        ('C', "C", ""),
        ('D', "D", ""),
        ('S', "S", "")],
     name = "Variant Types"
  )
  
  h_align: bpy.props.EnumProperty(name = "Horizontal Alignment", items=[('NONE', "None", ""), ('LEFT', "Left", ""), ('CENTER', "Center", ""), ('RIGHT', "Right", "")])
  v_align: bpy.props.EnumProperty(name = "Vertical Alignment", default='TOP', items=[('NONE', "None", ""), ('TOP', "Top", ""), ('CENTER', "Center", ""), ('BOTTOM', "Bottom", "")])
  scale: bpy.props.EnumProperty(name = "Scale", items=[('NONE', "None", ""), ('FIT_X', "Fit X", ""), ('FIT_Y', "Fit Y", ""), ('FIT_BOTH', "Fit Both", ""), ('SET_X', "Set X", ""), ('SET_Y', "Set Y", ""), ('SET_XY', "Set XY", "")])  
  size_x: bpy.props.FloatProperty(name = "Size X", default = 1.0)
  size_y: bpy.props.FloatProperty(name = "Size Y", default = 1.0)

# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////
class IMAGE_OP_Ultimate_Trim_Align(bpy.types.Operator):
    """Aligns selected UV Island(s) to given trim index"""
    bl_label = "Align Trim"
    bl_idname = "uv.trim_align"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH')
        
    def execute(self, context):
        props = context.scene.ut_uv_props

        UltimateTrimAlign(props)
        
        return {'FINISHED'}

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////// 
class IMAGE_OP_Ultimate_Edge_Align(bpy.types.Operator):
    """Aligns selected UV Island(s) to given edge index"""
    bl_label = "Align Edge"
    bl_idname = "uv.edge_align"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH')
        
    def execute(self, context):
        props = context.scene.ut_uv_props

        UltimateEdgeAlign(props)
        
        return {'FINISHED'}

# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////
class IMAGE_PT_Ultimate_Trim_UV(bpy.types.Panel):
    bl_label = "Ultimate Trim UV"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Ultimate Trim UV"
    
    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return sima.show_uvedit and \
            not context.scene.tool_settings.use_uv_select_sync

    def draw(self, context):
        props = context.scene.ut_uv_props
        layout = self.layout
        
        layout.prop(props, "trim_set", text="Trim Set")
        layout.prop(props, "trim_res", text="Trim Resolution")
        layout.prop(props, "uv_padding", text="UV Padding")
        layout.prop(props, "trim_index", text="Trim Index")
        layout.prop(props, "trim_variants", text="Variants")
        layout.prop(props, "h_align", text="H Align")
        layout.prop(props, "v_align", text="V Align")
        layout.prop(props, "scale", text="Scale")
        layout.prop(props, "size_x", text="Size X")
        layout.prop(props, "size_y", text="Size Y")
        layout.operator("uv.trim_align")
        layout.operator("uv.edge_align")

classes = {
  UltimateTrimUVProps,
  IMAGE_OP_Ultimate_Trim_Align,
  IMAGE_OP_Ultimate_Edge_Align,
  IMAGE_PT_Ultimate_Trim_UV
}

def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.ut_uv_props = bpy.props.PointerProperty(type=UltimateTrimUVProps)
    AdjustTrimDefs()

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    
    del bpy.types.Scene.ut_uv_props
