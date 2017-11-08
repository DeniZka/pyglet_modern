from pyglet.gl import *

import time
import math

from app import pyshaders
from random import randint, triangular

from app.c_rend import *
from app.c_camera import CameraGrp
from app.c_rend_stuff import *
from app.c_transform import TransformGrp
from app.c_wire import Wire

tri = [
    1.0*10, 0.0*10,
    0.0*10, 1.0*10,
    -0.0*10, 0.0*10
]

lines = [
    1.0 * 10, 0.0 * 10,
    0.0 * 10, 1.0 * 10,
    0.0 * 10, 1.0 * 10,
    -0.0 * 10, 0.0 * 10,
    -0.0 * 10, 0.0 * 10,
    1.0 * 10, 0.0 * 10,

]


class Factory:
    world = None
    win_proc = None
    shader = None
    cam = None
    wires_transform = None
    wires_coloring = None

    def __init__(self, world, win_proc):
        Factory.world = world
        Factory.win_proc = win_proc
        Factory.shader = None
        Factory.cam = None
        return

    @staticmethod
    def create_world():
        c_shader = pyshaders.from_files_names("shaders/vert3d.glsl", "shaders/frag3d.glsl")
        Factory.shader = c_shader
        shader_grp = ShaderGrp(c_shader)

        camera_grp = CameraGrp(0, c_shader, shader_grp)
        Factory.world.create_entity(camera_grp)
        Factory.cam = camera_grp
        Factory.win_proc.cam = camera_grp

        depth_grp = DepthTestGrp(0, camera_grp)
        texture_grp = EnableTextureGrp(depth_grp)
        xmas_bind_grp = BindTextureGrp.from_file('models/xmas_texture.jpg', texture_grp)
        cube_bind_grp = BindTextureGrp.from_file('models/cube.jpg', texture_grp)
        monkey_bind_grp = BindTextureGrp.from_file('models/monkey.jpg', texture_grp)
        xmas_mesh = ObjLoader()
        xmas_mesh.load_model("models/xmas_tree.obj")

        label_grp = ColorizeFontGrp(1, c_shader, parent=shader_grp)

        t = TransformGrp(c_shader, parent=camera_grp)
        t.pos = [10.0, 0.0]
        t.angle = 1.0
        t.scale = [1.0, 2.0]
        p = Primitive2D(c_shader, tri, group=t, clrs=(1.0, 0.5, 1.0, 10.5))
        p.add_lines(lines, (0.0, 1.0, 0.0, 1.0))
        Factory.world.create_entity(p, t)

        ct = TransformGrp(c_shader, parent=cube_bind_grp)
        ct.pos = [0.0, 0.0, 0.0]
        cube = TexturedObject.from_file(c_shader, "models/cube.obj", ct)
        Factory.world.create_entity(cube, ct)

        for i in range(30):
            t = TransformGrp(c_shader, parent=xmas_bind_grp)
            t.pos = [randint(-10, 10), randint(-10, 10), randint(-10, 10)]
            t.angle = randint(-10, 10)
            cb = TexturedObject(c_shader, xmas_mesh, t)
            Factory.world.create_entity(cb, t)

        tt = TransformGrp(c_shader, parent=xmas_bind_grp)
        tt.pos = [10.0, 10.0, 0.0]
        tt.parent_trfm = ct
        std = TexturedObject(c_shader, xmas_mesh, tt)
        Factory.world.create_entity(std, tt)

        # Factory.monkey = Monkey(m_shader)
        t = TransformGrp(c_shader, parent=monkey_bind_grp)
        t.pos = [0.0, 5.0, -10.0]
        t.parent_trfm = tt
        monkey = TexturedObject.from_file(c_shader, 'models/monkey.obj', t)
        Factory.world.create_entity(monkey, t)

        tl = TransformGrp(c_shader, parent=t)
        tl.parent_trfm = t
        tl.scale = [0.2, 0.2]
        tl.pos = [0.0, 0.0, 1.0]
        pyglet.text.Label('a monkey', batch=Renderable.batch, group=tl,
                          font_size=10, color=(1.0, 0.0, 0.0, 0.5),
                          x=0, y=0)
        pyglet.text.Label('Hello, world', batch=Renderable.batch, group=label_grp,
                          font_size=36, color=(1.0, 0.0, 0.0, 0.5),
                          x=10, y=100)

    @staticmethod
    def create_wire(x1, y1, x2, y2):
        if not Factory.wires_transform:
            Factory.wires_transform = TransformGrp(Factory.shader, parent=Factory.cam)
            Factory.wires_coloring = EnableColoringGrp(Factory.shader, Factory.wires_transform)
        g = Primitive2D(Factory.shader, (x1, y1, x2, y2), GL_LINES, Factory.wires_coloring, (0.0, 1.0, 0.0, 1.0))
        w = Wire([x1, y1, x2, y2])
        e = Factory.world.create_entity(g, w)
        return e, g, w, [(0, 2, 3)]  # like select