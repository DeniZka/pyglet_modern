import pyglet
import esper
from app.p_move import MoveProcessor
from app.p_window import WindowProcessor
from app.p_editor import EditorProcessor
from app.factory import Factory


def run(args=None):
    world = esper.World()
    window = WindowProcessor(1280, 720, "A Window", resizable=True)
    world.add_processor(window)
    world.add_processor(MoveProcessor())
    world.add_processor(EditorProcessor(window))

    factory = Factory(world, window)
    factory.create_world()

    pyglet.clock.schedule_interval(world.process, 1/60.0)
    pyglet.app.run()
