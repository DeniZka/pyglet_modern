"""
Renderable components
"""

import pyglet
from pyglet.gl import *
from app.ObjLoader import ObjLoader


class RenderableGroup:
    batch = pyglet.graphics.Batch()

    def __init__(self, group=None):
        self.group = group

    @staticmethod
    def draw():
        RenderableGroup.batch.draw()


class TexturedObject(RenderableGroup):
    def __init__(self, shader, mesh, group=None):
        super().__init__(group=group)
        self.shader = shader
        self.time = 0.0  # tempraty time
        self.mesh = mesh

        num_verts = len(mesh.model_vertices) // 3
        self.verts = self.batch.add(num_verts, GL_TRIANGLES, self.group,
                                    ('v3f/static', mesh.model_vertices),
                                    ('t3f/static', mesh.model_textures)
                                    )

    def __del__(self):
        for v in self.verts:
            v = None

    @classmethod
    def from_file(cls, shader, model_fn, group=None):
        mesh = ObjLoader()
        mesh.load_model(model_fn)
        return cls(shader, mesh, group)


class Primitive2D(RenderableGroup):
    def __init__(self, shader, vertices, atype=GL_TRIANGLES, group=None, clrs=(1.0, 1.0, 1.0, 1.0)):
        super().__init__(group=group)
        self.time = 0.0
        self.shader = shader
        self.dirty = True
        self._color = []
        self.verts = []
        self.add_lines(vertices, clrs, atype)

    def add_lines(self, vertices, clrs=(1.0, 1.0, 1.0, 1.0), atype=GL_LINES):
        num_verts = int(len(vertices) / 2)
        if len(clrs) == 4:
            self._color = clrs * num_verts
        else:
            self._color = clrs
        verts = self.batch.add(num_verts, atype, self.group,
                       ('v2f/static', vertices),
                       ('c4f/static', self._color))
        self.verts.append(verts)
        return verts
