"""
Renderable components
"""

import pyglet
from pyglet.gl import *
from app.ObjLoader import ObjLoader


class RenderableGroup(pyglet.graphics.Group):
    batch = pyglet.graphics.Batch()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        return

    @staticmethod
    def draw():
        RenderableGroup.batch.draw()


class TexturedObject(RenderableGroup):
    def __init__(self, shader, mesh, texture, parent=None):
        super().__init__(parent=parent)
        self.shader = shader
        self.time = 0.0  # tempraty time
        self.mesh = mesh
        self.texture = texture

        num_verts = len(mesh.model_vertices) // 3
        self.verts = self.batch.add(num_verts, GL_TRIANGLES, self, ('v3f/static', mesh.model_vertices),
                                                                   ('t3f/static', mesh.model_textures))

    @classmethod
    def from_file(cls, shader, model_fn, tex_fn, parent=None):
        mesh = ObjLoader()
        mesh.load_model(model_fn)
        texture = pyglet.image.load(tex_fn).texture
        #texture = pyglet.resource.image(tex_fn, False)
        return cls(shader, mesh, texture, parent)

    def set_state(self):
        glBindTexture(self.texture.target, self.texture.id)


class Primitive2D(RenderableGroup):
    def __init__(self, shader, vertices, atype=GL_TRIANGLES, parent=None, clrs=(1.0, 1.0, 1.0, 1.0)):
        super().__init__(parent=parent)
        self.time = 0.0
        self.shader = shader
        self.dirty = True
        self._color = []

        num_verts = int(len(vertices) / 2)
        if len(clrs) == 4:
            self._color = clrs * num_verts
        else:
            self._color = clrs

        self.verts = []
        self.verts.append(self.batch.add(num_verts, atype, self,
                                    ('v2f/static', vertices),
                                    ('c4f/static', self._color))
                          )

    def set_state(self):
        self.shader.uniforms.coloring = 1
        #self.shader.uniforms.time = self.time

    def unset_state(self):
        self.shader.uniforms.coloring = 0

    def add_lines(self, vertices, clrs=(1.0, 1.0, 1.0, 1.0)):
        num_verts = int(len(vertices) / 2)
        if len(clrs) == 4:
            self._color = clrs * num_verts
        else:
            self._color = clrs

        self.verts.append(self.batch.add(num_verts, GL_LINES, self,
                                    ('v2f/static', vertices),
                                    ('c4f/static', self._color))
                          )
