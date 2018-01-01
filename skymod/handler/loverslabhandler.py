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
from .authenticator.loverslab import LoversLab as LoversLabAuthenticator
from .down.simplehttp import SimpleHttpDownloader

from urllib.parse import urlparse
from tqdm import tqdm
from bs4 import BeautifulSoup as soup

import time

from skymod.cfg import config


class LoversLabHandler(Handler, LoversLabAuthenticator, SimpleHttpDownloader):
    scheme = "ll"

    headers = {"User-Agent": "Modbuild 0.1"}

    def __init__(self):
        self.cfg = config.ll
        super().__init__()

    def fetch(self, uri, filename):
        if super().needs_login():
            super().perform_login(self.cfg, self.headers)

        session = super().getSession()

        parts = urlparse(uri)

        #Get CSRF token
        r = session.get(
            f"https://www.loverslab.com/files/file/{parts.netloc}",
            allow_redirects=True,
            headers=self.headers
        )
        s = soup(r.content, "lxml")

        signoutTag = s.find("ul", id="elUserLink_menu").find("li", attrs={"data-menuitem": "signout"}).find("a")
        signoutUrl = signoutTag["href"]
        csrfToken = urlparse(signoutUrl).query[8:]

        mod_id = f"{parts.netloc}?{parts.query}"

        r = session.get(
            f"https://www.loverslab.com/files/file/{mod_id}&csrfKey={csrfToken}",
            allow_redirects=True,
            headers=self.headers
        )
        if r.status_code != 200:
            raise RuntimeError("Expected first request to return 200. "
                               "Instead got " + str(r.status_code))

        for i in tqdm(range(0, 11), desc=filename + " timeout", unit="Sec"):
            time.sleep(1)
        url = f"https://www.loverslab.com/files/file/{mod_id}&csrfKey={csrfToken}"
        super().download_file(filename, url, self.headers, filename)
