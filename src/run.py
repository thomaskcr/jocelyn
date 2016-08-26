import csv
import cv2
import glob
import math
import numpy
import os
import time

import scipy.misc

from skimage import draw
from matplotlib import pyplot
from optparse import OptionParser

import jocelyn.image
import jocelyn.waypoints
import jocelyn.paths
import jocelyn.segments

from jocelyn.cell import Cell
from jocelyn.edge import Edge
from jocelyn.image import Image

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
parser.add_option("--perimeter",
                  action="store_const", dest="program",
                  default="all", const="perimeter",
                  help="Calculate the perimeter incidence data.")
parser.add_option("--coverage",
                  action="store_const", dest="program",
                  default="all", const="coverage",
                  help="Calculate void space and cellular coverage.")
parser.add_option("--segments",
                  action="store_const", dest="program",
                  default="all", const="segments",
                  help="Process segments")
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

output_directory = run_directory + 'output/'

# Create the output directory if it does not already exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

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

    paths = jocelyn.waypoints.find_path(input_image, waypoints, redlines)

    gray_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)

    path_image = input_image.copy().astype(numpy.uint8)
    path_image[:, :, 0] = gray_image
    path_image[:, :, 1] = gray_image
    path_image[:, :, 2] = gray_image

    for path in paths:
        for e in path:
            r, c = e
            path_image[r, c] = 255, 0, 0

    for waypoint in waypoints:
        r, c = waypoint
        path_image[r, c] = 0, 0, 255

    pyplot.imshow(path_image)
    pyplot.show()

