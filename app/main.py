from random import randint, triangular

from pyglet.gl import *
from pyrr import matrix44, Matrix44, quaternion

from app.ObjLoader import ObjLoader
from app import pyshaders
from ctypes import c_bool

import esper
import time

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
active_shader_pid = 0

active_shader = None


class CameraGrp(pyglet.graphics.Group):
    """
    Group that enable camera
    transformation to uniforms
    """
    def __init__(self, shader, parent=None):
        super().__init__(parent=parent)
        self.shader = shader
        self.projection = matrix44.create_orthogonal_projection(
            -1280 / 2 / zoom, 1280 / 2 / zoom,
            -720 / 2 / zoom, 720 / 2 / zoom,
            -100, 100
        )
        self.view = matrix44.create_look_at(
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 0.0),
            (0.0, 1.0, 0.1)
        )

    def set_state(self):
        self.shader.uniforms.proj = projection  # self.projection
        self.shader.uniforms.view = view  # self.view

    def unset_state(self):
        # TODO reset to default view
        pass

    def zoom(self):
        # TODO zoom and another features
        pass


class ShaderGrp(pyglet.graphics.Group):
    """
    Group for shader accessors
    """
    active_shader_pid = 0

    def __init__(self, shader, parent=None):
        super().__init__(parent=parent)
        self.shader = shader
        self.bak_shader_pid = 0

    def set_state(self):
        """
        set this shader
        """
        self.shader.use()
        self.bak_shader_pid = self.active_shader_pid
        self.active_shader_pid = self.shader.pid

    def unset_state(self):
        """
        return prevous shader
        """
        glUseProgram(self.bak_shader_pid)
        self.active_shader_pid = self.bak_shader_pid


class ShaderSwitchColoringGrp(pyglet.graphics.Group):
    def __init__(self, shader, parent=None):
        super().__init__(parent=parent)
        self.shader = shader

    def set_state(self):
        #FIXME test this or use - ctypes
        self.shader.uniforms.coloring = 1

    def unset_state(self):
        self.shader.uniforms.coloring = 0


class DepthTestGrp(pyglet.graphics.OrderedGroup):
    """
    Group for 3D objects
    Seems must be first ordered to draw blend futurer
    """
    def __init__(self, order, parent=None):
        super().__init__(order, parent=parent)

    def set_state(self):
        glEnable(GL_DEPTH_TEST)

    def unset_state(self):
        glDisable(GL_DEPTH_TEST)


class BlendGrp(pyglet.graphics.OrderedGroup):
    """
    Group for 2D objects
    Must have lowest order to blend last
    """
    def __init__(self, order, parent=None):
        super().__init__(order, parent=parent)

    def set_state(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self):
        glDisable(GL_BLEND)

