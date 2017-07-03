from functools import total_ordering

@total_ordering
class Version(object):
    def __init__(self, version_str):
        self.v = [int(p) for p in version_str.split(".")]

    def __lt__(self, other):
        for k, v in enumerate(self.v):
            if k >= len(other.v):
                return False
            if v < other.v[k]:
                return True
            if v > other.v[k]:
                return False
        if len(self.v) < len(other.v):
            return True

    def __eq__(self, other):
        if len(self.v) != len(other.v):
            return False

        for k, v in enumerate(self.v):
            if v != other.v[k]:
                return False
        return True

    def __repr__(self):
        return ".".join(map(str, self.v))

