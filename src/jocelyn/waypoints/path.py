import cv2
import math
import numpy
from scipy import ndimage

from matplotlib import pyplot
from skimage import morphology
from skimage import graph

MAX_TEST = 3

def find_path(image, waypoints, redlines=None):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    contrast = gray_image.copy().astype(numpy.float_)

    contrast = numpy.square(contrast / numpy.max(gray_image)) * 255

    gray_image = contrast.copy().astype(gray_image.dtype)

    # Handle redlines
    if redlines is not None:
        for redline in redlines:
            r, c = redline
            gray_image[r, c] = 0

    paths = []

    start = waypoints[0]
    used = [0]

    done = False
    while not done:
        best = None, None, None
        tests = 0
        for idx in range(0, len(waypoints)):
            if idx not in used:
                end = waypoints[idx]

                path, cost = graph.route_through_array(255 - gray_image, start,
                                                       end)
                best_idx, best_cost, best_path = best

                if best_cost is None or cost < best_cost:
                    best = idx, cost, path

                tests += 1
                if tests >= MAX_TEST:
                    break


        best_idx, best_cost, best_path = best
        if best_cost is None:
            done = True
        else:
            used.append(best_idx)
            paths.append(best_path)
            start = waypoints[best_idx]

    # Complete circle
    start = waypoints[used[-1]]
    end = waypoints[0]
    path, cost = graph.route_through_array(255 - gray_image, start, end)
    paths.append(path)

    #plotter = gray_image.copy()
    #for path in paths:
    #    for e in path:
    #        r, c = e
    #        plotter[r, c] = 255
    #pyplot.imshow(plotter)
    #pyplot.show()

    return paths
