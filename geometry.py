import numpy as np

def distance(a, b):
    (ax, ay) = a
    (bx, by) = b

    return np.sqrt((ax-bx)**2+(ay-by)**2)
