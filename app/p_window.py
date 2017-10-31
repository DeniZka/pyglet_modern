import esper
import pyglet
from app import pyshaders
from random import randint, triangular

from pyglet.gl import *
from pyrr import matrix44, Matrix44, quaternion

class WindowProcessor(pyglet.window.Window, esper.Processor):
    def __init__(self, *args, **kwargs):
        super(WindowProcessor, self).__init__(*args, **kwargs)
        return
        self.set_minimum_size(400, 300)
        glClearColor(0.2, 0.2, 0.2, 1.0)
        self.fps_display = pyglet.clock.ClockDisplay()

        self.cube = []
        ps = pyshaders.from_files_names("shaders/vert2d.glsl", "shaders/space.glsl")
        ps.use()
        ps.uniforms.proj = projection
        ps.uniforms.view = view
        p = Poly2D(ps, tri)
        #p.pos = [10.0, 0.0]
        p.angle = 1.0
        p.scale = [1.0, 2.0]
        p.color = [1.0, 0.0, 0.0, 1.0,
                   0.0, 1.0, 0.0, 1.0,
                   0.0, 0.0, 1.0, 1.0]
        self.p = p

        c_shader = pyshaders.from_files_names("shaders/vert3d.glsl", "shaders/frag3d.glsl")
        c_shader.use()
        c_shader.uniforms.proj = projection
        c_shader.uniforms.view = view
        self.xmas = TexturedObject.from_file(c_shader, "models/cube.obj", 'models/cube.jpg')
        self.xmas.pos = [10.0, 10.0, 0.0]

        c_shader = pyshaders.from_files_names("shaders/vert3d.glsl", "shaders/frag3d.glsl")
        c_shader.use()
        c_shader.uniforms.proj = projection
        c_shader.uniforms.view = view
        std = TexturedObject.from_file(c_shader, "models/xmas_tree.obj", 'models/xmas_texture.jpg')
        std.pos = [10.0, 0.0, 0.0]
        for i in range(100):
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
        m_shader = pyshaders.from_files_names("shaders/vert3d.glsl", "shaders/frag3d.glsl")
        m_shader.uniforms.proj = projection
        m_shader.uniforms.view = view
        #self.monkey = Monkey(m_shader)
        self.monkey = TexturedObject.from_file(m_shader, 'models/monkey.obj', 'models/monkey.jpg')

        self.label = pyglet.text.Label('Hello, world',
                              font_size=36,
                              x=10, y=100)


    def on_draw(self):
        return
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
        pyshaders.ShaderProgram.clear()  # or simply glUseProgram(0)

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
        self.p.update(dt)
        for i in range(10):
            self.cube[i].update(dt)


    # self methods
    def calc_projection(self):
        return
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

    def update(self, dt):
        pass


