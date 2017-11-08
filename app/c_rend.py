"""
Renderable components
"""

import pyglet
from pyglet.gl import *
from app.ObjLoader import ObjLoader


class Renderable:
    batch = pyglet.graphics.Batch()

    def __init__(self, group=None):
        self.group = group

    @staticmethod
    def draw():
        Renderable.batch.draw()


class TexturedObject(Renderable):
    def __init__(self, shader, mesh, group=None):
        super().__init__(group=group)
        self.shader = shader
        self.time = 0.0  # tempraty time
        self.mesh = mesh
        self.verts = []
        self.add_mesh(self.mesh)

    def __del__(self):
        for v in self.verts:
            v = None

    @classmethod
    def from_file(cls, shader, model_fn, group=None):
        mesh = ObjLoader()
        mesh.load_model(model_fn)
        return cls(shader, mesh, group)

    def add_mesh(self, mesh):
        num_verts = len(mesh.model_vertices) // 3
        self.verts.append(
            self.batch.add(
                num_verts, GL_TRIANGLES, self.group,
                ('v3f/dynamic', mesh.model_vertices),
                ('t3f/dynamic', mesh.model_textures)
            )
        )


class Primitive2D(Renderable):
    def __init__(self, shader, vertices, atype=GL_TRIANGLES, group=None, clrs=(1.0, 1.0, 1.0, 1.0)):
        super().__init__(group=group)
        self.time = 0.0
        self.shader = shader
        self.dirty = True
        self._color = []
        self.verts = []
        self.add_lines(vertices, clrs, atype)

    def __del__(self):
        for v in self.verts:
            v = None

    def add_lines(self, vertices, clrs=(1.0, 1.0, 1.0, 1.0), atype=GL_LINES):
        num_verts = int(len(vertices) / 2)
        if len(clrs) == 4:
            self._color = clrs * num_verts
        else:
            self._color = clrs
        verts = self.batch.add(num_verts, atype, self.group,
                       ('v2f/dynamic', vertices),
                       ('c4f/dynamic', self._color))
        self.verts.append(verts)
        return verts
