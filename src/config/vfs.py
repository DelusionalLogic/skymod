from path import Path

class VirtualFS(object):
    def __init__(self):
        self.map = {}

    def remap(self, from_, to):
        self.map[str(from_)] = to

    def translate(self, path):
        # I can't translate an absolute path. What would that even do?
        assert(not path.isabs())

        # Normalizing is nice
        path_norm = path.normpath()
        # Since we know the path is relative we know that index=0 is empty and
        # index=1 is the first path part
        path_split = path_norm.splitall()
        # I don't think it would make any sense to translate anything besides
        # the first part
        path_split[1] = self.map[path_split[1]]
        translated = Path.joinpath(*path_split)
        return translated
