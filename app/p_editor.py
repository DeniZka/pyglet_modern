import esper
from app.c_rend import Primitive2D
from app.c_wire import Wire
from app.c_camera import CameraGrp
from app.factory import Factory


class EditorProcessor(esper.Processor):

    def __init__(self, win_proc):
        super().__init__()
        self.window = win_proc
        self.cam = None
        # subscribing
        self.window.e_m_drag.append(self.on_mouse_drag)
        self.window.e_m_press.append(self.on_mouse_press)
        self.window.e_m_release.append(self.on_mouse_release)

        self.drag_ent = 0
        self.drag_wire = None
        self.drag_line = None
        self.sel = []

    def _has_cam(self):
        self.cam = CameraGrp.active_cam
        return self.cam

    def _get_wire(self, x, y):
        for e, (p, w) in self.world.get_components(Primitive2D, Wire):
            sel = w.select(x, y)
            if len(sel) > 0:
                self.drag_ent = e
                self.sel = sel
                self.drag_line = p
                self.drag_wire = w
                return True
        return False

    def _update_sel_scrn(self, x, y):
        if self._has_cam():
            wx, wy = self.cam.to_world(x, y)
            self._update_sel_wrld(wx, wy)

    def _update_sel_wrld(self, x, y):
        for s in self.sel:
            self.drag_wire.points[s[0]][s[1]] = x
            self.drag_wire.points[s[0]][s[2]] = y
            self.drag_line.verts[s[0]].vertices = self.drag_wire.points[s[0]]

    def on_mouse_press(self, x, y, button, modifiers):
        wx = x
        wy = y
        if self._has_cam():
            wx, wy = self.cam.to_world(x, y)
        if button & 1 == 1:
            if not self._get_wire(wx, wy):
                self.drag_ent, self.drag_line, self.drag_wire, self.sel = Factory.create_wire(wx, wy, wx, wy)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if len(self.sel) > 0:
            self._update_sel_scrn(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.drag_ent:
            # drop to
            wx, wy = self.cam.to_world(x, y)
            for e, (p, w) in self.world.get_components(Primitive2D, Wire):
                if e == self.drag_ent:
                    continue
                sel = w.select(wx, wy)
                if len(sel) > 0:
                    # update
                    self._update_sel_wrld(w.points[sel[0][0]][sel[0][1]], w.points[sel[0][0]][sel[0][2]])
                    # drop
                    w.points += self.drag_wire.points
                    p.verts += self.drag_line.verts
                    self.world.delete_entity(self.drag_ent)
            #clean
            self.drag_ent = 0
            self.drag_wire = None
            self.drag_line = None
            self.sel = []

    def process(self, dt):
        pass
