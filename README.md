Main IDEA
=========
Pyglet+Shader+ECS

The pyglet is realy comfortable as graphical engine
but it has a problem with geometry updating. By default we cannot work
with vertices, textures, and colors in shaders. A little patching
and everything fine.
Also there is an experiment to work with Entity Component System

profiling tools:
----------------
* `pip3 install pyprof2calltree`
* `kcachegrind`

pyglet modifications:
---------------------
most important changes in `vertexattribute.py`

`glEnableClientState` -> `glEnableVertexAttribArray(<SHADER_LAYOUT__LOCATION_INDEX>)`
`glTexCoordPointer` -> `glVertexAttribPointer()`

Now layot location indexes are:
* 0 - vertices
* 1 - texture uvw
* 2 - vertex colors

TODO
----
Instanced draw