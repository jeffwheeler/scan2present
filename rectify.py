import itertools
import numpy as np

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

def rectify_shapes(img, shapes):
    largest = find_largest_container(shapes)

    if not largest:
        return None

    # Order the vertices
    vs = largest.get_vertices()

    vs = reorder_quadrilater_vertices(vs)

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

    (A, B, C, D, E, F, G, H) = M.T.tolist()[0]

    # Rebuild new shapes with rectified vertices
    rectified_shapes = []
    for shape in shapes:
        if shape.is_complete():
            new_shape = []
            for (xorig, yorig) in shape.get_vertices():
                denom = G*xorig + H*yorig + 1
                xp = (A*xorig + B*yorig + C)/denom
                yp = (D*xorig + E*yorig + F)/denom
                new_shape.append((xp, yp))
            rectified_shapes.append(new_shape)

    return rectified_shapes
