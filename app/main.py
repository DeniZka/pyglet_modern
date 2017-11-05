from random import randint, triangular

from pyglet.gl import *
from pyrr import matrix44, Matrix44

from app.ObjLoader import ObjLoader
from app import pyshaders
from ctypes import c_bool

import esper
import time
import math

main_batch = pyglet.graphics.Batch()
batch2d = pyglet.graphics.Batch()
zoom = 50

tri = [
    1.0*10, 0.0*10,
    0.0*10, 1.0*10,
    -0.0*10, 0.0*10
]
active_shader_pid = 0

active_shader = None
label = None


class CameraGrp(pyglet.graphics.OrderedGroup):
    """
    Group that enable camera
    transformation to uniforms
    """
    def __init__(self, order, shader, parent=None, x=0.0, y=0.0):
        super().__init__(order, parent=parent)
        self.x, self.y = x, y
        self.width = 1280
        self.height = 720
        self._zoom = 50.0
        self.shader = shader
        self.projection = None
        self.view = None
        self.default_proj = None
        self.default_view = matrix44.create_identity()
        self.up_x = 0.0
        self.up_y = 1.0
        self._angle = 0.0
        self.calc_projection()

    def set_state(self):
        self.shader.uniforms.proj = self.projection
        self.shader.uniforms.view = self.view

    def unset_state(self):
        self.shader.uniforms.proj = self.default_proj
        self.shader.uniforms.view = self.default_view

    def calc_projection(self):
        self.projection = matrix44.create_orthogonal_projection(
            -self.width / 2 / self._zoom, self.width / 2 / self._zoom,
            -self.height / 2 / self._zoom, self.height / 2 / self._zoom,
            -100, 100
        )
        self.default_proj = matrix44.create_orthogonal_projection(
            0, self.width, 0, self.height, -1, 1
        )
        #projection = matrix44.create_perspective_projection_matrix(
        #    45.0, self.width / self.height,0.1,100.0)
        self.view = matrix44.create_look_at(
            (self.x, self.y, 1.0),
            (self.x, self.y, 0.0),
            (self.up_x, self.up_y, 0.0)
        )

    def resize(self, width, height):
        self.width = width
        self.height = height
        self.calc_projection()

    def zoom(self, val):
        self._zoom += self._zoom * val
        self.calc_projection()

    def drag(self, dx , dy):
        zdx = dx / self._zoom
        zdy = dy / self._zoom
        #sv.rotate(self._angle)
        self.x -= zdx
        self.y -= zdy
        self.calc_projection()

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, val):
        self._angle = val
        prex = self.up_x*math.cos(val) - self.up_y*math.sin(val)
        self.up_y = self.up_x*math.sin(val) - self.up_y*math.cos(val)
        self.up_x = prex


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
        if self.active_shader_pid != self.shader.pid:
            self.shader.use()
            self.bak_shader_pid = self.active_shader_pid
            self.active_shader_pid = self.shader.pid

    def unset_state(self):
        """
        return prevous shader if need
        """
        #glUseProgram(self.bak_shader_pid)
        #self.active_shader_pid = self.bak_shader_pid
        pass


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


class ColorizeFontGrp(pyglet.graphics.OrderedGroup):
    """
    Group for 2D objects
    Must have lowest order to blend last
    """
    def __init__(self, order, shader, color=(1.0, 1.0, 1.0, 0.0), parent=None):
        super().__init__(order, parent=parent)
        self.shader = shader
        self.color = color

    def set_state(self):
        #self.shader.uniforms.colorize = 1
        #self.shader.uniforms.clr_clr = self.color
        self.shader.uniforms.trfm = matrix44.create_identity()  #Clean transform matrix before draw lables TODO move somewhere

    def unset_state(self):
        #self.shader.uniforms.colorize = 0
        pass


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


class Graphics(pyglet.graphics.Group):
    """
    Simple painted vertices
    """
    def __init__(self, shader, vertex_list, color_list, parent=None):
        super().__init__(parent=parent)
        self.vlist = vertex_list
        self.clist = color_list
        self.shader = shader

    def __del__(self):
        self.vertex_list = None

    @classmethod
    def from_file(cls, shader, model_fn, tex_fn, parent=None):
        mesh = ObjLoader()
        mesh.load_model(model_fn)
        texture = pyglet.image.load(tex_fn).texture
        num_verts = len(mesh.model_vertices) // 3
        verts = main_batch.add(num_verts, GL_TRIANGLES, None, ('v3f/static', mesh.model_vertices),
                                                                   ('t3f/static', mesh.model_textures))
        return cls(shader, mesh, texture, parent)

    def set_state(self):
        self.shader.uniforms.coloring = 1
        #self.shader.uniforms.time = self.time

    def unset_state(self):
        self.shader.uniforms.coloring = 0