if options.program == "shape-factors":
    waypoints, redlines, regions = \
        jocelyn.image.extract_features(input_image, feature_images)

    paths = jocelyn.waypoints.find_path(input_image, waypoints, redlines)

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

    # Sector values
    sect_r_min, sect_r_max, sect_c_min, sect_c_max = cell.get_sector()
    # Scaled sector values
    s_s_r_min, s_s_r_max, s_s_c_min, s_s_c_max = \
        sect_r_min * 10, sect_r_max * 10, sect_c_min * 10, sect_c_max * 10

    pyplot.imshow(cell.get_traced_image())
    cur_axes = pyplot.gca()
    cur_axes.axes.get_xaxis().set_visible(False)
    cur_axes.axes.get_yaxis().set_visible(False)
    pyplot.savefig(output_directory + 'perimeter.png',
                   bbox_inches='tight', pad_inches=0, dpi=300)

    sector_image = cell.get_sector_image()

    # Save the sector image figure
    pyplot.imshow(sector_image)
    cur_axes = pyplot.gca()
    cur_axes.axes.get_xaxis().set_visible(False)
    cur_axes.axes.get_yaxis().set_visible(False)
    pyplot.savefig(output_directory + 'sector-perimeter.png',
                   bbox_inches='tight', pad_inches=0, dpi=300)

    # Save the convex hull figure
    plotter = cell.get_traced_image()

    plotter = scipy.misc.imresize(plotter,
                                  (plotter.shape[0]*10, plotter.shape[1]*10, 3))

    hull_points = cell.get_convex_hull()

    hull_image = input_image.copy()
    hull_image[:, :, 0] = 0
    hull_image[:, :, 1] = 0
    hull_image[:, :, 2] = 0

    for idx in range(0, len(hull_points)):
        if idx == len(hull_points) - 1:
            s_r, s_c = hull_points[0]
            e_r, e_c = hull_points[idx]
        else:
            s_r, s_c = hull_points[idx]
            e_r, e_c = hull_points[idx + 1]

        line_rr, line_cc, pressure = draw.line_aa(s_r, s_c, e_r, e_c)
        hull_image[line_rr, line_cc, 0] = pressure*255

    hull_image = scipy.misc.imresize(hull_image,
                                     (plotter.shape[0], plotter.shape[1]))

    for e in numpy.transpose(numpy.nonzero(hull_image[:, :, 0])):
        r, c = e
        plotter[r, c, 0] = hull_image[r, c, 0]
        plotter[r, c, 1] = plotter[r, c, 1]
        plotter[r, c, 2] = hull_image[r, c, 2]

    pyplot.imshow(plotter)
    cur_axes = pyplot.gca()
    cur_axes.axes.get_xaxis().set_visible(False)
    cur_axes.axes.get_yaxis().set_visible(False)
    pyplot.savefig(output_directory + 'convex-hull.png',
                   bbox_inches='tight', pad_inches=0, dpi=300)

    pyplot.imshow(plotter[s_s_r_min:s_s_r_max, s_s_c_min:s_s_c_max, :])
    cur_axes = pyplot.gca()
    cur_axes.axes.get_xaxis().set_visible(False)
    cur_axes.axes.get_yaxis().set_visible(False)
    pyplot.savefig(output_directory + 'sector-convex-hull.png',
                   bbox_inches='tight', pad_inches=0, dpi=300)

    # Plot aspect ratio
    xc, yc, a, b, theta = cell.get_ellipse_parameters()

    r_c, c_c = int(xc), int(yc)

    a_end_r = r_c + a * math.cos(theta)
    a_end_c = c_c + a * math.sin(theta)
    a_end_r, a_end_c = int(a_end_r), int(a_end_c)

    a_start_r = r_c - a * math.cos(theta)
    a_start_c = c_c - a * math.sin(theta)
    a_start_r, a_start_c = int(a_start_r), int(a_start_c)

    b_end_r = r_c + b * math.cos(theta - math.pi/2.0)
    b_end_c = c_c + b * math.sin(theta - math.pi/2.0)
    b_end_r, b_end_c = int(b_end_r), int(b_end_c)

    b_start_r = r_c - b * math.cos(theta - math.pi/2.0)
    b_start_c = c_c - b * math.sin(theta - math.pi/2.0)
    b_start_r, b_start_c = int(b_start_r), int(b_start_c)

    plotter = input_image.copy()

    plotter = scipy.misc.imresize(plotter,
                                  (plotter.shape[0]*10, plotter.shape[1]*10, 3))

    a_aspect_points = input_image.copy()
    a_aspect_points[:, :, 0] = 0
    a_aspect_points[:, :, 1] = 0
    a_aspect_points[:, :, 2] = 0

    b_aspect_points = input_image.copy()
    b_aspect_points[:, :, 0] = 0
    b_aspect_points[:, :, 1] = 0
    b_aspect_points[:, :, 2] = 0

    line_rr, line_cc, pressure = draw.line_aa(r_c, c_c, a_start_r, a_start_c)
    a_aspect_points[line_rr, line_cc, 0] = pressure*255

    line_rr, line_cc, pressure = draw.line_aa(r_c, c_c, a_end_r, a_end_c)
    a_aspect_points[line_rr, line_cc, 0] = pressure*255

    line_rr, line_cc, pressure = draw.line_aa(r_c, c_c, b_start_r, b_start_c)
    b_aspect_points[line_rr, line_cc, 2] = pressure*255

    line_rr, line_cc, pressure = draw.line_aa(r_c, c_c, b_end_r, b_end_c)
    b_aspect_points[line_rr, line_cc, 2] = pressure*255


    a_aspect_points = scipy.misc.imresize(a_aspect_points,
                                          (plotter.shape[0], plotter.shape[1]))

    rr, cc = numpy.nonzero(a_aspect_points[:, :, 0])
    plotter[rr, cc, 0] = a_aspect_points[rr, cc, 0]

    rr, cc = numpy.where(a_aspect_points[:, :, 0] == 255)
    plotter[rr, cc, 1] = 0
    plotter[rr, cc, 2] = 0

    b_aspect_points = scipy.misc.imresize(b_aspect_points,
                                          (plotter.shape[0], plotter.shape[1]))

    rr, cc = numpy.nonzero(b_aspect_points[:, :, 2])
    plotter[rr, cc, 2] = b_aspect_points[rr, cc, 2]

    rr, cc = numpy.where(b_aspect_points[:, :, 2] == 255)
    plotter[rr, cc, 0] = 0
    plotter[rr, cc, 1] = 0

    pyplot.imshow(plotter)
    cur_axes = pyplot.gca()
    cur_axes.axes.get_xaxis().set_visible(False)
    cur_axes.axes.get_yaxis().set_visible(False)
    pyplot.savefig(output_directory + 'aspect-ratio.png',
                   bbox_inches='tight', pad_inches=0, dpi=300)

    pyplot.imshow(plotter[s_s_r_min:s_s_r_max, s_s_c_min:s_s_c_max, :])
    cur_axes = pyplot.gca()
    cur_axes.axes.get_xaxis().set_visible(False)
    cur_axes.axes.get_yaxis().set_visible(False)
    pyplot.savefig(output_directory + 'sector-aspect-ratio.png',
                   bbox_inches='tight', pad_inches=0, dpi=300)


if options.program == "perimeter":
    waypoints, redlines, regions = \
        jocelyn.image.extract_features(input_image, feature_images)

    paths = jocelyn.waypoints.find_path(input_image, waypoints)

    cell = Cell(input_image, paths)

    path_coverage, point_coverage, percent_coverage = \
        cell.get_perimeter_coverage()

    print "Perimeter Coverage: %.4f" % percent_coverage

    with open(output_directory + 'coverage-data.csv', 'wb') as csv_f:
        writer = csv.writer(csv_f)
        writer.writerow(['Point', 'Row', 'Column', 'Covered'])
        for point in range(0, len(path_coverage)):
            writer.writerow([point, point_coverage[point][0],
                             point_coverage[point][0], path_coverage[point]])

if options.program == "coverage":
    image = Image(input_image, feature_images)

    image.get_coverage()

exit()




if options.program == "segments":
    waypoints, redlines, regions = \
        jocelyn.image.extract_features(input_image, feature_images)

    paths = jocelyn.waypoints.find_path(input_image, waypoints)

    edge_segments = jocelyn.segments.find_edge_segments(input_image, paths,
                                                        redlines, threshold)

    edge_segments[2].hydrate()

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



