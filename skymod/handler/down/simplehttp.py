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
from tqdm import tqdm

from ..sessionfactory import SessionFactory


class SimpleHttpDownloader(SessionFactory):
    def __init__(self):
        super().__init__()

    def download_file(self, name, url, headers, filename):
        r = super().getSession().get(
            url,
            allow_redirects=True,
            headers=headers,
            stream=True
        )

        if r.status_code != 200:
            raise RuntimeError(
                "Failed downloading file due to non 200 return code. "
                "Return code was " + str(r.status_code)
            )

        total_size = int(r.headers.get("content-length", 0))
        with tqdm(desc=name, total=total_size, unit='B',
                  unit_scale=True, miniters=1) as bar:
            with open(filename, 'wb') as fd:
                for chunk in r.iter_content(32*1024):
                    bar.update(len(chunk))
                    fd.write(chunk)