class GraphicsTextured(pyglet.graphics.Group):
    """
    Painted with texture vertices
    """
    def __init__(self, shader, vertex_list, texture, color=(1.0, 1.0, 1.0, 1.0), parent=None):
        super().__init__(parent=parent)
        self.vlist = vertex_list
        self.color = color
        self.texture = texture
        self.shader = shader

    def __del__(self):
        self.vertex_list = None

    def set_state(self):
        glBindTexture(self.texture.target, self.texture.id)


class TransformGrp(pyglet.graphics.Group):
    """
    Unifrom transfromation access group
    """
    def __init__(self, shader, transform_matrix=None, parent_transform=None, parent=None):
        super().__init__(parent=parent)
        self.shader = shader
        self._ptr = parent_transform
        self._tr = transform_matrix
        if self._tr is None:
            self._tr = Matrix44.identity()
        self._gtr = self._tr  # global transform include parent transformations
        if self.parent and self.parent.__class__ is TransformGrp:
            self._gtr = self.parent.transform * self._tr

        self._pos = [0.0, 0.0, 0.0]
        self._tm = Matrix44.from_translation(self._pos)
        self._angle = 0.0
        self._rm = Matrix44.from_z_rotation(self._angle)
        self._scale = [1.0, 1.0, 1.0]
        self._sm = Matrix44.from_scale(self.scale)
        self._trfm = self._tm * self._rm * self._sm
        self.dirty = True  # global transform calculated

    def get_transform(self, glob=True):
        """
        :return: Total transform matrix
        """
        if self.dirty:
            self._trfm = self._tm * self._rm * self._sm
            if self._ptr:
                self._gtr = self._ptr.transform * self._trfm
        if self._ptr and glob:
            return self._gtr
        else:
            return self._trfm

    @property
    def parent_trfm(self):
        return self._ptr

    @parent_trfm.setter
    def parent_trfm(self, val):
        self._ptr = val

    @property
    def local_transform(self):
        return self.get_transform(False)

    @property
    def transform(self):
        return self.get_transform(True)


    @transform.setter
    def transform(self, val):
        self._tr = val
        self.dirty = True

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, val):
        if len(val) == 2:
            self._pos = val+[0.0]
        else:
            self._pos = val
        self._tm = Matrix44.from_translation(self._pos)
        self.dirty = True

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, val):
        self._angle = val
        self._rm = Matrix44.from_z_rotation(self._angle)
        self.dirty = True

    def rotate(self, angle):
        self._angle += angle
        self._rm = Matrix44.from_z_rotation(self._angle)
        self.dirty = True

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, val):
        if len(val) == 2:
            self._scale = val+[1.0]
        else:
            self._scale = val
        self._sm = Matrix44.from_scale(self._scale)
        self.dirty = True

    def set_state(self):
        self.shader.uniforms.trfm = self.transform


