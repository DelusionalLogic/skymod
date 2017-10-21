import requests


class SessionFactory(object):
    def __init__(self):
        self._session = None

    def getSession(self):
        if self._session is None:
            self._session = requests.Session()
        return self._session
