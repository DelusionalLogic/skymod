# Copyright 2017 Jesper Jensen (delusionallogic)
#
# This file is part of skymod.
#
# skymod is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# skymod is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with skymod.  If not, see <http://www.gnu.org/licenses/>.
from .handler import Handler

from urllib.parse import urlparse
from tqdm import tqdm
import requests
import skymod.query as query

import time

from skymod.cfg import config
from .errors import AuthorizationError


class LoversLabHandler(Handler):
    scheme = "ll"

    headers = {"User-Agent": "Modbuild 0.1"}

    def __init__(self):
        self.cfg = config.ll
        self.session = requests.Session()

        # Do some lazy initialization to login right before needed, but only
        # once
        self.initialized = False

    def _perform_login(self, username, password):
        data = {
            "ips_username": username,
            "ips_password": password,
            "rememberMe": 0,
            "auth_key": "880ea6a14ea49e853634fbdc5015a024"
        }
        r = self.session.post(
            "https://www.loverslab.com/index.php?app=core&module=global&section=login&do=process",  # noqa
            data=data,
            headers=self.headers
        )
        if r.status_code != 200:
            raise AuthorizationError("Generic login error")

    def fetch(self, uri, filename):
        if not self.initialized:
            self.initialized = True
            if self.cfg.username == "":
                raise Exception(
                    "Loverlab username wasn't set."
                    "Please set ll.username and optionally ll.password"
                )
            password = self.cfg.password
            if password == "":
                password = query.password("LoversLab password: ")
            self._perform_login(self.cfg.username, password)
        parts = urlparse(uri)
        mod_id = parts.netloc

        r = self.session.get(
            "http://www.loverslab.com/files/getdownload/" + mod_id,
            allow_redirects=True,
            headers=self.headers
        )
        while True:
            for i in tqdm(range(0, 30), desc="Timeout", unit="Sec"):
                time.sleep(1)
            r = self.session.get(
                "http://www.loverslab.com/files/getdownload/" + mod_id,
                allow_redirects=True,
                headers=self.headers,
                stream=True
            )
            if r.status_code == 200:
                break
            print(r.status_code)
        total_size = int(r.headers.get("content-length", 0))
        with tqdm(desc=uri, total=total_size, unit='B',
                  unit_scale=True, miniters=1) as bar:
            with open(filename, 'wb') as fd:
                for chunk in r.iter_content(32*1024):
                    bar.update(len(chunk))
                    fd.write(chunk)
