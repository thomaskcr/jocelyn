
## Installation

### Windows

The Python(x,y) distribution has all of the tools needed. Download it here: http://python-xy.github.io/downloads.html 

If you don't do the full installation, make sure you go through the list and include:

- OpenCV
- Scipy
- Numpy
- scikit-image
- Matplotlib


## Overview




## Terms

- Sector - Piece of an image

- Cell

- Segment - Piece of a cell wall. 

  These are not defined by waypoints (i.e. a segment can include and pass through a waypoint)


## Feature Marking

Feature marking is a way of guiding the algorithm. You will add marks with specific colors to a copy of the image called `features.tif` (or `features.png`, etc). Each mark gives different guidance to the algorithms. 

### Waypoints 

Waypoints mark a general path for computing the perimeter of the cell. 
 
The edge finding algorithm works by finding the Minimum Cost Path between each waypoint. The cost matrix is calculated by inverting the intensity of each pixel in the image by subtracting it from 255 (each pixel is an 8 bit integer, `2^8 - 1 = 255` (range starts at 0 not 1)). 
  
By finding the minimum cost path, it is effectively finding the shortest but brightest path between the two points. 

Waypoints are added to the image as a single pixel colored pure blue (Hex: #0000FF, RGB: (0, 0, 255)). They should be added when the minimum cost path between two points won't necessarily be the best estimation of the cell's edge. You can add additional waypoints to shorten the distance between waypoints, making it more costly for the algorithm to go out of the way. 

As an example, the minimum cost path in this figure does not follow the apparent cell edge. 

![](doc/waypoints-example-1.png)

By adding 3 waypoints you can redirect the path finding algorithm to include the convex region. 

![](doc/waypoints-example-2.png)

**Note:** It is important when adding these to pay attention to the behavior of your image editor of choice. For example, in Gimp the paint brush will create "soft" edges instead of just setting all of the pixels to the value you selected. In Gimp make sure to use the pencil tool. 
  
 Brush tool: 
 
 ![](doc/brush.png)
 
 Pencil tool:
 
 ![](doc/pencil.png)

- Redlines

  Pure Red (#FF0000 or (255, 0, 0))

  Will not be crossed when expanding a segment

  Fully redlined regions will be ignored when doing feature searches

- Regions

  Boxes that mark a region of interest - i.e. perpendicular region

  Segments within regions will be analyzed separately

## Examples

### Waypoints

Example files are located in the directory `examples/waypoints`. `features.tif` shows an example of marked waypoints.

To run this example:

```
python run.py --path-check ../examples/waypoints/
```

This will show the computed path based on the waypoints provided. 

![](examples/waypoints/output_figure_1.png)

### Shape Factors


