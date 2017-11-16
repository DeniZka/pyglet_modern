from app.vec2d import Vec2d


class Segment(list):

    def __init__(self, node1, node2):
        super().__init__()
        self.append(node1)
        node1.add_seg(self)
        self.append(node2)
        node2.add_seg(self)

    def __del__(self):
        #super().__del__()
        self[0].del_seg(self)
        self[1].del_seg(self)

    @property
    def points(self):
        return self[0].x, self[0].y, self[1].x, self[1].y

    def another(self, node):
        if node == self[0]:
            return self[1]
        else:
            return self[0]


class Node:
    """
    Vertex
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.segs = []

    #def __del__(self):
        #self.segs.

    def add_seg(self, segment):
        self.segs.append(segment)

    def del_seg(self, segment):
        self.segs.remove(segment)


class Wire:
    precise = 0.00001

    def __init__(self, points, name=''):
        self.name = name

        self._nods = [] # new joints
        self._segs = [] # new segments

        st = Node(points[0], points[1])
        sp = Node(points[2], points[3])
        seg = Segment(st, sp)
        self._nods.append(st)
        self._nods.append(sp)
        self._segs.append(seg)

        self._points = []
        self._points.append(points)

        self.bb = list(self._points[0])
        self.update_bb()

    def points(self, seg_ind):
        st = self._segs[seg_ind][0]
        sp = self._segs[seg_ind][1]
        return st.x, st.y, sp.x, sp.y

    def add_line(self, points):
        st = Vec2d(points[0], points[1])
        sp = Vec2d(points[2], points[3])

        self._points.append(points)
        self.update_bb()

    def merge(self, src_wire, src_node, dest_node):
        # swap nodes
        src_node.segs += dest_node.segs
        self._nods.remove(dest_node)
        # swap in nodes
        for s in self._segs:
            for i in range(2):
                if s[i] == dest_node:
                    s[i] = src_node
        # move segments
        self._segs += src_wire._segs
        # move joints
        self._nods += src_wire._nods

    def self_merge(self, src_node, dest_node):
        # swap in nodes
        for s in self._segs:
            for i in range(2):
                if s[i] == dest_node:
                    s[i] = src_node
                    src_node.segs.append(s)
        self._nods.remove(dest_node)

    def select(self, x, y, dist=1, except_nodes=()):
        """

        :param x:
        :param y:
        :param dist: maximal distance to mark as selected
        :return: list of (list_ind, x_ind, y_ind)
        """
        for n in self._nods:
            if except_nodes:
                # no self
                if n in except_nodes:
                    continue
            if abs(n.x - x) < dist and abs(n.y - y) < dist:
                return n
        return None

    def segment_index(self, segment):
        return self._segs.index(segment)

    def update_points(self, ind, part_id, val):
        self._points[ind][part_id] = val
        self.update_bb()

    def update_bb(self):
        for p in self._points:
            self.bb[0] = min([self.bb[0], p[0], p[2]])
            self.bb[1] = min([self.bb[1], p[1], p[3]])
            self.bb[2] = max([self.bb[2], p[0], p[2]])
            self.bb[3] = max([self.bb[3], p[1], p[3]])

    def in_bb(self, x, y, margin=1):
        """
        Fastest check collision with some additional distance
        :param x, y: position
        :param margin:
        :return: boolean
        """
        if self.bb[0] - margin < x < self.bb[2] + margin and \
           self.bb[1] - margin < y < self.bb[3] + margin:
            return True
        else:
            return False
