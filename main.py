from pyglet.gl import *
import ShaderLoader
from ObjLoader import ObjLoader
from pyrr import Vector3, matrix44, Matrix44, quaternion
import time
import numpy
from ctypes import byref, c_char, cast, POINTER
from random import randint, triangular
import math
import numpy as np
import ctypes

main_batch = pyglet.graphics.Batch()
batch2d = pyglet.graphics.Batch()
zoom = 50

projection = matrix44.create_orthogonal_projection(
    -1280 / 2 / zoom, 1280 / 2 / zoom,
    -720 / 2 / zoom, 720 / 2 / zoom,
    -100, 100
)
view = matrix44.create_look_at(
    (0.0, 0.0, 1.0),
    (0.0, 0.0, 0.0),
    (0.0, 1.0, 0.1)
)
projection_dirty = True

tri = [
    1.0*10, 0.0*10,
    0.0*10, 1.0*10,
    -0.0*10, 0.0*10
]


class GLGetObject(object):
    """
        Descriptor that wraps glGet* function
    """
    __slots__ = ['pname']
    buffer = GLint(0)

    def __init__(self, pname): self.pname = pname

    def __set__(self): raise AttributeError('Attribute is not writable')

    def __delete__(self): raise AttributeError('Attribute cannot be deleted')


class GetProgramObject(GLGetObject):
    __slots__ = []

    def __get__(self, instance, cls):
        glGetProgramiv(instance.id, self.pname, byref(self.buffer))
        return self.buffer.value


class Shader:
    delete_status = GetProgramObject(GL_DELETE_STATUS)
    log_length = GetProgramObject(GL_INFO_LOG_LENGTH)
    link_status = GetProgramObject(GL_LINK_STATUS)
    validate_status = GetProgramObject(GL_VALIDATE_STATUS)
    shaders_count = GetProgramObject(GL_ATTACHED_SHADERS)
    attributes_count = GetProgramObject(GL_ACTIVE_ATTRIBUTES)
    uniforms_count = GetProgramObject(GL_ACTIVE_UNIFORMS)
    max_attribute_length = GetProgramObject(GL_ACTIVE_ATTRIBUTE_MAX_LENGTH)
    max_uniform_length = GetProgramObject(GL_ACTIVE_UNIFORM_MAX_LENGTH)

    def __init__(self, vert_fn, frag_fn):
        self.uniforms = {}
        self.id = ShaderLoader.compile_shader(vert_fn, frag_fn)

        #get all uniforms
        name_buf = (c_char*self.max_attribute_length)()
        name_buf_ptr = cast(name_buf, POINTER(c_char))
        type_buf = GLenum(0)
        name_buf_length = GLint(0)
        buf_size = GLint(0)

        for i in range(self.uniforms_count):
            glGetActiveUniform(self.id, i, self.max_uniform_length, byref(name_buf_length), byref(buf_size), byref(type_buf), name_buf_ptr)

            # type = type_buf.value
            name_len = name_buf_length.value
            name = bytes(name_buf)[0:name_len].decode('UTF-8')
            # size = buf_size.value
            self.uniforms[name] = (glGetUniformLocation(self.id, name_buf_ptr), type_buf.value)

        glUseProgram(self.id)

        self.set_mat("proj", projection)
        self.set_mat("view", view)
        glUseProgram(0)

    def set_mat(self, uniform, mat):
        loc, u_type = self.uniforms[uniform]
        m = mat.flatten().astype("float32")
        c_m = numpy.ctypeslib.as_ctypes(m)
        if u_type == GL_FLOAT_MAT3:
            glUniformMatrix3fv(loc, 1, GL_FALSE, c_m)
        elif u_type == GL_FLOAT_MAT4:
            glUniformMatrix4fv(loc, 1, GL_FALSE, c_m)
        #TODO: other types
        else:
            print("Uniform not found")




class TexturedObject(pyglet.graphics.Group):
    active_program = 0

    def __init__(self, shader, mesh, image):
        super().__init__()
        self.ta = 0.0 #tempraty angle
        self._rot = Matrix44.identity()
        self._rotq = quaternion.create()
        self.pos = [0.0, 0.0, 0.0]
        self.scale = [1.0, 1.0, 1.0]
        self.shader = shader
        self.dirty = True

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
        glUseProgram(self.shader.id)
        # vertices
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, self.verts.vertices)

        # vertices uniforms
        if self.dirty:
            trans = matrix44.create_from_translation(self.pos)
            #rot = matrix44.create_from_y_rotation(self.angle)
            rot = matrix44.create_from_quaternion(self._rotq) #inverse_of_quaternion(self._rotq)
            scale = matrix44.create_from_scale(self.scale)
            self.shader.set_mat("translation", trans)
            self.shader.set_mat("rotation", rot)
            self.shader.set_mat("scale", scale)
            self.dirty = False
        if projection_dirty:
            self.shader.set_mat("proj", projection)
            self.shader.set_mat("view", view)

        # textures
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, self.verts.tex_coords)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)

    def unset_state(self):
        #glUseProgram(0)
        glDisable(GL_TEXTURE_2D)
        glDisableVertexAttribArray(0)
        glDisableVertexAttribArray(1)

    def update(self, dt):
        #self.ta += 0.1 * dt
        self.rotate_local(dt)
        #self.r += dt
        #self.scale[0] = math.sin(self.r) + 2
        self.dirty = True


