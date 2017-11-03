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
            (0.0, 1.0, 0.0)
        )
        self.dirty = True

    def resize(self, width, height):
        self.width = width
        self.height = height
        self.calc_projection()

    def zoom(self, val):
        self._zoom += self._zoom * val
        self.calc_projection()


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
        self.shader.uniforms.colorize = 1
        self.shader.uniforms.clr_clr = self.color
        self.shader.uniforms.trfm = matrix44.create_identity()  #Clean transform matrix before draw lables TODO move somewhere

    def unset_state(self):
        self.shader.uniforms.colorize = 0


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
    def __init__(self, vertex_list, color_list, parent=None):
        super().__init__(parent=parent)
        self.vlist = vertex_list
        self.clist = color_list

    def __del__(self):
        self.vertex_list = None

class GraphicTextured(pyglet.graphics.Group):
    """
    Painted with texture vertices
    """
    def __init__(self, vertex_list, texture, color=(1.0, 1.0, 1.0, 1.0), parent=None):
        super().__init__(parent=parent)
        self.vlist = vertex_list
        self.color = color
        self.texture = texture

    def __del__(self):
        self.vertex_list = None

    def set_state(self):
        glBindTexture(self.texture.target, self.texture.id)


class AbstractTransform(pyglet.graphics.Group):
    """
    Unifrom transfromation access group
    """
    def __init__(self, transform_matrix=None, parent_transform=None, parent=None):
        super().__init__(parent=parent)
        self._ptr = parent_transform
        self._tr = transform_matrix
        if self._tr is None:
            self._tr = Matrix44.identity()
        self._gtr = self._tr  # global transform include parent transformations
        if self.parent and self.parent.__class__ is AbstractTransform:
            self._gtr = self.parent.transform * self._tr

        self._pos = [0.0, 0.0, 0.0]
        self._tm = Matrix44.from_translation(self._pos)
        self._angle = 0.0
        self._rm = Matrix44.from_z_rotation(self._angle)
        self._scale = [1.0, 1.0, 1.0]
        self._sm = Matrix44.from_scale(self.scale)
        self._trfm = self._tm * self._rm * self._sm
        self.dirty = True  # global transform calculated

    @property
    def local_transform(self):
        return self._tr

    @property
    def transform(self):
        """
        :return: Total transform matrix
        """
        if self._ptr:
            if self.dirty:
                self._gtr = self._ptr.transform * self._tr
        else:
            if self.dirty:
                self._gtr = self._tr
                self.dirty = False
        return self._gtr

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

    def set_state(self):
        if self.dirty:
            self._trfm = self._tm * self._rm * self._sm
            self.dirty = False
        self.shader.uniforms.trfm = self._trfm


class TexturedObject(AbstractTransform):
    def __init__(self, shader, mesh, texture, parent=None):
        super().__init__(parent=parent)
        self.time = 0.0 #tempraty time
        self.shader = shader
        self.mesh = mesh
        self.texture = texture

        num_verts = len(mesh.model_vertices) // 3
        self.verts = main_batch.add(num_verts, GL_TRIANGLES, self, ('v3f/static', mesh.model_vertices),
                                                                   ('1g3f/static', mesh.model_textures))

    @classmethod
    def from_file(cls, shader, model_fn, tex_fn, parent=None):
        mesh = ObjLoader()
        mesh.load_model(model_fn)
        texture = pyglet.image.load(tex_fn).texture
        #texture = pyglet.resource.image(tex_fn, False)
        return cls(shader, mesh, texture, parent)

    def set_state(self):
        super().set_state()
        # textures
        self.shader.uniforms.coloring = 0
        glBindTexture(self.texture.target, self.texture.id)


