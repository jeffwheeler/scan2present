import cv2
import itertools
import numpy as np

from shape import ShapeList

#The amount of dilation of the shapes
th=7
BS=151
BSHD=15
kHD=0.13
DSTCONNECT=30

def distance(a, b):
    (ax, ay) = a
    (bx, by) = b

    return np.sqrt((ax-bx)**2+(ay-by)**2)

def threshold(img):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        thresholdType=cv2.THRESH_BINARY_INV, blockSize=BS, C=25)
    # _, thresh = cv2.threshold(gray, 130,255, cv2.THRESH_BINARY_INV)
    k3 = np.ones((3,3),np.uint8)
    k5 = np.ones((5,5),np.uint8)
    k7 = np.ones((7,7),np.uint8)
    kthl = np.ones((th-2,th-2),np.uint8)
    kth= np.ones((th,th),np.uint8)
    g = cv2.erode(cv2.dilate(thresh, kth, iterations=1), kthl, iterations=1)
    # g = cv2.Canny(g, 50, 150, apertureSize=5)

    return g

def threshold_shape_sizes(shapes):
    # Detect if any corners are within a few pixels of each other. If so,
    # we've screwed up somewhere.
    for shape in shapes:
        for v1, v2 in itertools.combinations(shape.get_vertices(), 2):
            if distance(v1, v2) < 10:
                shapes.delete_shape_with_vertex(v1)
                break

def order_shapes(img, shapes):
    pass

def find_largest_container(img, shapes):
    sizes = []
    maxarea = 0
    maxareashape = None
    for shape in shapes:
        if len(shape) == 4:
            vertices=shape.get_vertices()
            # calculate area now
            # print vertices
            
            area = abs(vertices[0][0]*vertices[1][1] - vertices[0][1]*vertices[1][0]
                   + vertices[1][0]*vertices[2][1] - vertices[1][1]*vertices[2][0]
                   + vertices[2][0]*vertices[3][1] - vertices[2][1]*vertices[3][0]
                   + vertices[3][0]*vertices[0][1] - vertices[3][1]*vertices[0][0])
            # print area
            if area > maxarea:
                maxarea = area
                maxareashape = shape
    return maxareashape

def recognize_linear_shapes(img, shapes):
    largest = find_largest_container(img, shapes)
    threshold_shape_sizes(shapes)
    for shape in shapes:
        if shape.is_complete():
            # Recognize the shapes
            if len(shape) == 3:
                color = (255, 0, 0)
            elif len(shape) == 4:
                color = (0, 255, 0)
            elif len(shape) > 4:
                color = (255, 255, 0)

            # Add the first vertex to the end, so I can iterate over
            # consecutive pairs and nicely get the ordered shape
            vs = shape.get_vertices()
            for i, v in enumerate(vs):
                cv2.line(img, v, vs[(i+1)%len(vs)], color, 2)
                color = (color[0], color[1], color[2] + np.uint8(255./(len(shape)-1)))

    color = (0, 0, 255)
    # Draw the biggest quadrilateral
    if largest:
        vs = largest.get_vertices()
        # print vs
        for i, v in enumerate(vs):
            cv2.line(img, v, vs[(i+1)%len(vs)], color, 2)