class EnableTextureGrp(pyglet.graphics.Group):
    """
    Texture enabling group
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def set_state(self):
        glEnable(GL_TEXTURE_2D)

    def unset_state(self):
        glDisable(GL_TEXTURE_2D)


class AbstractTransform(pyglet.graphics.Group):
    """
    Unifrom transfromation access group
    """
    def __init__(self, transform_matrix=None, parent=None):
        super().__init__(parent=parent)
        self._tr = transform_matrix
        if self._tr is None:
            self._tr = Matrix44.identity()
        self._gtr = self._tr  # global transform include parent transformations
        if self.parent and self.parent.__class__ is AbstractTransform:
            self._gtr = self.parent.transform * self._tr
        self.dirty = False  # global transform calculated

    @property
    def local_transform(self):
        return self._tr

    @property
    def transform(self):
        """

        :return: Total transform matrix
        """
        if self.parent:
            if self.dirty:
                self._gtr = self.parent.transform * self._tr
        else:
            if self.dirty:
                self._gtr = self._tr
        return self._gtr

    @transform.setter
    def transform(self, val):
        self._tr = val
        self.dirty = True

    def set_state(self):
        active_shader.uniforms.trfm = self._gtr


class TexturedObject(AbstractTransform):
    active_program = 0

    def __init__(self, shader, mesh, image, parent=None):
        super().__init__(parent=parent)
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
    def from_file(cls, shader, model_fn, tex_fn, parent=None):
        mesh = ObjLoader()
        mesh.load_model(model_fn)
        image = pyglet.image.load(tex_fn)
        #image = pyglet.resource.image(tex_fn, False).image_data TODO:use single texture
        return cls(shader, mesh, image, parent)

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
        global active_shader_pid
        if self.shader.pid != active_shader_pid:
            self.shader.use()
            active_shader_pid = self.shader.pid
        # vertices
        self.shader.attributes.position.enable()
        self.shader.attributes.position.point_to(self.verts.vertices, GL_FLOAT, 3)

        # vertices uniforms
    #if self.dirty:
        trfm = matrix44.create_identity()
        trans = matrix44.create_from_translation(self.pos)
        rot = matrix44.create_from_y_rotation(self._angle)
        #rot = matrix44.create_from_quaternion(self._rotq) #inverse_of_quaternion(self._rotq)
        scale = matrix44.create_from_scale(self.scale)
        self.shader.uniforms.trfm = trfm
        self.shader.uniforms.translation = trans
        self.shader.uniforms.rotation = rot
        self.shader.uniforms.scale = scale
        self.dirty = False

        # textures
        self.shader.uniforms.coloring = 0
        self.shader.attributes.textureCoords.enable()
        self.shader.attributes.textureCoords.point_to(self.verts.tex_coords, GL_FLOAT, 2)

        glBindTexture(GL_TEXTURE_2D, self.texture)

    def unset_state(self):
        self.shader.attributes.position.disable()
        self.shader.attributes.textureCoords.disable()



class Poly2D(AbstractTransform):
    def __init__(self, shader, vertices, type=GL_TRIANGLES, parent=None):
        super().__init__(parent=parent)
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

        self.verts = main_batch.add(num_verts, type, self, ('v2f', vertices), ('c4f', self._color))

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
        global active_shader_pid
        if self.shader.pid != active_shader_pid:
            self.shader.use()
            active_shader_pid = self.shader.pid

        # vertices
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, self.verts.vertices)

        # vertices uniforms
        if self.dirty:
            self._trfm = self._pos * self._rot * self._scale
            self.shader.uniforms.trfm = self._trfm

        #texture uniform
        self.shader.uniforms.coloring = 1
        self.shader.uniforms.time = self.time

        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 0, self.verts.colors)
        glEnableVertexAttribArray(1)

    def unset_state(self):
        #glUseProgram(0)
        glDisableVertexAttribArray(0)
        glDisableVertexAttribArray(1)
        self.dirty = False


class MoveProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self, dt):
        for e, to in self.world.get_component(TexturedObject):
            # self.ta += 0.1 * dt
            to.rotate_local(dt)
            to._angle += dt
            # self.r += dt
            # self.scale[0] = math.sin(self.r) + 2
            to.dirty = True

        for e, poly in self.world.get_component(Poly2D):
            poly.time += dt


class WindowProcessor(pyglet.window.Window, esper.Processor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_minimum_size(400, 300)
        glClearColor(0.2, 0.2, 0.2, 1.0)
        self.fps_display = pyglet.clock.ClockDisplay()

        self.label = pyglet.text.Label('Hello, world',
                              font_size=36,
                              x=10, y=100)

    def on_draw(self):
        self.clear()
        #ts = time.time()
        # draw 3D Modern OpenGL
        main_batch.draw()

        #print(1/(time.time() - ts))

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

    def process(self, dt):
        pass


def run(args=None):
    world = esper.World()
    window = WindowProcessor(1280, 720, "My Pyglet Window", resizable=True)
    world.add_processor(window)
    world.add_processor(MoveProcessor())

    # FACTORY
    c_shader = pyshaders.from_files_names("shaders/vert3d.glsl", "shaders/frag3d.glsl")
    sgrp = ShaderGrp(c_shader)

    camera_grp = CameraGrp(c_shader, sgrp)
    depth_grp = DepthTestGrp(0, camera_grp)
    texture_grp = EnableTextureGrp(depth_grp)
    blend_grp = BlendGrp(1, camera_grp)

    p = Poly2D(c_shader, tri, parent=blend_grp)
    # p.pos = [10.0, 0.0]
    p.angle = 1.0
    p.scale = [1.0, 2.0]
    p.color = [1.0, 0.0, 0.0, 1.0,
               0.0, 1.0, 0.0, 1.0,
               0.0, 0.0, 1.0, 1.0]
    world.create_entity(p)

    xmas = TexturedObject.from_file(c_shader, "models/cube.obj", 'models/cube.jpg', texture_grp)
    xmas.pos = [10.0, 10.0, 0.0]
    world.create_entity(xmas)

    std = TexturedObject.from_file(c_shader, "models/xmas_tree.obj", 'models/xmas_texture.jpg', texture_grp)
    std.pos = [10.0, 0.0, 0.0]
    world.create_entity(std)

    for i in range(20):
        cb = TexturedObject(c_shader, std.mesh, std.image, depth_grp)
        cb.pos = [randint(-10, 10), randint(-10, 10), randint(-10, 10)]
        world.create_entity(cb)
        v = (triangular(), triangular(), triangular())
        # v = (0.0, 1.0, 1.0)
        a = triangular()  # math.pi/2
        q = quaternion.create_from_axis_rotation(v, a)
        # m = matrix44.create_from_quaternion(q)#inverse_of_quaternion(q)
        # cb.angle = randint(-10, 10) / 10
        cb.angle = q
        cb._angle = randint(-10, 10)

    # self.monkey = Monkey(m_shader)
    monkey = TexturedObject.from_file(c_shader, 'models/monkey.obj', 'models/monkey.jpg', texture_grp)
    world.create_entity(monkey)

    # END FACTORY

    #window = MyWindow(1280, 720, "My Pyglet Window", resizable=True)
    pyglet.clock.schedule_interval(world.process, 1/60.0)
    pyglet.app.run()
    return