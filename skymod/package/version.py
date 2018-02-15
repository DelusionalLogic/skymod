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
from functools import total_ordering


@total_ordering
class Version(object):
    def __init__(self, version_str):
        self.v = [int(p) for p in version_str.split(".")]

    def __lt__(self, other):
        for k, v in enumerate(self.v):
            if k >= len(other.v):
                return False
            if v < other.v[k]:
                return True
            if v > other.v[k]:
                return False
        if len(self.v) < len(other.v):
            return True

    def __eq__(self, other):
        if len(self.v) != len(other.v):
            return False

        for k, v in enumerate(self.v):
            if v != other.v[k]:
                return False
        return True

    def __repr__(self):
        return ".".join(map(str, self.v))
