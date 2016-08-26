import cv2
import numpy
import math

import scipy.spatial
import skimage.draw
import skimage.measure

from matplotlib import pyplot

from utility import shoelace_area

TRACE_COLOR = (0, 0, 255)

class Cell:

    def __init__(self, image, paths):
        self.__area_image = None
        self.__sorted_hull_points = None

        self.image = image
        self.paths = paths

        # Get a complete path
        self.path = []
        for path in self.paths:
            for e in path:
                r, c = e
                self.path.append(e)

    def get_sector_image(self):
        r_min, r_max = None, None
        c_min, c_max = None, None

        traced_cell = self.image.copy()

        for path in self.paths:
            for e in path:
                r, c = e
                traced_cell[r, c] = TRACE_COLOR
                if r_min is None or r < r_min :
                    r_min = r
                if r_max is None or r > r_max:
                    r_max = r
                if c_min is None or c < c_min :
                    c_min = c
                if c_max is None or c > c_max:
                    c_max = c

        sector_r = r_min - 25, r_max + 25
        sector_c = c_min - 25, c_max + 25

        return traced_cell[sector_r[0]:sector_r[1], sector_c[0]:sector_c[1]]


    def get_area_image(self):
        if self.__area_image is None:
            path = numpy.asarray(self.path)

            area_image = numpy.zeros(self.image.shape)
            rr, cc = skimage.draw.polygon(path[:,0], path[:,1], self.image.shape)
            area_image[rr, cc, 1] = 100

            self.__area_image = area_image

        return self.__area_image

    def get_area(self):
        area_image = self.get_area_image()

        return float(numpy.count_nonzero(area_image[:, :, 1]))

    def get_perimeter(self):
        area_image = self.get_area_image()
        area_image = area_image[:, :, 1]
        area_image[numpy.nonzero(area_image)] = 1

        return float(skimage.measure.perimeter(area_image))

    def get_convex_hull(self):
        if self.__sorted_hull_points is None:
            path = numpy.asarray(self.path)

            hull = scipy.spatial.ConvexHull(self.path)
            hull_indices = numpy.unique(hull.simplices.flat)

            hull_points = path[hull_indices, :]

            centroid = (sum([p[0] for p in hull_points])/len(hull_points),
                        sum([p[1] for p in hull_points])/len(hull_points))

            sorted_hull_points = \
                sorted(hull_points,
                       key=lambda p: math.atan2(p[1]-centroid[1], p[0]-centroid[0]))

            self.__sorted_hull_points = sorted_hull_points

        return self.__sorted_hull_points

    def get_convex_area_image(self):
        hull_points = self.get_convex_hull()
        hull_points = numpy.asarray(hull_points)

        hull_r, hull_c = skimage.draw.polygon_perimeter(hull_points[:,0],
                                                        hull_points[:,1],
                                                        self.image.shape)

        hull_area_image = numpy.zeros(self.image.shape)
        hull_area_image[hull_r, hull_c, 1] = 100

        return float(hull_area_image)

    def get_convex_area(self):
        sorted_hull_points = self.get_convex_hull()
        convex_area = shoelace_area(sorted_hull_points)
        return float(convex_area)

    def get_solidity(self):
        return float(self.get_area() / self.get_convex_area())

    def get_circularity(self):
        perimeter = self.get_perimeter()
        area = self.get_area()

        return (4.0 * math.pi * area) / perimeter**2

    def get_aspect_ratio(self):
        path = numpy.asarray(self.path)
        # path = numpy.asarray(self.get_convex_hull())
        ellipse = skimage.measure.EllipseModel()
        ellipse.estimate(path)

        xc, yc, a, b, theta = ellipse.params

        return float(a) / float(b)
