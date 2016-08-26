import cv2
import numpy

from matplotlib import pyplot

from features import _get_void_seeds
from k_means import cluster_image

class Image:

    def __init__(self, image, feature_images):
        if image is None:
            # OpenCV does not automatically raise an error when an image cannot
            # be found which can lead to None objects being passed in
            raise Exception("Image file is empty or not found.")

        if len(image.shape) != 3 and image.shape[2] != 3:
            # Make sure image is not grayscale and has 3 color channels.
            raise Exception("Must use color image with 3 color channels.")

        self.image = image

        # Currently only support using one feature image
        feature_image = feature_images[0]

        self.void_seeds = _get_void_seeds(image, feature_image)

    def get_coverage(self):
        gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        clustered, centers = cluster_image(self.image, 16)

        print centers

        voids = self.void_seeds

        for idx, void in voids.iteritems():
            normalized = numpy.zeros(gray_image.shape)
            normalized[numpy.nonzero((void == idx))] = 1

            average = numpy.mean(gray_image[void == idx])
            print average

            #pyplot.imshow(normalized)
            #pyplot.show()


            print idx, numpy.count_nonzero(void)



