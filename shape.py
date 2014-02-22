# [(v1, (s1, s2)), (v2, (s3, s4))]
class Shape:
    def __init__(self, s1, s2, v):
        (s1, s2) = sorted((sorted(s1), sorted(s2)))
        self.c = [(v, sorted((s1, s2)))]

    def has_vertex(self, vertex):
        return vertex in [v for v, _ in self.c]

    def has_segment(self, seg):
        seg = sorted(seg)
        for v, ss in self.c:
            if seg in ss:
                return True
        return False

    def add(self, s1, s2, v):
        (s1, s2) = sorted((sorted(s1), sorted(s2)))
        if s1 in self.c[-1][1] or s2 in self.c[-1][1]:
            self.c.append((v, sorted((s1, s2))))
        elif s1 in self.c[0][1] or s2 in self.c[0][1]:
            self.c.insert(0, (v, sorted((s1, s2))))
        else:
            print 'Failed to add'

    def is_complete(self):
        (a, b) = (self.c[0][1][0], self.c[-1][1][0])
        (c, d) = (self.c[0][1][1], self.c[-1][1][1])

        # Must have more than two corners and two of the four line segments at
        # corner nodes must be the same (i.e. 3 unique line segments among
        # them).
        s = set(map(tuple, [a, b, c, d]))
        return len(self.c) > 2 and len(s) == 3

    def get_vertices(self):
        return [v for v, _ in self.c]

    def __iter__(self):
        return iter(self.c)

    def __repr__(self):
        if self.is_complete():
            c = 'C: '
        else:
            c = ''

        ss = ['{V=%s S1=%s S2=%s}' % (str(v), str(s1), str(s2)) for v, (s1, s2) in self.c]
        return '[%s%s]' % (c, ', '.join(ss))

    def __len__(self):
        return len(self.c)

class ShapeList:
    def __init__(self):
        self.shapes = []

    def add(self, s1, s2, v):
        found_home = False

        for shape in self.shapes:
            if shape.has_vertex(v):
                found_home = True
            else:
                has_s1 = shape.has_segment(s1)
                has_s2 = shape.has_segment(s2)
                if has_s1 or has_s2:
                    assert not found_home, 'Should be merging shapes now'
                    shape.add(s1, s2, v)
                    found_home = True

        if not found_home:
            s = Shape(s1, s2, v)
            self.shapes.append(s)

    def delete_shape_with_vertex(self, v):
        for i, shape in enumerate(self.shapes):
            if shape.has_vertex(v):
                del self.shapes[i]
                return

    def __str__(self):
        return str(self.shapes)

    def __iter__(self):
        return iter(self.shapes)

if __name__ == '__main__':
    s1 = ((10, 45), (10, 15))
    s2 = ((15, 10), (45, 10))
    s3 = ((50, 15), (50, 45))
    s4 = ((45, 50), (15, 50))

    v1 = (10, 10)
    v2 = (50, 10)
    v3 = (50, 50)
    v4 = (10, 50)

    c1 = (s1, s2, v1)
    c2 = (s2, s3, v2)
    c3 = (s3, s4, v3)
    c4 = (s4, s1, v4)

    sl = ShapeList()
    sl.add(*c1)
    sl.add(*c1)
    sl.add(*c2)
    sl.add(*c3)
    sl.add(*c4)
    print sl, '\n'
