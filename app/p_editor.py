import esper
from app.c_rend import Primitive2D
from app.c_wire import Wire
from app.c_camera import CameraGrp
from app.factory import Factory


class EditorProcessor(esper.Processor):

    PICK_DIST = 14

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

        self.contact_list = [] # list of entities, Primitives and Wires that could be used. Don't want to repeat on drag
        self.except_list = []

    def _has_cam(self):
        self.cam = CameraGrp.active_cam
        return self.cam

    def _get_wire(self, x, y):
        dist = EditorProcessor.PICK_DIST / self.cam.zoom
        for e, (p, w) in self.world.get_components(Primitive2D, Wire):
            #if w.in_bb(x, y, dist):
            sel = w.select(x, y, dist)
            if sel:
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
        self.sel.x = x
        self.sel.y = y
        for s in self.sel.segs:
            ind = self.drag_wire.segment_index(s)
            self.drag_line.verts[ind].vertices = s.points

    def on_mouse_press(self, x, y, button, modifiers):
        wx = x
        wy = y
        if self._has_cam():
            wx, wy = self.cam.to_world(x, y)
        if button & 1 == 1:
            if not self._get_wire(wx, wy):
                self.drag_ent, self.drag_line, self.drag_wire, self.sel = Factory.create_wire(wx, wy, wx, wy)
            # calc except list for self wire
            self.except_list.append(self.sel)
            for s1 in self.sel.segs:
                n1 = s1.another(self.sel)
                if n1 in self.except_list:
                    continue
                self.except_list.append(n1)
                for s2 in n1.segs:
                    n2 = s2.another(n1)
                    if n2 in self.except_list:
                        continue
                    self.except_list.append(n2)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.sel:
            wx, wy = self.cam.to_world(x, y)
            dist = EditorProcessor.PICK_DIST / self.cam.zoom
            if not self.contact_list:
                for e, (p, w) in self.world.get_components(Primitive2D, Wire):
                    if e != self.drag_ent:  # exclude selected
                        self.contact_list.append(w)
            sel = None
            for cl in self.contact_list:
                sel = cl.select(wx, wy, dist)
                if sel:
                    self._update_sel_wrld(sel.x, sel.y)
                    break
            # Check with self
            if not sel:
                sel = self.drag_wire.select(wx, wy, dist, self.except_list)
                if sel:
                    self._update_sel_wrld(sel.x, sel.y)
            # simple move
            if not sel:
                self._update_sel_wrld(wx, wy)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.drag_ent:
            # drop to
            wx, wy = self.cam.to_world(x, y)
            dist = EditorProcessor.PICK_DIST / self.cam.zoom
            for e, (p, w) in self.world.get_components(Primitive2D, Wire):
                if e == self.drag_ent:
                    sel = w.select(wx, wy, dist, self.except_list)
                    if sel:
                        self._update_sel_wrld(sel.x, sel.y)
                        w.self_merge(self.sel, sel)

                else:
                    sel = w.select(wx, wy, dist)
                    if sel:
                        # update
                        self._update_sel_wrld(sel.x, sel.y)
                        # drop
                        w.merge(self.drag_wire, self.sel, sel)
                        #w.points += self.drag_wire.points
                        p.verts += self.drag_line.verts
                        self.world.delete_entity(self.drag_ent)
            #clean
            self.drag_ent = 0
            self.drag_wire = None
            self.drag_line = None
            self.sel = None
        self.contact_list = []
        self.except_list = []

    def process(self, dt):
        pass
