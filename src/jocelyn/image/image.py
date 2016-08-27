import cv2
import numpy

from matplotlib import pyplot
from scipy import ndimage
from scipy import signal


from features import _get_void_seeds, _get_redlines
from features import VOID_SEED_COLOR
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
        self.redlines = _get_redlines(image, feature_image)

    def get_coverage(self, movie=False):
        gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        clustered, centers = cluster_image(self.image, 8)

        gray_clustered = cv2.cvtColor(clustered, cv2.COLOR_BGR2GRAY)
        gray_centers = numpy.unique(gray_clustered)

        voids = self.void_seeds

        frames = []
        done = False
        finished = []

        working_image = gray_image.copy()
        for idx, void in voids.iteritems():
            working_image[void == idx] = 0
        for redline in self.redlines:
            r, c = redline
            gray_image[r, c] = 0

        while not done:
            assigned_elements = numpy.zeros(gray_image.shape)

            for idx, void in voids.iteritems():
                if idx in finished:
                    continue

                normalized = numpy.zeros(gray_image.shape)
                normalized[void == idx] = 1

                dilated = ndimage.binary_dilation(normalized).astype(normalized.dtype)
                adjacent = numpy.subtract(dilated, normalized)

                added_elements = 0
                for e in numpy.transpose(numpy.nonzero(adjacent)):
                    r, c = e
                    if gray_image[r, c] < gray_centers[1] and working_image[r, c] != 0:
                        assigned_elements[r, c] = idx
                        working_image[r, c] = 0
                        added_elements += 1

                if added_elements < numpy.count_nonzero(adjacent) * 0.15:
                    finished.append(idx)

            # Add assigned elements
            for e in numpy.transpose(numpy.nonzero(assigned_elements)):
                r, c = e

                assigned_index = assigned_elements[r, c]

                mass = voids[assigned_index]
                mass[r, c] = assigned_index
                voids[assigned_index] = mass

            if numpy.count_nonzero(assigned_elements) == 0:
                done = True

            if movie:
                frame = self.image.copy()

                for idx, void in voids.iteritems():
                    frame[void == idx] = numpy.asarray([255, 0, 255])

                frames.append(frame)

            live_regions = len(voids.keys()) - len(finished)
            pixels_added = (((assigned_elements != 0)).sum())
            print ("%d live regions - %d pixels added" % (live_regions, pixels_added))

        # Get percentages
        process_image = self.image.copy()
        for idx, void in voids.iteritems():
            process_image[void == idx] = numpy.asarray([255, 0, 255])

        void_total = numpy.count_nonzero(numpy.where(
            numpy.all(process_image == VOID_SEED_COLOR, axis = -1)))

        image_size = float(process_image.shape[0]*process_image.shape[1])

        void_percent = (float(void_total) / image_size) * 100.0

        if movie:
            return process_image, void_percent, frames
        else:
            return process_image, void_percent
