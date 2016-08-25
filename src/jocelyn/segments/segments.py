import cv2
import numpy
import scipy.ndimage

from segment import Segment

from matplotlib import pyplot

def find_edge_segments(image, paths, redlines, threshold):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Build singular path
    path = []
    for i_path in paths:
        for e in i_path:
            r, c = e
            if len(path) == 0 or e != path[-1]:
                path.append(e)

    intensities = {}
    for e in path:
        r, c = e
        if gray_image[r, c] < threshold:
            intensities[e] = 0
        else:
            intensities[e] = gray_image[r, c]

    intensity_image = numpy.zeros(gray_image.shape)
    for e, intensity in intensities.iteritems():
        r, c = e
        intensity_image[r, c] = intensity

    normalized_intensity = numpy.zeros(intensity_image.shape)
    normalized_intensity[intensity_image > 0] = 1

    binary_full = scipy.ndimage.generate_binary_structure(2, 2)
    labeled_objects, num_objects = scipy.ndimage.label(normalized_intensity,
                                                       structure=binary_full)

    segments = []
    for idx in range(1, num_objects + 1):
        mass = labeled_objects.copy()
        mass[mass != idx] = 0
        mass[mass > 0] = 1

        segment = Segment(mass, image, path, redlines, threshold)
        segments.append(segment)

    return segments




    #plotter = numpy.zeros(gray_image.shape)
    #for e, intensity in intensities.iteritems():
    #    r, c = e
    #    plotter[r, c] = intensity
    #pyplot.imshow(plotter)
    #pyplot.show()