class Poly2D(pyglet.graphics.Group):
    def __init__(self, shader, vertices, type=GL_TRIANGLES):
        super().__init__()
        self.shader = shader
        self.dirty = True
        self.color = []

        self._trfm = Matrix44.identity()
        self._rot = Matrix44.identity()
        self._scale = Matrix44.identity()
        self._pos = Matrix44.identity()


        num_verts = int(len(vertices) / 2)
        for i in range(num_verts):
            for j in range(3):
                self.color.append(triangular(0.0, 1.0))
            self.color.append(triangular(0.7, 1.0))

        self.verts = batch2d.add(num_verts, type, self, ('v2f', vertices), ('c4f', self.color))

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
        glUseProgram(self.shader.id)

        # vertices
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.verts.vertices)

        # vertices uniforms
        if self.dirty:
            self._trfm = self._pos * self._rot * self._scale
            self.shader.set_mat("trfm", self._trfm)
        if projection_dirty:
            self.shader.set_mat("proj", projection)
            self.shader.set_mat("view", view)

        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 0, self.verts.colors)
        glEnableVertexAttribArray(1)

    def unset_state(self):
        #glUseProgram(0)
        glDisableVertexAttribArray(0)
        glDisableVertexAttribArray(1)
        self.dirty = False

class LabelGrp(pyglet.graphics.Group):
    def __init__(self):
        super().__init__()

    def set_state(self):
        return

    def unset_state(self):
        return


class MyWindow(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_minimum_size(400, 300)
        glClearColor(0.2, 0.2, 0.2, 1.0)
        self.cube = []
        ps = Shader("shaders/vert2d.glsl", "shaders/frag2d.glsl")
        p = Poly2D(ps, tri)
        p.pos = [10.0, 0.0]
        p.angle = 1.0
        p.scale = [1.0, 2.0]
        c_shader = Shader("shaders/vert3d.glsl", "shaders/frag3d.glsl")
        self.xmas = TexturedObject.from_file(c_shader, "models/cube.obj", 'models/cube.jpg')
        self.xmas.pos = [10.0, 10.0, 0.0]

        c_shader = Shader("shaders/vert3d.glsl", "shaders/frag3d.glsl")
        std = TexturedObject.from_file(c_shader, "models/xmas_tree.obj", 'models/xmas_texture.jpg')
        std.pos = [10.0, 0.0, 0.0]
        for i in range(100):
            c_shader = Shader("shaders/vert3d.glsl", "shaders/frag3d.glsl")
            cb = TexturedObject(c_shader, std.mesh, std.image)
            cb.pos = [randint(-10, 10), randint(-10, 10), randint(-10, 10)]
            v = (triangular(), triangular(), triangular())
            #v = (0.0, 1.0, 1.0)
            a = triangular() #math.pi/2
            q = quaternion.create_from_axis_rotation(v, a)
            #m = matrix44.create_from_quaternion(q)#inverse_of_quaternion(q)
            #cb.angle = randint(-10, 10) / 10
            cb.angle = q
            self.cube.append(cb)
        m_shader = Shader("shaders/vert3d.glsl", "shaders/frag3d.glsl")
        #self.monkey = Monkey(m_shader)
        self.monkey = TexturedObject.from_file(m_shader, 'models/monkey.obj', 'models/monkey.jpg')
        self.fps_display = pyglet.clock.ClockDisplay()
        self.label = pyglet.text.Label('Hello, world',
                              font_size=36,
                              x=10, y=100)

    def on_draw(self):
        self.clear()

        # draw 3D Modern OpenGL
        glEnable(GL_DEPTH_TEST)
        main_batch.draw()
        glDisable(GL_DEPTH_TEST)

        # draw 2D
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Modern OpenGL 2D drawning
        batch2d.draw()
        glUseProgram(0)

        # reset projection is dirty
        global projection_dirty
        if projection_dirty:
            projection_dirty = False

        # Legacy OpenGL
        glMatrixMode(gl.GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)
        glMatrixMode(gl.GL_MODELVIEW)

        self.fps_display.draw()
        self.label.draw()

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        self.calc_projection()

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        global zoom
        if scroll_y > 0:
            zoom += zoom * 0.1
        if scroll_y < 0:
            zoom -= zoom * 0.1
        self.calc_projection()

    def update(self, dt):
        self.monkey.update(dt)
        for cb in self.cube:
            cb.update(dt)
        self.xmas.update(dt)
        #for i in range(10):
        #    self.cube[i].update(dt)


    # self methods
    def calc_projection(self):
        global projection, view, projection_dirty
        projection = matrix44.create_orthogonal_projection(
            -self.width / 2 / zoom, self.width / 2 / zoom,
            -self.height / 2 / zoom, self.height / 2 / zoom,
            -100, 100
        )
        #projection = matrix44.create_perspective_projection_matrix(
        #    45.0,
        #    self.width / self.height,
        #    0.1,
        #    100.0
        #)
        view = matrix44.create_look_at(
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0)
        )
        projection_dirty = True


if __name__ == "__main__":
    window = MyWindow(1280, 720, "My Pyglet Window", resizable=True)
    pyglet.clock.schedule_interval(window.update, 1/60.0)
    pyglet.app.run()
