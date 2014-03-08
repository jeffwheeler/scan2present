import cv2
import itertools
import numpy as np

from shape import ShapeList
import rectify
import geometry

#The amount of dilation of the shapes
th=7
BS=151
BSHD=15
kHD=0.13
DSTCONNECT=30

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
            if geometry.distance(v1, v2) < 10:
                shapes.delete_shape_with_vertex(v1)
                break

def order_shapes(img, shapes):
    pass

def recognize_linear_shapes(img, shapes):
    largest = rectify.find_largest_container(shapes)
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

def preview_detection(img, g):
    gf = np.float32(g)

    dst = cv2.cornerHarris(gf,th+8,BSHD,kHD)
    dst = cv2.dilate(dst,None)

    g[dst>0.02*dst.min()]=0

    line_endpoints = []
    ellipses = []

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
                # ellipses.append(ellipse)

                maj_x = x + major_axis/2*np.sin(np.radians(angle))
                maj_y = y + major_axis/2*np.cos(np.radians(angle))
                min_x = x + minor_axis/2*np.sin(np.radians(90+angle))
                min_y = y + minor_axis/2*np.cos(np.radians(90+angle))
                cv2.line(img, (int(x), int(y)), (int(maj_x), int(maj_y)), (255, 0, 0), 2)
                cv2.line(img, (int(x), int(y)), (int(min_x), int(min_y)), (0, 255, 0), 2)

                e = ((x, y), (maj_x, maj_y), (min_x, min_y))
                ellipses.append(e)
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
                    if geometry.distance(m, n) < DSTCONNECT:
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
                        if geometry.distance(m, p) < DSTCONNECT and geometry.distance(n, p) < DSTCONNECT:
                            cv2.line(img, m, p, (0, 0, 255), 1)
                            cv2.line(img, n, p, (0, 0, 255), 1)
                            # linear_shapes.add((a, b), (c, d), extra=p)
                            linear_shapes.add((a, b), (c, d), p)

    recognize_linear_shapes(img, linear_shapes)

    return (linear_shapes, ellipses)

def prepare_rectified(img, linear_shapes, ellipses):
    (rect_lin_shapes, rect_ellipses) = rectify.rectify_shapes(img, linear_shapes, ellipses)
    thresholded = rectify.threshold_shapes(15, rect_lin_shapes)
    return (img, (thresholded, rect_ellipses))

def prepare_img(input_path, output_path):
    img = cv2.imread(input_path)
    img = np.rot90(img, 3)

    img = cv2.resize(img, (0, 0), fx=0.3, fy=0.3)
    thresh = threshold(img)

    shapes = preview_detection(img, thresh)

    cv2.imwrite(output_path, img)

    return shapes

def test_img(filename, show=False):
    img = cv2.imread(filename)
    img = np.rot90(img, 3)
    img = cv2.resize(img, (0,0), fx=0.3, fy=0.3)
    # img = cv2.resize(img, (0,0), fx=0.2, fy=0.2)
    thresh = threshold(img)

    linear_shapes, ellipses = preview_detection(img, thresh)
    img, rectified = prepare_rectified(img, linear_shapes, ellipses)

    print 'L=%d, E=%d' % (
        len(filter(lambda s: s.is_complete(), linear_shapes)),
        len(ellipses)
    )

    if show:
        cv2.imshow(filename, img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return rectified

    # import tikz
    # tikz.build_pdf([rectified])

if __name__ == '__main__':
    slides = []
    import os, tikz

    for filename in os.listdir('./input-images/uploaded/'):
        if '.jpg' in filename:
            print filename
            slides.append(test_img(os.path.join('.', 'input-images', 'uploaded', filename)))

    tikz.build_pdf(slides)

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
