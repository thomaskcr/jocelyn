

def interpolate_unit_box(x, y, xf_yf, xc_yf, xf_yc, xc_yc):

    if x > 1 or y > 1:
        raise Exception("x and y must be between 0 and 1")

    xf_yf = float(xf_yf)
    xc_yf = float(xc_yf)
    xf_yc = float(xf_yc)
    xc_yc = float(xc_yc)

    z = ((xf_yf * (1 - x) * (1 - y)) +
         (xc_yf * x * (1 - y)) +
         (xf_yc * (1 - x) * y) +
         (xc_yc * x * y))

    return z
