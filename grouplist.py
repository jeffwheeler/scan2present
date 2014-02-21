# [{'data': [a', 'b', 'c'], 'extra': []}, {'data': ['d', 'e'], 'extra': []}]
class GroupList:
    def __init__(self):
        self.c = []

    def add(self, a, b, extra=None):
        found_home = False
        for x in self.c:
            if a in x['data'] or b in x['data']:
                x['data'].add(a)
                x['data'].add(b)

                if extra:
                    x['extra'].add(extra)

                found_home = True
        if not found_home:
            e = None
            if extra:
                e = set([extra])
            else:
                e = set([])
            self.c.append({'data': set([a, b]), 'extra': e})

    def __iter__(self):
        return iter(self.c)

if __name__ == '__main__':
    print 'Testing GroupList'
    g = GroupList()
    g.add(1, 2, extra='a')
    g.add(1, 3)
    g.add(4, 5, extra='c')
    g.add(6, 5, extra='d')
    print g.c
