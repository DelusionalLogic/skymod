from .handler import Handler

class StubHandler(Handler):
    def __init__(self, scheme, message):
        self.scheme = scheme
        self.message = message

    def fetch(self, uri, filename):
        raise Exception(self.message)
