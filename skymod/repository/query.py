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
from skymod.package import Version

from enum import Enum
import re

query_re = re.compile("(?P<name>[a-zA-Z0-9-_]{2,})(?:(?P<compar>[<>]=?|=)(?P<version>[0-9.]+))?$")

class Mod(Enum):
    ANY = ""
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    EQ = "="


class Query(object):
    def __init__(self, target_str):
        match = query_re.match(target_str)
        if match == None:
            raise MalformedQueryError("Query did not conform")
        self.name = match.group("name")
        version_str = match.group("version")
        self.version = Version(version_str) if version_str != None else None

        try:
            self.mod = {
                    None: Mod.ANY,
                    "<": Mod.LT,
                    "<=": Mod.LE,
                    ">": Mod.GT,
                    ">=": Mod.GE,
                    "=": Mod.EQ,
            }[match.group("compar")]
        except KeyError:
            raise

    def _ver_match(self, version):
        if self.mod == Mod.ANY:
            return True
        elif self.mod == Mod.LT:
            return version < self.version
        elif self.mod == Mod.LE:
            return version <= self.version
        elif self.mod == Mod.GT:
            return version > self.version
        elif self.mod == Mod.GE:
            return version >= self.version
        elif self.mod == Mod.EQ:
            return version == self.version
        else:
            raise Exception("Unknown version mod")

    def matches(self, config):
        if self.name == config.name:
            return self._ver_match(config.version)

        for p in config.provides:
            name, *rest = p.split("=")
            ver = rest[0] if rest else None
            if name == self.name:
                if ver == None:
                    return True
                return self._ver_match(Version(ver))
        return False

    def __repr__(self):
        return "{}{}{}".format(self.name, self.mod.value or "", self.version or "")

