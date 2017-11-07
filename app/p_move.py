import esper
from app.c_transform import TransformGrp
from app.c_rend import *


class MoveProcessor(esper.Processor):
    def __init__(self):
        super().__init__()
        self.time = 0.0

    def process(self, dt):
        self.time += dt
        for e, (t, to) in self.world.get_components(TransformGrp, TexturedObject):
            if e < 10:
                t.rotate(dt)

        for e, (poly, tr) in self.world.get_components(Primitive2D, TransformGrp):
            poly.time += dt
            if (3.0 - self.time) < 0.1:
                tr.pos = [0.0, 0.0, 0.0]
                poly.verts[0].vertices = [
                    1.0*20, 0.0*20,
                    0.0*20, 1.0*20,
                    -0.0*20, 0.0*20
                ]
                poly.verts[0].colors = \
                    [1.0, 1.0, 0.0, 1.0] + \
                    [0.0, 1.0, 0.0, 0.5] + \
                    [0.0, 0.0, 1.0, 0.3]