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
import hashlib
from contextlib import contextmanager


class DirMap(object):
    def __init__(self, container_dir):
        self.container_dir = container_dir

        # Transaction stuff

        # Since no SHA-1 hash is TEMP we can safely use that as a temp dir name
        # in tree
        self.temp = self.container_dir / "TEMP"
        # Set when we know where the destination of a current transaction is
        # going. If this is not None a transaction is running
        self.transaction_dest = None
        # Create the container dir if it doesn't exist
        if not self.container_dir.exists():
            self.container_dir.mkdir()

    def _get_path_safe(self, key):
        key_hash = hashlib.sha1(key.encode()).hexdigest()
        key_path = self.container_dir / key_hash
        return key_path

    def has_key(self, key):
        return self.__contains__(key)

    def __contains__(self, key):
        key_path = self._get_path_safe(key)
        if key_path.exists():
            return True
        return False

    def alloc(self, key):
        if key in self:
            raise KeyError("{} already in map".format(key))

        self.transaction_dest = self._get_path_safe(key)
        if self.temp.exists():
            self.temp.rmtree()
        self.temp.mkdir()
        return self.temp

    def clear(self):
        assert(self.transaction_dest is None)
        for d in self.container_dir.dirs():
            d.rmtree()

    def abort(self):
        self.temp.rmtree()
        self.transaction_dest = None

    def commit(self):
        self.temp.rename(self.transaction_dest)
        self.transaction_dest = None

    @contextmanager
    def atomic_add(m, key):
        h = m.alloc(key)
        try:
            yield h
        except Exception:
            m.abort()
            raise
        m.commit()

    def get(self, key):
        if key not in self:
            raise KeyError("{} not in map".format(key))

        key_path = self._get_path_safe(key)
        return key_path

    def remove(self, key):
        key_path = self._get_path_safe(key)
        key_path.rmtree()
