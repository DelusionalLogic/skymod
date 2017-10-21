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
from skymod.dirhashmap import DirMap

from skymod.cfg import config as cfg


class Downloader(object):
    def __init__(self, cache=None):
        self.handlers = set()
        self.cache = cache or DirMap(cfg.cache.dir)

    def add_handler(self, handler):
        self.handlers.add(handler)

    def fetch_file(self, uri, filename):
        print("Fetching {}".format(filename))
        # Is the uri cached
        if uri in self.cache:
            tqdm.write("{} found in cache".format(uri))
            return (self.cache.get(uri) / "file", filename)

        with self.cache.atomic_add(uri) as dl_cache:
            for handler in self.handlers:
                if handler.accept(uri):
                    handler.fetch(uri, dl_cache / "file")

        return (self.cache.get(uri) / "file", filename)

    def fetch(self, entries):
        files = {}
        for (uri, filename) in entries:
            files[uri] = self.fetch_file(uri, filename)
        return files
