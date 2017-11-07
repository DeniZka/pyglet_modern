from pyglet.gl import *

import time
import math

from app import pyshaders
from random import randint, triangular

from app.c_rend import *
from app.c_camera import CameraGrp
from app.c_rend_stuff import *
from app.c_transform import TransformGrp

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


class Factory():
    def __init__(self, world, win_proc):
        self.world = world
        self.win_proc = win_proc
        return

    def create_world(self):
        c_shader = pyshaders.from_files_names("shaders/vert3d.glsl", "shaders/frag3d.glsl")
        shader_grp = ShaderGrp(c_shader)

        camera_grp = CameraGrp(0, c_shader, shader_grp)
        self.world.create_entity(camera_grp)
        self.win_proc.cam = camera_grp

        depth_grp = DepthTestGrp(0, camera_grp)
        texture_grp = EnableTextureGrp(depth_grp)
        label_grp = ColorizeFontGrp(1, c_shader, parent=shader_grp)

        t = TransformGrp(c_shader, parent=camera_grp)
        t.pos = [10.0, 0.0]
        t.angle = 1.0
        t.scale = [1.0, 2.0]
        p = Primitive2D(c_shader, tri, parent=t, clrs=(1.0, 0.5, 1.0, 10.5))
        p.add_lines(lines, (0.0, 1.0, 0.0, 1.0))
        self.world.create_entity(p, t)

        ct = TransformGrp(c_shader, parent=texture_grp)
        ct.pos = [0.0, 0.0, 0.0]
        xmas = TexturedObject.from_file(c_shader, "models/cube.obj", 'models/cube.jpg', ct)
        self.world.create_entity(xmas, ct)

        tt = TransformGrp(c_shader, parent=texture_grp)
        tt.pos = [10.0, 10.0, 0.0]
        tt.parent_trfm = ct
        std = TexturedObject.from_file(c_shader, "models/xmas_tree.obj", 'models/xmas_texture.jpg', tt)
        self.world.create_entity(std, tt)

        for i in range(30):
            t = TransformGrp(c_shader, parent=depth_grp)
            t.pos = [randint(-10, 10), randint(-10, 10), randint(-10, 10)]
            t.angle = randint(-10, 10)
            cb = TexturedObject(c_shader, std.mesh, std.texture, t)
            self.world.create_entity(cb, t)

        # self.monkey = Monkey(m_shader)
        t = TransformGrp(c_shader, parent=texture_grp)
        t.pos = [0.0, 5.0, -10.0]
        t.parent_trfm = tt
        monkey = TexturedObject.from_file(c_shader, 'models/monkey.obj', 'models/monkey.jpg', t)
        self.world.create_entity(monkey, t)

        tl = TransformGrp(c_shader, parent=monkey)
        tl.parent_trfm = t
        tl.scale = [0.2, 0.2]
        tl.pos = [0.0, 0.0, 1.0]
        pyglet.text.Label('a monkey', batch=RenderableGroup.batch, group=tl,
                          font_size=10, color=(1.0, 0.0, 0.0, 0.5),
                          x=0, y=0)
        pyglet.text.Label('Hello, world', batch=RenderableGroup.batch, group=label_grp,
                          font_size=36, color=(1.0, 0.0, 0.0, 0.5),
                          x=10, y=100)