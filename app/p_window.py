import time
import pyglet
from pyglet.gl import *
from pyglet.window import key
import esper
from app.c_rend import RenderableGroup


class WindowProcessor(pyglet.window.Window, esper.Processor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_minimum_size(400, 300)
        glClearColor(0.2, 0.2, 0.2, 1.0)
        #self.fps_display = pyglet.clock.ClockDisplay()
        self.cam = None
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def on_draw(self):
        self.clear()
        t = time.time()
        RenderableGroup.draw()
        print ((1/(time.time()-t)))
        #self.fps_display.draw()

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
        if buttons & 4 == 4:
            if self.cam:
                self.cam.drag(dx, dy)
        #if (button == 4): TODO Cam rotation

    def on_key_press(self, symbol, modifiers):
        super().on_key_press(symbol, modifiers)
        if symbol == key.NUM_5:
            self.cam.swap_mode()

    def process(self, dt):
        pass