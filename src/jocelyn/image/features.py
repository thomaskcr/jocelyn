import cv2
import numpy
import math

import scipy.ndimage
import skimage.draw

from matplotlib import pyplot


# Colors are BGR in CV2
WAYPOINT_COLOR = (255, 0, 0)
REDLINE_COLOR = (0, 0, 255)
REGION_COLOR = (0, 255, 0)
VOID_SEED_COLOR = (255, 0, 255)

def _get_waypoints(image, feature_image):
    """
    Gets a list of waypoints ordered by polar angle

    Args:
        image (numpy.ndarray): Original image file, must have 3 channels (RGB).
        feature_image (numpy.ndarray): Image file with features highlighted,
            image must have 3 channels (BRG).


    """

    # Get indexes for all waypoints
    waypoint_indexes = \
        numpy.where(numpy.all(feature_image == WAYPOINT_COLOR, axis = -1))

    # Convert indexes to points
    waypoints = zip(waypoint_indexes[0], waypoint_indexes[1])

    centroid = (sum([p[0] for p in waypoints])/len(waypoints),
                sum([p[1] for p in waypoints])/len(waypoints))

    # Sort by polar angle
    waypoints = sorted(waypoints,
                       key=lambda
                           p: math.atan2(p[1]-centroid[1], p[0]-centroid[0]))

    # Reverse list so path moves clockwise
    waypoints = list(reversed(waypoints))

    return waypoints


def _get_redlines(image, feature_image):
    """
    Return a list of points comprising red-lined regions

    Although these are called redlines it is really a collection of "kill
    points", when one of these is hit during segment growth it will not cross
    that point.

    Args:
        image (numpy.ndarray): Original image file, must have 3 channels (RGB).
        feature_image (numpy.ndarray): Image file with features highlighted,
            image must have 3 channels (BRG).

    """

    redline_indexes = \
        numpy.where(numpy.all(feature_image == REDLINE_COLOR, axis = -1))

    # Convert indexes to points
    redlines = zip(redline_indexes[0], redline_indexes[1])

    return redlines


def _get_regions(image, feature_image):
    """
    Get a 1-indexed dictionary of regions of interest.

    Regions may be arbitrarily shaped.

    Args:
        image (numpy.ndarray): Original image file, must have 3 channels (RGB).
        feature_image (numpy.ndarray): Image file with features highlighted,
            image must have 3 channels (BRG).

    """

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    region_image = numpy.zeros(gray_image.shape)

    region_indexes = \
        numpy.where(numpy.all(feature_image == REGION_COLOR, axis = -1))
    region_image[region_indexes[0], region_indexes[1]] = 100

    binary_full = scipy.ndimage.generate_binary_structure(2, 2)
    labeled_objects, num_objects = scipy.ndimage.label(region_image,
                                                       structure=binary_full)

    region_masses = {}
    for idx in range(1, num_objects + 1):
        mass = labeled_objects.copy()
        mass[mass != idx] = 0

        # Normalize
        mass[mass == idx] = 1

        # Get a list of points outlining the polygon
        outline = numpy.transpose(numpy.nonzero(mass))

        # These can get really big, reduce vertices to approximately 100
        sample_factor = int(outline.shape[0]/100)
        if sample_factor > 1:
            outline = outline[::sample_factor, :]

        # Only works for polygons sorted by polar angle
        centroid = (sum([p[0] for p in outline])/len(outline),
                    sum([p[1] for p in outline])/len(outline))

        # Sort by polar angle
        outline = sorted(outline,
                         key=lambda
                             p: math.atan2(p[1]-centroid[1], p[0]-centroid[0]))

        # Convert back to numpy array
        outline = numpy.asarray(outline)

        # Fill in polygon
        rr, cc = skimage.draw.polygon(outline[:,0], outline[:,1], mass.shape)
        mass[rr, cc] = 1

        # De-normalize for consistency with the rest of the application since
        # convention has been to label masses with their index number.
        mass[mass == 1] = idx
        region_masses[idx] = mass

    return region_masses

def _get_void_seeds(image, feature_image):
    """
    Get a 1-indexed dictionary of void seeds

    Seeds may be arbitrarily shaped but I encourage circles

    Args:
        image (numpy.ndarray): Original image file, must have 3 channels (RGB).
        feature_image (numpy.ndarray): Image file with features highlighted,
            image must have 3 channels (BRG).

    """

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    region_image = numpy.zeros(gray_image.shape)

    region_indexes = \
        numpy.where(numpy.all(feature_image == VOID_SEED_COLOR, axis = -1))
    region_image[region_indexes[0], region_indexes[1]] = 100

    binary_full = scipy.ndimage.generate_binary_structure(2, 2)
    labeled_objects, num_objects = scipy.ndimage.label(region_image,
                                                       structure=binary_full)

    region_masses = {}
    for idx in range(1, num_objects + 1):
        mass = labeled_objects.copy()
        mass[mass != idx] = 0
        region_masses[idx] = mass

    return region_masses


def extract_features(image, feature_images):
    """
    Extract all of the features from the image and return structured
    representations of them.

    Args:
        image (numpy.ndarray): Original image file, must have 3 channels (BGR).
        feature_images (list<numpy.ndarray>): List of image files with features
            highlighted, each image must have 3 channels (BRG).

    Returns:
        waypoints (list):
        redlines (list):
        regions (dictionary):

    """

    if image is None:
        # OpenCV does not automatically raise an error when an image cannot be
        # found which can lead to None objects being passed in
        raise Exception("Image file is empty or not found.")

    if len(image.shape) != 3 and image.shape[2] != 3:
        # Make sure image is not grayscale and has 3 color channels.
        raise Exception("Must use color image with 3 color channels.")

    # Currently only support using one feature image
    feature_image = feature_images[0]

    waypoints = _get_waypoints(image, feature_image)
    redlines = _get_redlines(image, feature_image)
    regions = _get_regions(image, feature_image)

    return waypoints, redlines, regions
