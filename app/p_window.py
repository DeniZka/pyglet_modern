import time
import pyglet
from pyglet.gl import *
from pyglet.window import key
import esper
from app.c_rend import RenderableGroup


class Event(list):
    """Event subscription.

    A list of callable objects. Calling an instance of this will cause a
    call to each item in the list in ascending order by index.

    Example Usage:
    >>> def f(x):
    ...     print 'f(%s)' % x
    >>> def g(x):
    ...     print 'g(%s)' % x
    >>> e = Event()
    >>> e()
    >>> e.append(f)
    >>> e(123)
    f(123)
    >>> e.remove(f)
    >>> e()
    >>> e += (f, g)
    >>> e(10)
    f(10)
    g(10)
    >>> del e[0]
    >>> e(2)
    g(2)

    """
    def __call__(self, *args, **kwargs):
        for f in self:
            f(*args, **kwargs)

    def __repr__(self):
        return "Event(%s)" % list.__repr__(self)


class WindowProcessor(pyglet.window.Window, esper.Processor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_minimum_size(400, 300)
        glClearColor(0.2, 0.2, 0.2, 1.0)
        #self.fps_display = pyglet.clock.ClockDisplay()
        self.cam = None
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.e_m_scroll = Event()
        self.e_m_drag = Event()
        self.e_m_press = Event()
        self.e_m_release = Event()


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

    def on_mouse_press(self, x, y, button, modifiers):
        self.e_m_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        self.e_m_release(x, y, button, modifiers)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.cam:
            if scroll_y > 0:
                self.cam.zoom(0.1)
            if scroll_y < 0:
                self.cam.zoom(-0.1)
        self.e_m_scroll(x, y, scroll_x, scroll_y)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & 4 == 4:
            if self.cam:
                self.cam.drag(dx, dy)
        self.e_m_drag(x, y, dx, dy, buttons, modifiers)
        #if (button == 4): TODO Cam rotation

    def on_key_press(self, symbol, modifiers):
        super().on_key_press(symbol, modifiers)
        if symbol == key.NUM_5:
            self.cam.swap_mode()

    def process(self, dt):
        pass