import cv2
import itertools
import numpy as np

from grouplist import GroupList

def distance(a, b):
    (ax, ay) = a
    (bx, by) = b

    return np.sqrt((ax-bx)**2+(ay-by)**2)

def threshold(img):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    thresh = 255-cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        thresholdType=cv2.THRESH_BINARY, blockSize=151, C=50)

    k5 = np.ones((5,5),np.uint8)
    k7 = np.ones((7,7),np.uint8)
    g = cv2.erode(cv2.dilate(thresh, k7, iterations=1), k5, iterations=1)
    # g = cv2.Canny(g, 50, 150, apertureSize=5)
    return g

def threshold_shape_sizes(shapes):
    # Detect if any corners are within a few pixels of each other. If so,
    # we've screwed up somewhere.
    for shape in shapes:
        corners = shape['extra']
        for (c1, c2) in itertools.combinations(corners, 2):
            if distance(c1, c2) < 10:
                shapes.remove(list(shape['data'])[0])
                break

def recognize_linear_shapes(img, shapes):
    threshold_shape_sizes(shapes)
    for shape in shapes:
        sides = shape['data']
        corners = list(shape['extra'])

        if len(sides) == len(corners):
            # Recognize the shapes
            if len(sides) == 3:
                cv2.line(img, corners[0], corners[1], (255, 0, 0), 2)
                cv2.line(img, corners[1], corners[2], (255, 0, 0), 2)
                cv2.line(img, corners[0], corners[2], (255, 0, 0), 2)
            elif len(sides) == 4:
                cv2.line(img, corners[0], corners[1], (0, 255, 0), 2)
                cv2.line(img, corners[0], corners[2], (0, 255, 0), 2)
                cv2.line(img, corners[0], corners[3], (0, 255, 0), 2)
                cv2.line(img, corners[1], corners[2], (0, 255, 0), 2)
                cv2.line(img, corners[1], corners[3], (0, 255, 0), 2)
                cv2.line(img, corners[2], corners[3], (0, 255, 0), 2)


def process(img, g):
    gf = np.float32(g)

    dst = cv2.cornerHarris(gf,7,15,0.04)
    dst = cv2.dilate(dst,None)
    g[dst>0.05*dst.max()]=0

    line_endpoints = []
    linear_shapes = GroupList()

    contours, hierarchy = cv2.findContours(g, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        if cv2.contourArea(c) > 50:
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
                # cv2.drawContours(img, c, -1, (0, 255, 0), 1)
                pass
        else:
            # Small objects
            # cv2.drawContours(img, c, -1, (0, 255, 0), 1)
            pass

    for (a, b) in line_endpoints:
        cv2.line(img, a, b, (255, 255, 0), 1)
        for (c, d) in line_endpoints:
            if (a, b) != (c, d):
                for (m, n) in itertools.combinations([a, b, c, d], 2):
                    if distance(m, n) < 20:
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
                        # before crashing here. It is extraordinarily unlikely,
                        # though.

                        p = tuple(np.int32((px_n/p_d, py_n/p_d)))
                        if distance(m, p) < 20 and distance(n, p) < 20:
                            cv2.line(img, m, p, (0, 0, 255), 1)
                            cv2.line(img, n, p, (0, 0, 255), 1)
                            linear_shapes.add((a, b), (c, d), extra=p)

    recognize_linear_shapes(img, linear_shapes)

    return img

def test_img(filename):
    img = cv2.imread(filename)

    img = cv2.resize(img, (0,0), fx=0.2, fy=0.2)
    thresh = threshold(img)
    img = process(img, thresh)

    cv2.imshow(filename, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    test_img('input-images/training/square.jpg')
    test_img('input-images/slides/slide1.jpg')
    # test_img('input-images/slides/slide2.jpg')
    # test_img('input-images/slides/slide3.jpg')
    # test_img('input-images/slides/slide4.jpg')
    # test_img('input-images/slides/slide5.jpg')
    # test_img('input-images/slides/slide6.jpg')
    test_img('input-images/slides/slide7.jpg')
    # test_img('input-images/slides/slide8.jpg')
    # test_img('input-images/slides/slide9.jpg')
    # test_img('input-images/slides/slide10.jpg')
    test_img('input-images/slides/slide11.jpg')
