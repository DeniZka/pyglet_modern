import pyglet
from pyrr import Matrix44


class TransformGrp(pyglet.graphics.Group):
    """
    Unifrom transfromation access group
    """
    def __init__(self, shader, transform_matrix=None, parent_transform=None, parent=None):
        super().__init__(parent=parent)
        self.shader = shader
        self._ptr = parent_transform
        self._pos = [0.0, 0.0, 0.0]
        self._tm = Matrix44.from_translation(self._pos)
        self._angle = 0.0
        self._rm = Matrix44.from_z_rotation(self._angle)
        self._scale = [1.0, 1.0, 1.0]
        self._sm = Matrix44.from_scale(self.scale)
        self._trfm = self._tm * self._rm * self._sm
        self._gtr = self._trfm  # global transform include parent transformations
        if self.parent and self.parent.__class__ is TransformGrp:
            self._gtr = self.parent.transform * self._trfm
        self.dirty = True  # global transform calculated

    def get_transform(self, glob=True):
        """
        :return: Total transform matrix
        """
        if self.dirty:
            self._trfm = self._tm * self._rm * self._sm
        if self._ptr and glob:
            self._gtr = self._ptr.transform * self._trfm
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
        self._trfm = val
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