from .handler import Handler

from urllib.parse import urlparse
from tqdm import tqdm
import requests
import skymod.query as query

import time

from skymod.cfg import config

cfg = config.ll


class LoversLabHandler(Handler):
    scheme = "ll"

    headers = {"User-Agent": "Modbuild 0.1"}

    def __init__(self):
        self.session = requests.Session()

        # Do some lazy initialization to login right before needed, but only
        # once
        self.initialized = False

    def _perform_login(self, username, password):
        r = self.session.post("https://www.loverslab.com/index.php?app=core&module=global&section=login&do=process", data = {"ips_username": username, "ips_password": password, "rememberMe": 0, "auth_key": "880ea6a14ea49e853634fbdc5015a024"}, headers = self.headers)
        if r.status_code != 200:
            raise AuthorizationError("Generic login error")

    def fetch(self, uri, filename):
        if not self.initialized:
            self.initialized = True
            if cfg.username == "":
                raise Exception("Loverlab username wasn't set. Please set ll.username and optionally ll.password")
            password = cfg.password
            if password == "":
                password = query.password("LoversLab password: ")
            self._perform_login(cfg.username, password)
        parts = urlparse(uri)
        mod_id = parts.netloc

        r = self.session.get("http://www.loverslab.com/files/getdownload/" + mod_id, allow_redirects=True, headers = self.headers)
        while True:
            for i in tqdm(range(0, 30), desc="Timeout", unit="Sec"):
                time.sleep(1)
            r = self.session.get("http://www.loverslab.com/files/getdownload/" + mod_id, allow_redirects=True, headers = self.headers, stream=True)
            if r.status_code == 200:
                break
        total_size = int(r.headers.get("content-length", 0))
        with tqdm(desc=uri, total=total_size, unit='B', unit_scale=True, miniters=1) as bar:
            with open(filename, 'wb') as fd:
                for chunk in r.iter_content(32*1024):
                    bar.update(len(chunk))
                    fd.write(chunk)
