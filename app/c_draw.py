from random import randint, triangular

from pyglet.gl import *
from pyrr import matrix44, Matrix44, quaternion

from app.ObjLoader import ObjLoader


class TexturedObject(pyglet.graphics.Group):
    active_program = 0

    def __init__(self, shader, mesh, image):
        super().__init__()
        self.time = 0.0 #tempraty time
        self.ta = 0.0 #tempraty angle
        self._rot = Matrix44.identity()
        self._rotq = quaternion.create()
        self.pos = [0.0, 0.0, 0.0]
        self.scale = [1.0, 1.0, 1.0]
        self.shader = shader
        self.attr_pos = self.shader.attributes["position"]
        self.dirty = True
        self._angle = 0.0

        self.r = 1.0

        self.mesh = mesh
        self.image = image

        #mesh = ObjLoader()
        #mesh.load_model(model_fn)
        num_verts = len(mesh.model_vertices) // 3
        self.verts = main_batch.add(num_verts, GL_TRIANGLES, self, ('v3f', mesh.model_vertices),
                                                                    ('t2f', mesh.model_textures))

        # region texture settings
        self.texture = GLuint(0)
        glGenTextures(1, self.texture)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        # set the texture wrapping
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        # set the texture filtering
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        #image = pyglet.image.load(tex_fn)
        image_data = image.get_data('RGB', image.pitch)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, image.width, image.height, 0, GL_RGB, GL_UNSIGNED_BYTE, image_data)
        # endregion

    @classmethod
    def from_file(cls, shader, model_fn, tex_fn):
        mesh = ObjLoader()
        mesh.load_model(model_fn)
        image = pyglet.image.load(tex_fn)
        return cls(shader, mesh, image)

    @property
    def angle(self):
        return self._rot

    @angle.setter
    def angle(self, val):
        if type(val) is float:
            self._rot = Matrix44.from_y_rotation(val)
            self._rotq = quaternion.create_from_y_rotation(val)
        else:
            self._rot = matrix44.create_from_quaternion(val)
            self._rotq = val
        self.dirty = True

    def rotate_local(self, angle, axis='z'):
        if axis == 'z':
            q = quaternion.create_from_z_rotation(angle)
        if axis == 'y':
            q = quaternion.create_from_y_rotation(angle)
        if axis == 'x':
            q = quaternion.create_from_x_rotation(angle)
        self._rotq = q * self._rotq
        self.dirty = True



    def set_state(self):
        #glUseProgram(self.shader.id)
        self.shader.use()
        # vertices
        self.shader.attributes.position.enable()
        self.shader.attributes.position.point_to(self.verts.vertices, GL_FLOAT, 3)

        # vertices uniforms
        if self.dirty:
            trans = matrix44.create_from_translation(self.pos)
            rot = matrix44.create_from_y_rotation(self._angle)
            #rot = matrix44.create_from_quaternion(self._rotq) #inverse_of_quaternion(self._rotq)
            scale = matrix44.create_from_scale(self.scale)
            self.shader.uniforms.translation = trans
            self.shader.uniforms.rotation = rot
            self.shader.uniforms.scale = scale
            self.dirty = False
        if projection_dirty:
            self.shader.uniforms.proj = projection
            self.shader.uniforms.view = view

        # textures
        self.shader.attributes.textureCoords.enable()
        self.shader.attributes.textureCoords.point_to(self.verts.tex_coords, GL_FLOAT, 2)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)

    def unset_state(self):
        #glUseProgram(0)
        glDisable(GL_TEXTURE_2D)
        self.shader.attributes.position.disable()
        self.shader.attributes.textureCoords.disable()

    def update(self, dt):
        #self.ta += 0.1 * dt
        self.rotate_local(dt)
        self._angle += dt
        #self.r += dt
        #self.scale[0] = math.sin(self.r) + 2
        self.dirty = True


class Poly2D(pyglet.graphics.Group):
    def __init__(self, shader, vertices, type=GL_TRIANGLES):
        super().__init__()
        self.time = 0.0
        self.shader = shader
        self.dirty = True
        self._color = []

        self._trfm = Matrix44.identity()
        self._rot = Matrix44.identity()
        self._scale = Matrix44.identity()
        self._pos = Matrix44.identity()


        num_verts = int(len(vertices) / 2)
        for i in range(num_verts):
            for j in range(3):
                self._color.append(triangular(0.0, 1.0))
            self._color.append(triangular(0.7, 1.0))

        self.verts = batch2d.add(num_verts, type, self, ('v2f', vertices), ('c4f', self._color))

    @property
    def color(self):
        return self.verts.colors

    @color.setter
    def color(self, val):
        self.verts.colors = val

    @property
    def angle(self):
        return self._rot

    @angle.setter
    def angle(self, val):
        if type(val) is float:
            self._rot = Matrix44.from_z_rotation(val)
        else:
            self._rot = val
        self.dirty = True

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, val):
        self._pos = Matrix44.from_translation(val+[0.0])
        self.dirty = True

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, val):
        self._scale = Matrix44.from_scale(val+[1.0])
        self.dirty = True


    def set_state(self):
        self.shader.use()

        # vertices
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.verts.vertices)

        # vertices uniforms
        if self.dirty:
            self._trfm = self._pos * self._rot * self._scale
            self.shader.uniforms.trfm = self._trfm
        if projection_dirty:
            self.shader.uniforms.proj = projection
            self.shader.uniforms.view = view


        #texture uniform
        self.shader.uniforms.time = self.time

        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 0, self.verts.colors)
        glEnableVertexAttribArray(1)

    def unset_state(self):
        #glUseProgram(0)
        glDisableVertexAttribArray(0)
        glDisableVertexAttribArray(1)
        self.dirty = False

    def update(self, dt):
        self.time += dt

class LabelGrp(pyglet.graphics.Group):
    def __init__(self):
        super().__init__()

    def set_state(self):
        return

    def unset_state(self):
        return