import cv2
import numpy
import math

from scipy import ndimage
from skimage import morphology

from matplotlib import pyplot

k_means_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
k_means_flags = cv2.KMEANS_RANDOM_CENTERS


def cluster_image(image_region, clusters):
    iterations = 10

    # Turn the image into an array of pixels
    image_pixels = image_region.reshape((-1,3))
    image_pixels = numpy.float32(image_pixels)

    compactness, labels, cluster_centers = \
        cv2.kmeans(image_pixels, clusters, None, k_means_criteria, iterations,
                   k_means_flags)

    # Convert back to unsigned 8 bit integers
    cluster_centers = numpy.uint8(cluster_centers)

    # List of pixels
    cluster_pixels = cluster_centers[labels.flatten()]
    clustered_image = cluster_pixels.reshape((image_region.shape))

    return clustered_image, cluster_centers