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
from .version import Version
from .sourceline import SourceLine


class LuaPackageConfigProxy(object):
    def __init__(self, path, config, pkgsrc, pkgins):
        self.path = path
        self.config = config
        self.pkgsrc = pkgsrc
        self.pkgins = pkgins / self.name

    @property
    def name(self):
        return self.config.env.name

    @property
    def version(self):
        if not self.config.env.version:
            return Version("1")
        return Version(self.config.env.version)

    @property
    def desc(self):
        if not self.config.env.desc:
            return ""
        return self.config.env.desc

    @property
    def dependecies(self):
        if not self.config.env.depends:
            return []
        return [self.config.env.depends[i] for i in self.config.env.depends]

    def package(self, source_lookup):
        # Assign it to the context, because we don't really want the lua code
        # to know anything about his
        self.config.source_lookup = source_lookup
        return self.config.env.package()

    @property
    def provides(self):
        if not self.config.env.provides:
            return []
        return [self.config.env.provides[i] for i in self.config.env.provides]

    @property
    def sources(self):
        if not self.config.env.sources:
            return []
        return [SourceLine(self.config.env.sources[i]) for i in self.config.env.sources]

    @property
    def conflicts(self):
        if not self.config.env.conflicts:
            return []
        return [self.config.env.conflicts[i] for i in self.config.env.conflicts]

    @property
    def bridges(self):
        if not self.config.env.bridges:
            return []
        b = set()
        for v in [self.config.env.bridges[i] for i in self.config.env.bridges]:
            p = v.split("::")
            b.add( (p[0], p[1]) )
        return b

    @property
    def optdepends(self):
        # @HACK we should be parsing the string here
        if not self.config.env.optdepends:
            return []
        o = []
        for v in [
                    self.config.env.optdepends[i]
                    for i in self.config.env.optdepends
                ]:
            p = v.split("::")
            o.append((p[0], p[1]))
        return o

    @property
    def is_local(self):
        return False

    @property
    def pkgins(self):
        return self.config.pkgins

    @pkgins.setter
    def pkgins(self, value):
        self.config.pkgins = value

    @property
    def pkgsrc(self):
        return self.config.pkgsrc

    @pkgsrc.setter
    def pkgsrc(self, value):
        self.config.pkgsrc = value

    @property
    def pkgdwn(self):
        return self.config.pkgdwn

    @pkgdwn.setter
    def pkgdwn(self, value):
        self.config.pkgdwn = value

    def __str__(self):
        return "{}={}".format(self.name, self.version)

    def __repr__(self):
        return "<{}={}>".format(self.name, self.version)

    def __eq__(self, other):
        if type(other) == str:
            return self.name == other
        return self.name == other.name

    def __hash__(self):
        return self.name.__hash__()

