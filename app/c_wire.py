

class Wire:
    precise = 0.01

    def __init__(self, points, name=''):
        self.name = name
        self.points = []
        self.points.append(points)

        self.bb = list(self.points[0])
        self.update_bb()

    def add_line(self, points):
        self.points.append(points)
        self.update_bb()

    def select(self, x, y, dist=1, except_list=()):
        """

        :param x:
        :param y:
        :param dist: maximal distance to mark as selected
        :return: list of (list_ind, x_ind, y_ind)
        """
        # find first nearest
        min_dist_id = -1
        min_dist_x = -1
        min_dist_y = -1

        exc_ids = []
        for e in except_list:
            exc_ids.append(e[0])

        for i in range(len(self.points)):
            if i in exc_ids:
                continue
            if min_dist_id == -1:
                for j in range(2):
                    # get in bb
                    min_dist_x = self.points[i][j * 2]
                    min_dist_y = self.points[i][j * 2 + 1]
                    if abs(min_dist_x - x) < dist and abs(min_dist_y - y) < dist:
                        min_dist_id = i
                        break
        if min_dist_id == -1:
            return []

        # get the same position
        sel = []
        for i in range(len(self.points)):
            for j in range(2):
                if abs(self.points[i][j * 2] - min_dist_x) < Wire.precise and \
                     abs(self.points[i][j * 2 + 1] - min_dist_y) < Wire.precise:
                    sel.append((i, j * 2, j * 2 + 1))
                continue
        return sel

    def update_points(self, ind, part_id, val):
        self.points[ind][part_id] = val
        self.update_bb()

    def update_bb(self):
        for p in self.points:
            self.bb[0] = min([self.bb[0], p[0], p[2]])
            self.bb[1] = min([self.bb[1], p[1], p[3]])
            self.bb[2] = max([self.bb[2], p[0], p[2]])
            self.bb[3] = max([self.bb[3], p[1], p[3]])

    def in_bb(self, x, y, dist=1):
        """
        Fastest check collision with some additional distance
        :param x, y: position
        :param dist:
        :return: boolean
        """
        if self.bb[0] - dist < x < self.bb[2] + dist and \
           self.bb[1] - dist < y < self.bb[3] + dist:
            return True
        else:
            return False
