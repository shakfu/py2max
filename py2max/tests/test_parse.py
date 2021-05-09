# test deeply nested structure and a recursive function to visit each node

d = {
    'patcher': {
        'name': 'patcher',
        'boxes' : [
            {
                'box': {
                    'name': 'patcher.box[0]',
                }
            },
            {
                'box': {
                    'name': 'patcher.box[1]',
                    'patcher': {
                        'name': 'patcher.box[1].patcher',
                        'boxes': [
                            {
                                'box': {
                                    'name': 'patcher.box[1].patcher.box[0]',
                                    'patcher': {
                                        'name': 'patcher.box[1].patcher.box[0].patcher',
                                        'boxes': [
                                            {
                                                'box': {
                                                    'name': 'patcher.box[1].patcher.box[0].patcher.box[0]'
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        ]
                    }
                }
            },
        ],
    }
}

class Patcher:
    def __init__(self):
        self.name = None
        self.boxes = []
        self.lines = []
        self._boxes = []
        self._lines = []

class Box:
    def __init__(self):
        self.name = None
        self.patcher = None
    

p = Patcher()
p.__dict__.update(d['patcher'])

for box_dict in p.boxes:
    box = box_dict['box']
    b = Box()
    b.__dict__.update(box)
    p._boxes.append(b)

def visit(parent):
    print(parent['name'])
    for box_dict in parent['boxes']:
        box = box_dict['box']
        print(box['name'])
        if 'patcher' in box:
            visit(box['patcher'])

root = d['patcher']
visit(root)
