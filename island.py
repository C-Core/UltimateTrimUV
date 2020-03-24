"""The Island module."""

import math
import os
import sys

import mathutils

from . import geometry, global_def, utils

class Island:
    """Create Island from a set() of faces.

    :param island: a set() of face indexes.
    :type island: set().
    """

    def __init__(self, island):
        self.faceList = island

    def __iter__(self):
        """Iterate throught all face faces forming the island."""
        for i in self.faceList:
            yield i

    def __len__(self):
        """Return the number of faces of this island."""
        return len(self.faceList)

    def __str__(self):
        return str(self.faceList)

    def __repr__(self):
        return repr(self.faceList)

    def __eq__(self, other):
        """Compare two island."""
        return self.faceList == other

# properties
    def BBox(self):
        """Return the bounding box of the island.

        :return: a Rectangle rappresenting the bounding box of the island.
        :rtype: :class:`.Rectangle`
        """
        minX = minY = 1000
        maxX = maxY = -1000
        for face_id in self.faceList:
            face = global_def.bm.faces[face_id]
            for loop in face.loops:
                u, v = loop[global_def.uvlayer].uv
                minX = min(u, minX)
                minY = min(v, minY)
                maxX = max(u, maxX)
                maxY = max(v, maxY)

        return geometry.Rectangle(mathutils.Vector((minX, minY)),
                                  mathutils.Vector((maxX, maxY)))

    def angle(self):
        """Return the island angle.

        :return: the angle of the island in radians.
        :rtype: float
        """
        uvList = []
        for face_id in self.faceList:
            face = global_def.bm.faces[face_id]
            for loop in face.loops:
                uv = loop[global_def.bm.loops.layers.uv.active].uv
                uvList.append(uv)

        angle = mathutils.geometry.box_fit_2d(uvList)
        return angle

    def size(self):
        """Return the island size.

        :return: the size of the island(bounding box).
        :rtype: :class:`.Size`
        """
        bbox = self.BBox()
        sizeX = bbox.right() - bbox.left()
        sizeY = bbox.top() - bbox.bottom()

        return geometry.Size(sizeX, sizeY)

# Transformation
    def move(self, vector):
        """Move the island by vector.

        Move the island by 'vector', by adding 'vector' to the curretnt uv
        coords.

        :param vector: the vector to add.
        :rtype: :class:`mathutils.Vector`
        """
        for face_id in self.faceList:
            face = global_def.bm.faces[face_id]
            for loop in face.loops:
                loop[global_def.bm.loops.layers.uv.active].uv += vector

    def rotate(self, angle):
        """Rotate the island on it's center by 'angle(radians)'.

        :param angle: the angle(radians) of rotation.
        :rtype: float
        """
        center = self.BBox().center()

        for face_id in self.faceList:
            face = global_def.bm.faces[face_id]
            for loop in face.loops:
                uv_act = global_def.bm.loops.layers.uv.active
                x, y = loop[uv_act].uv
                xt = x - center.x
                yt = y - center.y
                xr = (xt * math.cos(angle)) - (yt * math.sin(angle))
                yr = (xt * math.sin(angle)) + (yt * math.cos(angle))
                # loop[global_def.bm.loops.layers.uv.active].uv = trans
                loop[global_def.bm.loops.layers.uv.active].uv.x = xr + center.x
                loop[global_def.bm.loops.layers.uv.active].uv.y = yr + center.y

    def scale(self, scaleX, scaleY):
        """Scale the island by 'scaleX, scaleY'.

        :param scaleX: x scale factor.
        :type scaleX: float
        :param scaleY: y scale factor
        :type scaleY: float
        """
        center = self.BBox().center()
        for face_id in self.faceList:
            face = global_def.bm.faces[face_id]
            for loop in face.loops:
                x = loop[global_def.bm.loops.layers.uv.active].uv.x
                y = loop[global_def.bm.loops.layers.uv.active].uv.y
                xt = x - center.x
                yt = y - center.y
                xs = xt * scaleX
                ys = yt * scaleY
                loop[global_def.bm.loops.layers.uv.active].uv.x = xs + center.x
                loop[global_def.bm.loops.layers.uv.active].uv.y = ys + center.y