class Poly2D(AbstractTransform):
    def __init__(self, shader, vertices, type=GL_TRIANGLES, parent=None):
        super().__init__(parent=parent)
        self.time = 0.0
        self.shader = shader
        self.dirty = True
        self._color = []

        self._trfm = Matrix44.identity()
        self._scale = Matrix44.identity()

        num_verts = int(len(vertices) / 2)
        for i in range(num_verts):
            for j in range(3):
                self._color.append(triangular(0.0, 1.0))
            self._color.append(triangular(0.7, 1.0))

        self.verts = main_batch.add(num_verts, type, self,
                                    ('v2f/static', vertices),
                                    ('2g4f/static', self._color))

    def set_state(self):
        super().set_state()
        self.shader.uniforms.coloring = 1
        #self.shader.uniforms.time = self.time

    def unset_state(self):
        self.shader.uniforms.coloring = 0
        self.dirty = False


class MoveProcessor(esper.Processor):
    def __init__(self):
        super().__init__()
        self.time = 0.0

    def process(self, dt):
        self.time += dt
        for e, to in self.world.get_component(TexturedObject):
            # self.ta += 0.1 * dt
            to.rotate(dt)
            #to._angle += dt
            # self.r += dt
            # self.scale[0] = math.sin(self.r) + 2
            to.dirty = True

        for e, poly in self.world.get_component(Poly2D):
            poly.time += dt
            if self.time > 3:
                poly.verts.vertices = [
                1.0*20, 0.0*20,
                0.0*20, 1.0*20,
                -0.0*20, 0.0*20
            ]


class WindowProcessor(pyglet.window.Window, esper.Processor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_minimum_size(400, 300)
        glClearColor(0.2, 0.2, 0.2, 1.0)
        self.fps_display = pyglet.clock.ClockDisplay()

    def on_draw(self):
        self.clear()
        main_batch.draw()
        self.fps_display.draw()

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        for e, cam in self.world.get_component(CameraGrp):
            cam.resize(width, height)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        for e, cam in self.world.get_component(CameraGrp):
            if scroll_y > 0:
                cam.zoom(0.1)
            if scroll_y < 0:
                cam.zoom(-0.1)

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
    depth_grp = DepthTestGrp(0, camera_grp)
    texture_grp = EnableTextureGrp(depth_grp)
    blend_grp = BlendGrp(1, camera_grp)
    label_grp = ColorizeFontGrp(1, c_shader, parent=shader_grp)

    p = Poly2D(c_shader, tri, parent=blend_grp)
    p.pos = [10.0, 0.0]
    p.angle = 1.0
    p.scale = [1.0, 2.0]
    world.create_entity(p)

    xmas = TexturedObject.from_file(c_shader, "models/cube.obj", 'models/cube.jpg', texture_grp)
    xmas.pos = [10.0, 10.0, 0.0]
    world.create_entity(xmas)

    std = TexturedObject.from_file(c_shader, "models/xmas_tree.obj", 'models/xmas_texture.jpg', texture_grp)
    std.pos = [10.0, 0.0, 0.0]
    world.create_entity(std)

    for i in range(200):
        cb = TexturedObject(c_shader, std.mesh, std.texture, depth_grp)
        cb.pos = [randint(-10, 10), randint(-10, 10), randint(-10, 10)]
        world.create_entity(cb)
        v = (triangular(), triangular(), triangular())
        # v = (0.0, 1.0, 1.0)
        a = triangular()  # math.pi/2
        q = quaternion.create_from_axis_rotation(v, a)
        # m = matrix44.create_from_quaternion(q)#inverse_of_quaternion(q)
        # cb.angle = randint(-10, 10) / 10
        #cb.angle = q
        cb.angle = randint(-10, 10)

    # self.monkey = Monkey(m_shader)
    monkey = TexturedObject.from_file(c_shader, 'models/monkey.obj', 'models/monkey.jpg', texture_grp)
    world.create_entity(monkey)

    global label
    label = pyglet.text.Label('Hello, world', batch=main_batch, group=label_grp,
                              font_size=36,
                              x=10, y=100)
    # END FACTORY

    pyglet.clock.schedule_interval(world.process, 1/60.0)
    pyglet.app.run()