class TexturedObject(pyglet.graphics.Group):
    def __init__(self, shader, mesh, texture, parent=None):
        super().__init__(parent=parent)
        self.shader = shader
        self.time = 0.0  # tempraty time
        self.mesh = mesh
        self.texture = texture

        num_verts = len(mesh.model_vertices) // 3
        self.verts = main_batch.add(num_verts, GL_TRIANGLES, self, ('v3f/static', mesh.model_vertices),
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


class Poly2D(pyglet.graphics.Group):
    def __init__(self, shader, vertices, type=GL_TRIANGLES, parent=None, clrs=(1.0, 1.0, 1.0, 1.0)):
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

        self.verts = main_batch.add(num_verts, type, self,
                                    ('v2f/static', vertices),
                                    ('c4f/static', self._color))

    def set_state(self):
        self.shader.uniforms.coloring = 1
        #self.shader.uniforms.time = self.time

    def unset_state(self):
        self.shader.uniforms.coloring = 0


class MoveProcessor(esper.Processor):
    def __init__(self):
        super().__init__()
        self.time = 0.0

    def process(self, dt):
        self.time += dt
        for e, (t, to) in self.world.get_components(TransformGrp, TexturedObject):
            t.rotate(dt)

        for e, (poly, tr) in self.world.get_components(Poly2D, TransformGrp):
            poly.time += dt
            if self.time > 3:
                tr.pos = [0.0, 0.0, 0.0]
                poly.verts.vertices = [
                    1.0*20, 0.0*20,
                    0.0*20, 1.0*20,
                    -0.0*20, 0.0*20
                ]
                poly.verts.colors = \
                    [1.0, 1.0, 0.0, 1.0] + \
                    [0.0, 1.0, 0.0, 0.5] + \
                    [0.0, 0.0, 1.0, 0.3];


class WindowProcessor(pyglet.window.Window, esper.Processor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_minimum_size(400, 300)
        glClearColor(0.2, 0.2, 0.2, 1.0)
        self.fps_display = pyglet.clock.ClockDisplay()
        self.cam = None
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def on_draw(self):
        self.clear()
        main_batch.draw()
        self.fps_display.draw()

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        if self.cam:
            self.cam.resize(width, height)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.cam:
            if scroll_y > 0:
                self.cam.zoom(0.1)
            if scroll_y < 0:
                self.cam.zoom(-0.1)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if (buttons == 1):
            if self.cam:
                self.cam.drag(dx, dy)
        #if (button == 4): TODO Cam rotation

    def process(self, dt):
        pass


def run(args=None):
    world = esper.World()
    window = WindowProcessor(1280, 720, "My Pyglet Window", resizable=True)
    world.add_processor(window)
    world.add_processor(MoveProcessor())

    # FACTORY
    c_shader = pyshaders.from_files_names("shaders/vert3d.glsl", "shaders/frag3d.glsl")
    shader_grp = ShaderGrp(c_shader)

    camera_grp = CameraGrp(0, c_shader, shader_grp)
    world.create_entity(camera_grp)
    window.cam = camera_grp

    depth_grp = DepthTestGrp(0, camera_grp)
    texture_grp = EnableTextureGrp(depth_grp)
    label_grp = ColorizeFontGrp(1, c_shader, parent=shader_grp)

    t = TransformGrp(c_shader, parent=camera_grp)
    t.pos = [10.0, 0.0]
    t.angle = 1.0
    t.scale = [1.0, 2.0]
    p = Poly2D(c_shader, tri, parent=t, clrs=(1.0, 0.5, 1.0, 0.5))
    world.create_entity(p,t)

    ct = TransformGrp(c_shader, parent=texture_grp)
    ct.pos = [0.0, 0.0, 0.0]
    xmas = TexturedObject.from_file(c_shader, "models/cube.obj", 'models/cube.jpg', ct)
    world.create_entity(xmas, ct)

    tt = TransformGrp(c_shader, parent=texture_grp)
    tt.pos = [10.0, 10.0, 0.0]
    tt.parent_trfm = ct
    std = TexturedObject.from_file(c_shader, "models/xmas_tree.obj", 'models/xmas_texture.jpg', tt)
    world.create_entity(std, tt)

    for i in range(20):
        t = TransformGrp(c_shader, parent=depth_grp)
        t.pos = [randint(-10, 10), randint(-10, 10), randint(-10, 10)]
        t.angle = randint(-10, 10)
        cb = TexturedObject(c_shader, std.mesh, std.texture, t)
        world.create_entity(cb, t)

    # self.monkey = Monkey(m_shader)
    t = TransformGrp(c_shader, parent=texture_grp)
    t.pos = [0.0, 5.0, -10.0]
    t.parent_trfm = tt
    monkey = TexturedObject.from_file(c_shader, 'models/monkey.obj', 'models/monkey.jpg', t)
    world.create_entity(monkey, t)

    global label
    tl = TransformGrp(c_shader, parent=monkey)
    tl.parent_trfm = t
    tl.scale = [0.2, 0.2]
    tl.pos = [0.0, 0.0, 1.0]
    label = pyglet.text.Label('a monkey', batch=main_batch, group=tl,
                              font_size=10, color=(1.0, 0.0, 0.0, 0.5),
                              x=0, y=0)

    label = pyglet.text.Label('Hello, world', batch=main_batch, group=label_grp,
                              font_size=36, color=(1.0, 0.0, 0.0, 0.5),
                              x=10, y=100)
    # END FACTORY

    pyglet.clock.schedule_interval(world.process, 1/60.0)
    pyglet.app.run()
