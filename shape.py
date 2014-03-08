def sorted_segments(s1, s2):
    (s1, s2) = (tuple(sorted(s1)), tuple(sorted(s2)))
    return tuple(sorted((s1, s2)))

# [(v1, (s1, s2)), (v2, (s3, s4))]
class Shape:
    def __init__(self, s1, s2, v):
        self.c = [(v, sorted_segments(s1, s2))]

    def has_vertex(self, vertex):
        return vertex in [v for v, _ in self.c]

    def has_segment(self, seg):
        seg = tuple(sorted(seg))
        for v, ss in self.c:
            if seg in ss:
                return True
        return False

    def add(self, s1, s2, v):
        assert not self.is_complete()

        if self.goes_to_head(s1, s2, v):
            self.c.append((v, sorted_segments(s1, s2)))
        elif self.goes_to_tail(s1, s2, v):
            self.c.insert(0, (v, sorted_segments(s1, s2)))
        else:
            print 'Failed to add'

    def goes_to_head(self, s1, s2, v):
        assert not self.is_complete()

        (s1, s2) = sorted_segments(s1, s2)
        return s1 in self.c[-1][1] or s2 in self.c[-1][1]

    def goes_to_tail(self, s1, s2, v):
        assert not self.is_complete()

        (s1, s2) = sorted_segments(s1, s2)
        return s1 in self.c[0][1] or s2 in self.c[0][1]

    def can_add(self, s1, s2, v):
        if self.has_vertex(v) or self.is_complete():
            return False
        else:
            return self.has_segment(s1) or self.has_segment(s2)

    def is_complete(self):
        (a, b) = (self.c[0][1][0], self.c[-1][1][0])
        (c, d) = (self.c[0][1][1], self.c[-1][1][1])

        # Must have more than two corners and two of the four line segments at
        # end corner nodes must be the same (i.e. 3 unique line segments among
        # them).
        s = set(map(tuple, [a, b, c, d]))
        return len(self.c) > 2 and len(s) == 3

    def area(self):
        if self.is_complete():
            # Form vectors a, b, c, etc. such that a+b+c+...=0
            return 0
        else:
            print 'Called area() on incomplete shape'
            return -1

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
        found_home = None

        for shape in self.shapes:
            if shape.has_vertex(v):
                # Already added this vertex
                found_home = shape
            elif shape.can_add(s1, s2, v):
                if found_home:
                    # We need to merge the shape we just found with the one
                    # that we had found previously (stored in 'found_home')
                    if not found_home.is_complete():
                        self.merge_shapes(found_home, shape)
                else:
                    shape.add(s1, s2, v)
                    found_home = shape

        if not found_home:
            s = Shape(s1, s2, v)
            self.shapes.append(s)

    def merge_shapes(self, shape1, shape2):
        print 'Merging shapes'

        assert not shape1.is_complete()
        assert not shape2.is_complete()

        sh2_head_v, sh2_head_segs = shape2.c[0]
        sh2_tail_v, sh2_tail_segs = shape2.c[-1]

        if shape1.can_add(sh2_head_segs[0], sh2_head_segs[1], sh2_head_v):
            # Add starting at the head
            for sh2_v, (sh2_seg1, sh2_seg2) in shape2:
                shape1.add(sh2_seg1, sh2_seg2, sh2_v)
        elif shape1.can_add(sh2_tail_segs[0], sh2_tail_segs[1], sh2_tail_v):
            # Add starting at tail
            for sh2_v, (sh2_seg1, sh2_seg2) in reversed(shape2):
                shape1.add(sh2_seg1, sh2_seg2, sh2_v)
        else:
            assert False, 'Couldn\'t merge shapes'

        # Find shape2, delete it from the list of shapes
        self.shapes.remove(shape2)

    def delete_shape_with_vertex(self, v):
        for i, shape in enumerate(self.shapes):
            if shape.has_vertex(v):
                del self.shapes[i]
                return

    def __str__(self):
        return str(self.shapes)

    def __iter__(self):
        return iter(self.shapes)

    def __len__(self):
        return len(self.shapes)

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
    sl.add(*c3)
    sl.add(*c4)
    sl.add(*c2)
    print sl, '\n'
