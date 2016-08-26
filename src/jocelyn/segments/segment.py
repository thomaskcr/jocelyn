import cv2
import math
import numpy
import time

import skimage.morphology
import scipy.signal


from matplotlib import pyplot
from scipy import ndimage
from skimage import graph

from .utility import interpolate_unit_box


class Segment:


    def __init__(self, seed, image, path, redlines, threshold):
        self.seed = seed
        self.image = image
        self.full_path = path
        self.redlines = redlines
        self.threshold = threshold

        self.path = []
        self.data = numpy.zeros((0,0))
        self.data_10 = numpy.zeros((0,0))
        self.median_path_10 = None


    def _hydrate_path(self):
        """
        Hydrate self.path with an ordered list of points in the path
        """

        positions = {}
        for e in numpy.transpose(numpy.nonzero(self.seed)):
            r, c = e
            positions[self.full_path.index((r, c))] = e

        self.path = []
        for key in sorted(positions):
            self.path.append(positions[key])

    def __hydrate_median_line(self):
        pass

    def _hydrate_data(self):
        gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        for point in self.redlines:
            r, c = point
            gray_image[r, c] = 0
        float_image = numpy.float_(gray_image)

        p_t_data = []

        for p_idx in range(0, len(self.path) - 1):
            r1, c1 = self.path[p_idx]
            r2, c2 = self.path[p_idx + 1]

            vector_r, vector_c = (r2 - r1), (c2 - c1)
            norm_vector_r, norm_vector_c = -1*vector_c, vector_r

            dp_range = numpy.linspace(0, 2, 41)

            for dp in dp_range:
                p = p_idx + dp
                p_r = (r1 + vector_r * dp)
                p_c = (c1 + vector_c * dp)

                t_data = []

                done = False
                t = 0
                while not done:
                    t_r = (p_r + norm_vector_r * t)
                    t_c = (p_c + norm_vector_c * t)

                    t_r = round(t_r, 1)
                    t_c = round(t_c, 1)


                    c_l = math.floor(t_c)
                    c_h = math.ceil(t_c)

                    r_l = math.floor(t_r)
                    r_h = math.ceil(t_r)

                    # Interpolate intensity
                    z = interpolate_unit_box(t_c - c_l, t_r - r_l, float_image[r_l, c_l],
                                             float_image[r_l, c_h],
                                             float_image[r_h, c_l],
                                             float_image[r_h, c_h])

                    if z < self.threshold:
                        done = True
                    else:
                        t_data.append((p, p_r, p_c, t, t_r, t_c, z))

                    t = t - .05

                t_data = list(reversed(t_data))

                done = False
                t = 0
                while not done:
                    t_r = (p_r + norm_vector_r * t)
                    t_c = (p_c + norm_vector_c * t)

                    c_l = math.floor(t_c)
                    c_h = math.ceil(t_c)

                    r_l = math.floor(t_r)
                    r_h = math.ceil(t_r)

                    # Interpolate intensity
                    z = interpolate_unit_box(t_c - c_l, t_r - r_l, float_image[r_l, c_l],
                                             float_image[r_l, c_h],
                                             float_image[r_h, c_l],
                                             float_image[r_h, c_h])

                    if z < self.threshold:
                        done = True
                    else:
                        t_data.append((p, p_r, p_c, t, t_r, t_c, z))

                    t = t + .05

                p_t_data += t_data

            print p_idx, len(self.path), len(p_t_data)

        scale_factor = 10

        self.data = numpy.zeros(self.image.shape)
        self.data = self.data[:, :, 1]
        for data in p_t_data:
            p, p_r, p_c, t, t_r, t_c, z = data
            self.data[t_r, t_c] = z

        self.data_10 = numpy.zeros((self.image.shape[0]*scale_factor,
                                    self.image.shape[1]*scale_factor))
        for data in p_t_data:
            p, p_r, p_c, t, t_r, t_c, z = data
            self.data_10[t_r*scale_factor, t_c*scale_factor] = z


        skeleton_10 = skimage.morphology.medial_axis(self.data_10)

        neighbor_counts = scipy.signal.convolve2d(skeleton_10, numpy.ones((3,3)), mode='same')
        neighbor_counts = neighbor_counts * skeleton_10

        endpoints = []

        for e in numpy.transpose(numpy.where(neighbor_counts == 2)):
            r, c = e
            endpoints.append(e)

        inverse_skeleton = skeleton_10.copy().astype(numpy.uint8)
        inverse_skeleton[inverse_skeleton == 0] = 255
        inverse_skeleton[inverse_skeleton == 1] = 0

        costs = {}
        longest_stretch, best_path = None, None
        for index_a in range(0, len(endpoints)):
            for index_b in range(0, len(endpoints)):
                if index_a == index_b:
                    continue

                index = (min([index_a, index_b]), max([index_a, index_b]))
                if costs.get(index, None) is not None:
                    print index, "Already done"
                    continue

                start = time.time()
                indices, cost = graph.route_through_array(inverse_skeleton,
                                                          endpoints[index_a],
                                                          endpoints[index_b])

                costs[index] = cost
                if longest_stretch is None or len(indices) > longest_stretch:
                    longest_stretch, best_path = len(indices), indices
                print ("%s -> %s - %.2f: %.4f" % (str(index_a), str(index_b),
                                                  cost, time.time() - start))

        self.median_path_10 = best_path

        plotter = numpy.zeros((self.image.shape[0]*scale_factor,
                               self.image.shape[1]*scale_factor))

        for data in p_t_data:
            p, p_r, p_c, t, t_r, t_c, z = data

            plotter[t_r*scale_factor, t_c*scale_factor] = z

        for e in self.median_path_10:
            r, c = e
            plotter[r, c] = 255

        pyplot.imshow(plotter)
        pyplot.show()


    def hydrate(self):
        self._hydrate_path()
        self._hydrate_data()


