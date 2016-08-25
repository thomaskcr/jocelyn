import cv2
import math
import numpy
import skimage.morphology
import scipy.signal

from .utility import interpolate_unit_box

from matplotlib import pyplot

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


        self.data = numpy.zeros(self.image.shape)
        self.data = self.data[:, :, 1]
        for data in p_t_data:
            p, p_r, p_c, t, t_r, t_c, z = data
            self.data[t_r, t_c] = z

        self.data_10 = numpy.zeros((self.image.shape[0]*10,
                                    self.image.shape[1]*10))
        for data in p_t_data:
            p, p_r, p_c, t, t_r, t_c, z = data
            self.data_10[t_r*10, t_c*10] = z

        skeleton_10 = skimage.morphology.medial_axis(self.data_10)

        # inv_skeleton = 1 - skeleton_10
        neighbor_counts = scipy.signal.convolve2d(skeleton_10, numpy.ones((3,3)), mode='same')
        neighbor_counts = neighbor_counts * skeleton_10
        print numpy.unique(neighbor_counts)
        #for e in numpy.transpose(numpy.nonzero(skeleton_10)):
        #    print e

        plotter = numpy.zeros((self.image.shape[0]*10, self.image.shape[1]*10))
        # plotter = plotter[:, :, 1]
        for data in p_t_data:
            p, p_r, p_c, t, t_r, t_c, z = data
            #print p, p_r, p_c, t, t_r, t_c, z

            plotter[t_r*10, t_c*10] = z

        for e in numpy.transpose(numpy.nonzero(skeleton_10)):
            r, c = e
            plotter[r, c] = 200

        for e in numpy.transpose(numpy.where(neighbor_counts == 2)):
            r, c = e
            plotter[r, c] = 255

        pyplot.imshow(plotter)
        pyplot.show()


    def hydrate(self):
        self._hydrate_path()
        self._hydrate_data()


