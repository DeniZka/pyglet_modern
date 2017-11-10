

class Wire:
    precise = 0.01

    def __init__(self, points, name=''):
        self.name = name
        self.points = []
        self.points.append(points)

    def add_line(self, points):
        self.points.append(points)

    def select(self, x, y, dist=1):
        """

        :param x:
        :param y:
        :param precise: maximal distance to mark as selected
        :return: list of (list_ind, x_ind, y_ind)
        """
        # find first nearest
        min_dist_id = -1
        min_dist_x = -1
        min_dist_y = -1
        for i in range(len(self.points)):
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
