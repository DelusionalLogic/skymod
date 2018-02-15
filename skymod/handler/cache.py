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

from path import Path


class FsCache(object):
    def __init__(self, path):
        self.path = path
        # Make the cache
        if not self.path.exists():
            self.path.makedirs()

    # The filename is only a hint. We are allowed to do return whatever path we
    # want
    def get_path(self, key, filename):
        key_hash = hashlib.md5(key.encode()).hexdigest()
        key_dir = self.path / key_hash
        # Do we already have a value for this key?
        if key_dir.exists():
            # Just get the first file in the dir
            # @WINDOWS probably wont function on windows, since that includes
            # . and ..
            return key_dir.files()[0]
        key_dir.mkdir()
        return key_dir / filename
