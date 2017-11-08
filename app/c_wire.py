

class Wire:

    def __init__(self, points):
        self.points = []
        self.points.append(points)

    def add_line(self, points):
        self.points.append(points)

    def select(self, x, y, precise=0.1):
        """

        :param x:
        :param y:
        :param precise: maximal distance to mark as selected
        :return: list of (list_ind, x_ind, y_ind)
        """
        sel = []
        for i in range(len(self.points)):
            if abs(self.points[i][0] - x) < precise and abs(self.points[i][1] - y) < precise:
                sel.append((i, 0, 1))
                continue
            if abs(self.points[i][2] - x) < precise and abs(self.points[i][3] - y) < precise:
                sel.append((i, 2, 3))
        return sel
