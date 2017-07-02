from path import Path

class SourceLine(object):
    def __init__(self, string):
        self.uri, filename = string.split("::")
        self.filename = Path(filename)

    def get_name(self):
        return self.filename.splitext()[0]

    def get_ext(self):
        return self.filename.splitext()[1]
