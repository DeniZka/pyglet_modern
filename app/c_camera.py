import pyglet
from pyrr import matrix44
import math


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
        self.is_ortho = True #ortho
        self.ortho = None
        self.persp = None
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
        self.ortho = matrix44.create_orthogonal_projection(
            -self.width / 2 / self._zoom, self.width / 2 / self._zoom,
            -self.height / 2 / self._zoom, self.height / 2 / self._zoom,
            -100.0, 100.0
        )
        self.persp = matrix44.create_perspective_projection_matrix(
            50.0, self.width / self.height, 0.1, 200.0)
        if self.is_ortho:
            self.projection = self.ortho
        else:
            self.projection = self.persp
        self.default_proj = matrix44.create_orthogonal_projection(
            0, self.width, 0, self.height, -1, 1
        )
        self.view = matrix44.create_look_at(
            (self.x, self.y, 10.0),
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

    def swap_mode(self):
        self.is_ortho = not self.is_ortho
        self.calc_projection()
