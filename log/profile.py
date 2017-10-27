import pstats
from subprocess import call
p = pstats.Stats("out.stat")

p.strip_dirs().sort_stats("tottime").print_stats()
call(['pyprof2calltree', '-i', 'out.stat', '-o', 'callgrind.out'])
call(['kcachegrind', 'callgrind.out'])

#-m cProfile -o log/out.stat
