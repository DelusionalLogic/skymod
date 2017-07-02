from .handler import Handler

from urllib.parse import urlparse
from tqdm import tqdm
import requests

import query

from cfg import config

cfg = config.nexus

class NexusHandler(Handler):
    scheme = "nexus"

    headers = {"User-Agent": "Nexus Client v0.53.2"}

    def __init__(self):
        self.session = requests.Session()

        self.initialized = False

    def _perform_login(self, username, password):
        r = self.session.post("http://www.nexusmods.com/skyrim/sessions/?Login", params={"username": username, "password": password}, headers = self.headers)
        if r.status_code != 200:
            raise AuthorizationError("Generic login error")

        r = self.session.get("http://www.nexusmods.com/skyrim/Core/Libs/Flamework/Entities/User", params={"GetCredentials":""}, allow_redirects=True, headers = self.headers)
        if r.status_code != 200:
            raise AuthorizationError("Failed getting credentials (How did that happen?)")

    def fetch(self, uri, filename):
        if not self.initialized:
            self.initialized = True
            if cfg.username == "":
                raise Exception("Nexus username wasn't set. Please set nexus.username and optionally nexus.password")
            password = cfg.password
            if password == "":
                password = query.password("Nexus password: ")
            self._perform_login(cfg.username, password)
        parts = urlparse(uri)
        mod_id = parts.netloc

        r = self.session.get("http://www.nexusmods.com/skyrim/Files/download/" + mod_id, params={"game_id":"110"}, allow_redirects=True, headers = self.headers)
        j = r.json()
        r = self.session.get(j[0]["URI"], allow_redirects=True, headers = self.headers, stream=True)
        total_size = int(r.headers.get("content-length", 0))
        with tqdm(desc=uri, total=total_size, unit='B', unit_scale=True, miniters=1) as bar:
            with open(filename, 'wb') as fd:
                for chunk in r.iter_content(32*1024):
                    bar.update(len(chunk))
                    fd.write(chunk)

