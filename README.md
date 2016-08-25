
## Installation

### Windows

The Python(x,y) distribution has all of the tools needed. Download it here: http://python-xy.github.io/downloads.html 

If you don't do the full installation, make sure you go through the list and include:

- OpenCV
- Scipy
- Numpy
- scikit-image
- Matplotlib


## Terms

- Sector

- Cell

- Segment


## Feature Marking

- Waypoints

  Pure Blue (#0000FF or (0, 0, 255))

  Followed by program as a general outline of the cell - don't need to be perfectly accurate

- Redlines

  Pure Red (#FF0000 or (255, 0, 0))

  Will not be crossed when expanding a segment

  Fully redded out regions will be ignored when doing feature searches

- Regions

  Boxes that mark a region of interest - i.e. perpendicular region

  Segments within regions will be analyzed separately



