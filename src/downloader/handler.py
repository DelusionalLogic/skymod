from urllib.parse import urlparse

class Handler(object):
    def accept(self, uri):
        return self.scheme == urlparse(uri).scheme