def process(img, g):
    gf = np.float32(g)
    
    dst = cv2.cornerHarris(gf,th+8,BSHD,kHD)
    dst = cv2.dilate(dst,None)

    g[dst>0.02*dst.min()]=0
    
    line_endpoints = []

    x = 0

    contours, hierarchy = cv2.findContours(g, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        if cv2.contourArea(c) > 100:
            ellipse = cv2.fitEllipse(c)

            (x,y), (minor_axis, major_axis), angle = ellipse
            ecc = major_axis/minor_axis

            if ecc > 5:
                if abs(angle-90) > 30:
                    # Vertical
                    # cv2.drawContours(img, c, -1, (0, 0, 255), 1)

                    # Find extrema points
                    # via http://opencv-python-tutroals.readthedocs.org/en/...
                    #       latest/py_tutorials/py_imgproc/py_contours/...
                    #       py_contour_properties/py_contour_properties.html
                    topmost = tuple(c[c[:,:,1].argmin()][0])
                    bottommost = tuple(c[c[:,:,1].argmax()][0])

                    line_endpoints.append((topmost, bottommost))

                    # cv2.line(img, topmost, bottommost, (255, 255, 0), 1)
                else:
                    # Horizontal
                    # cv2.drawContours(img, c, -1, (0, 255, 255), 1)

                    leftmost = tuple(c[c[:,:,0].argmin()][0])
                    rightmost = tuple(c[c[:,:,0].argmax()][0])

                    line_endpoints.append((leftmost, rightmost))

                    # cv2.line(img, leftmost, rightmost, (0, 255, 255), 1)
            elif ecc < 1.5: # Need to draw pretty carefully to not pass 1.5
                # Circles
                # cv2.drawContours(img, c, -1, (255, 0, 0), 1)
                cv2.ellipse(img, ellipse, (0, 255, 255), 2)
            else:
                # Some weird line shape
                #cv2.drawContours(img, c, -1, (255, 0, x), 2)
                x += 125
                pass
        else:
            # Small objects
            # cv2.drawContours(img, c, -1, (0, 255, 0), 1)
            pass

    linear_shapes = ShapeList()

    for (a, b) in line_endpoints:
        cv2.line(img, a, b, (255, 255, 0), 1)
        for (c, d) in line_endpoints:
            if (a, b) != (c, d):
                for (m, n) in itertools.combinations([a, b, c, d], 2):
                    if distance(m, n) < DSTCONNECT:
                        # Likely found two line segments that should connect
                        
                        (x1, y1) = np.float32(a)
                        (x2, y2) = np.float32(b)
                        (x3, y3) = np.float32(c)
                        (x4, y4) = np.float32(d)

                        # Detect the intersection point (surely can be nicer!)
                        px_n = np.linalg.det(np.array(
                            [[np.linalg.det(np.array([[x1, y1], [x2, y2]])),
                              np.linalg.det(np.array([[x1, 1 ], [x2, 1 ]]))],
                             [np.linalg.det(np.array([[x3, y3], [x4, y4]])),
                              np.linalg.det(np.array([[x3, 1 ], [x4, 1 ]]))]]))
                        py_n = np.linalg.det(np.array(
                            [[np.linalg.det(np.array([[x1, y1], [x2, y2]])),
                              np.linalg.det(np.array([[y1, 1 ], [y2, 1 ]]))],
                             [np.linalg.det(np.array([[x3, y3], [x4, y4]])),
                              np.linalg.det(np.array([[y3, 1 ], [y4, 1 ]]))]]))
                        p_d  = np.linalg.det(np.array(
                            [[np.linalg.det(np.array([[x1, 1 ], [x2, 1]])),
                              np.linalg.det(np.array([[y1, 1 ], [y2, 1 ]]))],
                             [np.linalg.det(np.array([[x3, 1 ], [x4, 1]])),
                              np.linalg.det(np.array([[y3, 1 ], [y4, 1 ]]))]]))

                        # Should probably validate that there is an intersection
                        # before crashing here by division with zero. It is
                        # extraordinarily unlikely, though.

                        p = tuple(np.int32((px_n/p_d, py_n/p_d)))
                        if distance(m, p) < DSTCONNECT and distance(n, p) < DSTCONNECT:
                            cv2.line(img, m, p, (0, 0, 255), 1)
                            cv2.line(img, n, p, (0, 0, 255), 1)
                            # linear_shapes.add((a, b), (c, d), extra=p)
                            linear_shapes.add((a, b), (c, d), p)

    # Homography work
    recognize_linear_shapes(img, linear_shapes)
    rectified_shapes = rectify_shapes(img, linear_shapes)
    
    return (img, rectified_shapes)

def rectify_shapes(img, shapes):
    largest=find_largest_container(img, shapes)
    if not largest:
        return None
    print largest.get_vertices()
    # Read the vertices
    (A2, B2) = largest.get_vertices()[0]
    (A1, B1) = largest.get_vertices()[1]
    (A0, B0) = largest.get_vertices()[2]
    (A3, B3) = largest.get_vertices()[3]
    # Arrange the vertices in top-left, bottom-left, bottom-right, top-right order
    Dist0=A0*A0+B0*B0
    Dist1=A1*A1+B1*B1
    Dist2=A2*A2+B2*B2
    Dist3=A3*A3+B3*B3

    minDist = 10000000
    maxDist = 0
    
    # Re-arranges the rectangle in required order

    # Set top-left
    if Dist0 < minDist:
        (x0, y0) = (A0, B0)
        minDist = Dist0
    if Dist1 < minDist:
        (x0, y0) = (A1, B1)
        minDist = Dist1
    if Dist2 < minDist:
        (x0, y0) = (A2, B2)
        minDist = Dist2
    if Dist3 < minDist:
        (x0, y0) = (A3, B3)
        minDist = Dist3

    # Set bottom-right
    if Dist0 > maxDist:
        (x2, y2) = (A0, B0)
        maxDist = Dist0
    if Dist1 > maxDist:
        (x2, y2) = (A1, B1)
        maxDist = Dist1
    if Dist2 > maxDist:
        (x2, y2) = (A2, B2)
        maxDist = Dist2
    if Dist3 > maxDist:
        (x2, y2) = (A3, B3)
        maxDist = Dist3
        
    # Set bottom-left
    if B0>y0 and A0<x2:
        (x1, y1) = (A0, B0)  
    if B1>y0 and A1<x2:
        (x1, y1) = (A1, B1)
    if B2>y0 and A2<x2:
        (x1, y1) = (A2, B2)
    if B3>y0 and A3<x2:
        (x1, y1) = (A3, B3)

    # Set top-right
    if A0>x0 and B0<y2:
        (x3, y3) = (A0, B0)
    if A1>x0 and B1<y2:
        (x3, y3) = (A1, B1)
    if A2>x0 and B2<y2:
        (x3, y3) = (A2, B2)
    if A3>x0 and B3<y2:
        (x3, y3) = (A3, B3)

    k0 = k1 = k2 = k3 = 0.5

    # Shuffle the character
    (xtemp, ytemp) = (x3, y3)
    (x3, y3) = (x2, y2)
    (x2, y2) = (xtemp, ytemp)

    # Modified Transformation
    X0 = X1 = k0*x0 + k1*x1
    X2 = X3 = k2*x2 + k3*x3
    Y0 = Y2 = k0*y0 + k2*y2
    Y1 = Y3 = k1*y1 + k3*y3

    # Define the matrix as given in the paper
    R1 = [x0, y0, 1, 0, 0, 0, -X0*x0, -X0*y0]
    R2 = [0, 0, 0, x0, y0, 1, -Y0*x0, -Y0*y0]
    R3 = [x1, y1, 1, 0, 0, 0, -X1*x1, -X1*y1]
    R4 = [0, 0, 0, x1, y1, 1, -Y1*x1, -Y1*y1]
    R5 = [x2, y2, 1, 0, 0, 0, -X2*x2, -X2*y2]
    R6 = [0, 0, 0, x2, y2, 1, -Y2*x2, -Y2*y2]
    R7 = [x3, y3, 1, 0, 0, 0, -X3*x3, -X3*y3]
    R8 = [0, 0, 0, x3, y3, 1, -Y3*x3, -Y3*y3]

    g = np.matrix([R1, R2, R3, R4, R5, R6, R7, R8])
    v = np.matrix([[X0], [Y0], [X1], [Y1], [X2], [Y2], [X3], [Y3]])
    coeff = g.I*v 
    A = coeff[0].item()
    B = coeff[1].item()
    C = coeff[2].item()
    D = coeff[3].item()
    E = coeff[4].item()
    F = coeff[5].item()
    G = coeff[6].item()
    H = coeff[7].item()

    rectified_shapes = []

    for i, shape in enumerate(shapes):
        if shape.is_complete():
            new_shape = []
            for vertex in shape.get_vertices():
                (xold, yold) = vertex
                Xnew = ( A*xold + B*yold + C ) / (G*xold + H*yold + 1)
                Ynew = ( D*xold + E*yold + F ) / (G*xold + H*yold + 1)
                Xnorm = round((Xnew-X0)*(10/(X3-X0)),3)
                Ynorm = 8-round((Ynew-Y0)*(8/(Y3-Y0)), 3)
                new_shape.append((Xnorm,Ynorm))
            rectified_shapes.append(new_shape)

    return rectified_shapes

def prepare_img(input_path, output_path):
    img = cv2.imread(input_path)
    img = np.rot90(img, 3)

    img = cv2.resize(img, (0, 0), fx=0.3, fy=0.3)
    thresh = threshold(img)
    
    (img, rectified_shapes) = process(img, thresh)

    cv2.imwrite(output_path, img)

    return rectified_shapes

def test_img(filename):
    img = cv2.imread(filename)
    # img = np.rot90(img, 3)
    # img = cv2.resize(img, (0,0), fx=0.3, fy=0.3)
    img = cv2.resize(img, (0,0), fx=0.2, fy=0.2)
    thresh = threshold(img)

    process(img, thresh)

    cv2.imshow(filename, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    test_img('input-images/uploaded/test715.jpg')
    # test_img('input-images/training/square.jpg')
    # test_img('input-images/slides/slide1.jpg')
    # test_img('input-images/slides/slide2.jpg')
    # test_img('input-images/slides/slide3.jpg')
    # test_img('input-images/slides/slide4.jpg')
    # test_img('input-images/slides/slide5.jpg')
    # test_img('input-images/slides/slide6.jpg')
    # test_img('input-images/slides/slide7.jpg')
    # test_img('input-images/slides/slide8.jpg')
    # test_img('input-images/slides/slide9.jpg')
    # test_img('input-images/slides/slide10.jpg')
    # test_img('input-images/slides/slide11.jpg')
    # test_img('input-images/slides/slide12.jpg') # Need help on thresholding
    # test_img('input-images/slides/slide13.jpg')
