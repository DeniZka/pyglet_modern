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
