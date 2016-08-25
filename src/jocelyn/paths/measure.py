import cv2
import numpy
import math

from .utility import interpolate_unit_box


def _get_path_intensity(image, path):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    path_intensity = []
    idx = 0
    for e in path:
        r, c = e

        path_intensity.append([idx, gray_image[r, c]])
        idx += 1

    return path_intensity


def _get_peak_intensity(image, path):
    pass


def _get_path_data(image, path, threshold):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    float_image = numpy.float_(gray_image)

    p_limits = {}
    p_t_data = {}

    # Find normal slope for each point
    for idx in range(0, len(path)):
        if idx + 1 >= len(path):
            r1, c1 = path[idx-1]
            r2, c2 = path[idx]
        else:
            r1, c1 = path[idx]
            r2, c2 = path[idx+1]

        vector_r, vector_c = (r2 - r1), (c2 - c1)
        norm_vector_r, norm_vector_c = -1*vector_c, vector_r

        if idx + 1 >= len(path):
            r1, c1 = path[idx]

        dt_pos, dt_neg = 0, 0
        t_upper = path[idx]
        t_lower = path[idx]

        t_data = []

        done = False
        t = 0
        while not done:
            r = (r1 + norm_vector_r * t)
            c = (c1 + norm_vector_c * t)

            c_l = math.floor(c)
            c_h = math.ceil(c)

            r_l = math.floor(r)
            r_h = math.ceil(r)

            # Interpolate intensity
            z = interpolate_unit_box(c - c_l, r - r_l, float_image[r_l, c_l],
                                     float_image[r_l, c_h],
                                     float_image[r_h, c_l],
                                     float_image[r_h, c_h])

            if z < threshold:
                done = True
                dt_pos = t
                t_upper = r, c

            t_data.append((r, c, t, z))

            t = t + .1

        done = False
        t = 0
        while not done:
            r = (r1 + norm_vector_r * t)
            c = (c1 + norm_vector_c * t)

            c_l = math.floor(c)
            c_h = math.ceil(c)

            r_l = math.floor(r)
            r_h = math.ceil(r)

            # Interpolate intensity
            z = interpolate_unit_box(c - c_l, r - r_l, float_image[r_l, c_l],
                                     float_image[r_l, c_h],
                                     float_image[r_h, c_l],
                                     float_image[r_h, c_h])

            if z < threshold:
                done = True
                dt_neg = t
                t_lower = r, c

            t_data.append((r, c, t, z))

            t = t + -.1

        p_limits[idx] = [t_upper, t_lower]
        p_t_data[idx] = t_data

    p_widths = {}
    for key, value in p_limits.iteritems():
        dist = numpy.linalg.norm(numpy.asarray(value[0]) - numpy.asarray(value[1]))
        p_widths[key] = dist
        print key, path[key], value[0], value[1], dist

    return p_t_data, p_limits, p_widths


def get_path_measurements(image, path):

    path_intensity = _get_path_intensity(image, path)
    path_data, path_limits, path_widths = _get_path_data(image, path, 100)


