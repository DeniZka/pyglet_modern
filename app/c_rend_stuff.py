import pyglet
from pyglet.gl import *
from pyrr import matrix44


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
        #pass


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
        #glDisable(GL_TEXTURE_2D)
        pass