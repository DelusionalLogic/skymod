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
from path import Path

class VirtualFS(object):
    def __init__(self):
        self.map = {}

    def remap(self, from_, to):
        self.map[str(from_)] = to

    def translate(self, path):
        # I can't translate an absolute path. What would that even do?
        assert(not path.isabs())

        # Normalizing is nice
        path_norm = path.normpath()
        # Since we know the path is relative we know that index=0 is empty and
        # index=1 is the first path part
        path_split = path_norm.splitall()
        # I don't think it would make any sense to translate anything besides
        # the first part
        path_split[1] = self.map[path_split[1]]
        translated = Path.joinpath(*path_split)
        return translated
