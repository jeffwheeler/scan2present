import cv2
import numpy as np

def threshold(img):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    thresh = 255-cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        thresholdType=cv2.THRESH_BINARY, blockSize=151, C=50)

    k5 = np.ones((5,5),np.uint8)
    k7 = np.ones((7,7),np.uint8)
    g = cv2.erode(cv2.dilate(thresh, k7, iterations=1), k5, iterations=1)
    # g = cv2.Canny(g, 50, 150, apertureSize=5)
    return g

def process(g, img):
    gf = np.float32(g)
    dst = cv2.cornerHarris(gf,7,15,0.04)
    dst = cv2.dilate(dst,None)
    g[dst>0.05*dst.max()]=0

    contours, hierarchy = cv2.findContours(g, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    for c in contours:
        if cv2.contourArea(c) > 50:
            ellipse = cv2.fitEllipse(c)

            (x,y), (minor_axis, major_axis), angle = ellipse
            ecc = major_axis/minor_axis

            print angle
            if ecc > 5:
                if abs(angle-90) > 30:
                    cv2.drawContours(img, c, -1, (0, 0, 255), 1)
                else:
                    cv2.drawContours(img, c, -1, (0, 255, 255), 1)
            else:
                cv2.drawContours(img, c, -1, (255, 0, 0), 1)
        else:
            cv2.drawContours(img, c, -1, (0, 255, 0), 1)

    return img

def test_img(filename):
    img = cv2.imread(filename)
    # img = cv2.imread('input-images/training/square.jpg')

    img = cv2.resize(img, (0,0), fx=0.2, fy=0.2)
    thresh = threshold(img)
    img = process(thresh, img)

    cv2.imshow(filename, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    test_img('input-images/training/square.jpg')
    test_img('input-images/slides/slide1.jpg')
    test_img('input-images/slides/slide11.jpg')
