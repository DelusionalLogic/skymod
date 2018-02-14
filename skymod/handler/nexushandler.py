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
from .authenticator.nexus import Nexus as NexusAuthenticator
from .down.simplehttp import SimpleHttpDownloader

from urllib.parse import urlparse

from skymod.cfg import config


class NexusHandler(Handler, NexusAuthenticator, SimpleHttpDownloader):
    scheme = "nexus"

    headers = {"User-Agent": "Nexus Client v0.53.2"}

    def __init__(self):
        self.cfg = config.nexus
        super().__init__()

    def fetch(self, uri, filename):
        if super().needs_login():
            super().perform_login(self.cfg, self.headers)
        parts = urlparse(uri)
        mod_id = parts.netloc

        session = super().getSession()

        r = session.get(
            "http://www.nexusmods.com/skyrim/Files/download/" + mod_id,
            params={"game_id": "110"},
            allow_redirects=True,
            headers=self.headers
        )
        if r.status_code != 200:
            raise RuntimeError("Failed downloading " + uri)
        j = r.json()
        super().download_file(uri, j[0]["URI"], self.headers, filename)

    def check(self, uri):
        if super().needs_login():
            super().perform_login(self.cfg, self.headers)
        parts = urlparse(uri)
        mod_id = parts.netloc

        session = super().getSession()

        r = session.get(
            "http://www.nexusmods.com/skyrim/Files/download/" + mod_id,
            params={"game_id": "110"},
            allow_redirects=True,
            headers=self.headers
        )
        if r.status_code != 200:
            raise RuntimeError("Failed requesting " + uri)
        if r.content != b"null":
            return True

        return False
