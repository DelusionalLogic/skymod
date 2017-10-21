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
from .sessionfactory import SessionFactory
from .authenticator.nexus import Nexus as NexusAuthenticator

from urllib.parse import urlparse
from tqdm import tqdm

from skymod.cfg import config


class NexusHandler(Handler, NexusAuthenticator):
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
        j = r.json()
        r = session.get(
            j[0]["URI"],
            allow_redirects=True,
            headers=self.headers,
            stream=True
        )
        total_size = int(r.headers.get("content-length", 0))
        with tqdm(desc=uri, total=total_size, unit='B',
                  unit_scale=True, miniters=1) as bar:
            with open(filename, 'wb') as fd:
                for chunk in r.iter_content(32*1024):
                    bar.update(len(chunk))
                    fd.write(chunk)
