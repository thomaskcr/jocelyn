import cv2
import glob
import numpy
import os

from matplotlib import pyplot
from optparse import OptionParser

import jocelyn.image
import jocelyn.waypoints
import jocelyn.paths
import jocelyn.segments

from jocelyn.cell import Cell
from jocelyn.edge import Edge

usage = "usage: %prog [options] input-folder"
parser = OptionParser(usage=usage)

parser.add_option("-v", "--verbose",
                  action="store_true", dest="verbose", default=False,
                  help="Print status messages to stdout while running")
parser.add_option("-d", "--debug",
                  action="store_true", dest="debug", default=False,
                  help="Print debug information")
parser.add_option("--show-plots",
                  action="store_true", dest="debug", default=False,
                  help="Print debug information")


parser.add_option("-t", "--threshold",
                  action="store", dest="threshold", default=100,
                  help="Change the threshold used for calculation (default " +
                       "threshold is 100)")
parser.add_option("--path-check",
                  action="store_const", dest="program",
                  default="all", const="path-check",
                  help="Check only the paths")
parser.add_option("--shape-factors",
                  action="store_const", dest="program",
                  default="all", const="shape-factors",
                  help="Calculate shape factors for cell")

parser.add_option("-f", "--file", dest="filename",
                  help="write report to FILE", metavar="FILE")
(options, args) = parser.parse_args()

# Parse folder argument
if len(args) == 0:
    raise Exception("You must specify a folder to run jocelyn against.")

relative_directory = args[0]
run_directory = os.path.abspath(relative_directory) + "/"

if not os.path.isdir(run_directory):
    raise Exception(("You must specify a folder to run jocelyn against. " +
                    "Supplied argument '%s' is not a folder.") % run_directory)

threshold = int(options.threshold)

# Get images to be processed
input_image = cv2.imread(run_directory + 'input.tif')
feature_images = []
for feature_image_path in glob.glob(run_directory + 'features*'):
    feature_images.append(cv2.imread(feature_image_path))

if input_image is None:
    # OpenCV does not automatically raise an error when an image cannot be found
    raise Exception("Could not find input image.")

if len(feature_images) > 1:
    # There are still downstream processing things that need to be worked out
    # to properly deal with multiple feature images.
    raise Exception("Multiple image support has been removed in this version.")



if options.program == "path-check":
    waypoints, redlines, regions = \
        jocelyn.image.extract_features(input_image, feature_images)

    paths = jocelyn.waypoints.find_path(input_image, waypoints)

    gray_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)

    path_image = input_image.copy().astype(numpy.uint8)
    path_image[:, :, 0] = gray_image
    path_image[:, :, 1] = gray_image
    path_image[:, :, 2] = gray_image

    for path in paths:
        for e in path:
            r, c = e
            path_image[r, c] = 255, 0, 0

    pyplot.imshow(path_image)
    pyplot.show()

if options.program == "shape-factors":
    waypoints, redlines, regions = \
        jocelyn.image.extract_features(input_image, feature_images)

    paths = jocelyn.waypoints.find_path(input_image, waypoints)

    cell = Cell(input_image, paths)

    area = cell.get_area()
    print "Area:         %.4f" % area

    convex_area = cell.get_convex_area()
    print "Convex Area:  %.4f" % convex_area

    solidity = cell.get_solidity()
    print "Solidity:     %.4f" % solidity

    perimeter = cell.get_perimeter()
    print "Perimeter:    %.4f" % perimeter

    aspect_ratio = cell.get_aspect_ratio()
    print "Aspect Ratio: %.4f" % aspect_ratio

    circularity = cell.get_circularity()
    print "Circularity:  %.4f" % circularity



exit()




edge_segments = jocelyn.segments.find_edge_segments(input_image, paths,
                                                    redlines, threshold)

edge_segments[2].hydrate()



exit()



cell = Cell(input_image, paths)

#sector_image = cell.get_sector_image()

#pyplot.imshow(sector_image)
#pyplot.show()

#print cell.get_area()
#print cell.get_convex_area()
#cell.get_convex_area_image()
#print cell.get_perimeter()
# print cell.get_aspect_ratio()

edge = Edge(input_image, paths)

intensities = edge.get_path_intensity()

#intensities = numpy.asarray(intensities)
#pyplot.plot(intensities[:, 0], intensities[:, 1])
#pyplot.show()

path_data, path_limits, path_widths = edge.get_path_measurements(100)


plotter = numpy.zeros(input_image.shape)
plotter = plotter[:, :, 1]

for key, data in path_data.iteritems():
    for e in data:
        r, c, t, z = e

        plotter[r, c] = z

pyplot.imshow(plotter)
pyplot.show()



#pyplot.plot(path_widths.values())
#pyplot.show()



exit()


#image_waypoints = cv2.imread(run_directory + 'waypoints.tif')

#waypoints =  jocelyn.waypoints.extract_waypoints(image_waypoints)

paths = jocelyn.waypoints.find_path(input_image, waypoints)

for path in paths:
    measurements = jocelyn.paths.get_path_measurements(input_image, path)



