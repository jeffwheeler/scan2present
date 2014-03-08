import itertools
import numpy as np

import geometry

def find_largest_container(shapes):
    max_area = 0
    max_area_shape = None

    for shape in shapes:
        if len(shape) == 4:
            vertices = shape.get_vertices()

            area = abs(vertices[0][0]*vertices[1][1] - vertices[0][1]*vertices[1][0]
                     + vertices[1][0]*vertices[2][1] - vertices[1][1]*vertices[2][0]
                     + vertices[2][0]*vertices[3][1] - vertices[2][1]*vertices[3][0]
                     + vertices[3][0]*vertices[0][1] - vertices[3][1]*vertices[0][0])

            if area > max_area:
                max_area = area
                max_area_shape = shape

    return max_area_shape

# Calculates the angle between the two vertices with respect to the first vertex
# Returns angle in degrees.
def calculate_angle(v1, v2):
    # Check horizontal line
    if v1[1] == v2[1]:
        return 0
    # Check vertical line
    if v1[0] == v2[0]:
        return 90
    deltaY = v2[1] - v1[1]
    deltaX = v2[0] - v1[0]
    angle = np.arctan(deltaY/deltaX)
    # Convert angle from radian to degrees
    angle = angle * 57.2957795
    return angle

# Returns thresholded_shapes with corrected vertices
# Same data structure as input linear_shapes
def threshold_shapes(threshold, linear_shapes):
    thresholded_shapes = []
    # Go over all the shapes
    for i, v in enumerate(linear_shapes):
        # Go over all the vertices and threshold them
        shapes = []
        for j, w in enumerate(v):
            v_mod = v_current = v[j]
            v_next = v[(j+1) % len(v)]
            a = calculate_angle(v_current, v_next)

            # Check to see if it can be approximated as a vertical line
            if abs(a) > (90-threshold):
                v_mod = (v_next[0], v_current[1])
            # Check to see if it can be approximated as a horizontal line
            if abs(a) < threshold:
                v_mod = (v_current[0], v_next[1])

            ## print i
            ## print j
            ## print w
            ## print a
            shapes.append(v_mod)
        thresholded_shapes.append(shapes)

    # print 'comparing structures'
    # print linear_shapes[1]
    # print thresholded_shapes[1]

    return thresholded_shapes

def apply_homography(M, v):
    (A, B, C, D, E, F, G, H) = M.T.tolist()[0]
    (x0, y0) = v

    denom = G*x0 + H*y0 + 1
    xp = (A*x0 + B*y0 + C)/denom
    yp = (D*x0 + E*y0 + F)/denom
    return (xp, yp)

def reorder_quadrilater_vertices(vertices):
    # I think this assumes the quadrilateral is convex (but the bounding box
    # always ought to be).
    d = {}
    for v in vertices:
        d[v] = {'left': 0, 'above': 0, 'right': 0, 'below': 0}
        for vc in vertices:
            if v != vc:
                if v[0] < vc[0]: d[v]['left']  += 1
                if v[1] < vc[1]: d[v]['above'] += 1
                if v[0] > vc[0]: d[v]['right'] += 1
                if v[1] > vc[1]: d[v]['below'] += 1

    tl = ['above', 'left']
    bl = ['below', 'left']
    tr = ['above', 'right']
    br = ['below', 'right']

    reordered = []
    for corner in [tl, bl, tr, br]:
        f = lambda r: r[corner[0]] >= 2 and r[corner[1]] >= 2
        reordered.append([v for (v, r) in d.iteritems() if f(r)][0])

    return reordered

def rectify_shapes(img, shapes, ellipses):
    largest = find_largest_container(shapes)

    if not largest:
        return None

    # Order the vertices
    vs = reorder_quadrilater_vertices(largest.get_vertices())

    (x0, y0) = vs[0]
    (x1, y1) = vs[1]
    (x2, y2) = vs[2]
    (x3, y3) = vs[3]

    X0 = X1 = 0
    X2 = X3 = 10
    Y0 = Y2 = 8
    Y1 = Y3 = 0

    g = np.matrix([
        [x0, y0, 1, 0 , 0 , 0, -X0*x0, -X0*y0],
        [0 , 0 , 0, x0, y0, 1, -Y0*x0, -Y0*y0],
        [x1, y1, 1, 0 , 0 , 0, -X1*x1, -X1*y1],
        [0 , 0 , 0, x1, y1, 1, -Y1*x1, -Y1*y1],
        [x2, y2, 1, 0 , 0 , 0, -X2*x2, -X2*y2],
        [0 , 0 , 0, x2, y2, 1, -Y2*x2, -Y2*y2],
        [x3, y3, 1, 0 , 0 , 0, -X3*x3, -X3*y3],
        [0 , 0 , 0, x3, y3, 1, -Y3*x3, -Y3*y3]
    ])
    v = np.matrix([X0, Y0, X1, Y1, X2, Y2, X3, Y3]).T
    M = g.I*v

    # Rebuild new shapes with rectified vertices
    rectified_linear_shapes = []
    for shape in shapes:
        if shape.is_complete():
            new_shape = []
            for v in shape.get_vertices():
                new_shape.append(apply_homography(M, v))
            rectified_linear_shapes.append(new_shape)

    rectified_ellipses = []
    for ellipse in ellipses:
        c, majp, minp = ellipse

        c_h    = apply_homography(M, c)
        majp_h = apply_homography(M, majp)
        minp_h = apply_homography(M, minp)

        majlen = geometry.distance(c_h, majp_h)
        minlen = geometry.distance(c_h, minp_h)

        theta = 0
        dy = majp_h[1] - c_h[1]
        dx = majp_h[0] - c_h[0]
        if dx != 0:
            theta = np.degrees(np.arctan(dy/dx))

        recte = (c_h, (majlen, minlen), theta)
        print recte
        rectified_ellipses.append(recte)

    return (rectified_linear_shapes, rectified_ellipses)
