class Box:
    def __init__(self, name, patcher=None, parent=None):
        self.name = name
        self.patcher = patcher
        self.parent = parent

    def __repr__(self):
        return f"Box(name='{self.name}')"

    def __iter__(self):
        yield self
        if self.patcher:
            yield from iter(self.patcher)


class Patcher:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.boxes = []

    def __repr__(self):
        return f"Patcher(name='{self.name}')"

    def __iter__(self):
        yield self
        for box in self.boxes:
            yield from iter(box)

    def add(self, name):
        self.boxes.append(Box(name, parent=self))
        return self.boxes[-1]

    def add_subpatcher(self, name):
        box = Box(name, parent=self)
        box.patcher = Patcher(f"subpatcher-{name}", parent=box)
        self.boxes.append(box)
        return self.boxes[-1]

    def print_tree(self, level=0):
        space = 4 * " "
        indent = space * level
        print(indent + repr(self))
        if self.boxes:
            level += 1
            indent = space * level
            for b in self.boxes:
                print(indent + repr(b))
                if b.patcher:
                    b.patcher.print_tree(level=level+1)

    def check_parenthood(self, level=0):
        if self.boxes:
            for b in self.boxes:
                assert b.parent == self
                if b.patcher:
                    assert b.patcher.parent == b
                    b.patcher.print_tree(level=level+1)


def test_tree():
    p = Patcher('root')
    p.add('phasor~')
    p.add('cycle~')
    sp1 = p.add_subpatcher('p hello')
    sp1.patcher.add("bye")
    sp2 = sp1.patcher.add_subpatcher('p inner')
    sp2.patcher.add("bye2")
    p.add('extra')

    xs = list(p)
    assert xs[-1].name == 'extra'
    p.check_parenthood()
    p.print_tree()


if __name__ == '__main__':
    test_tree()



