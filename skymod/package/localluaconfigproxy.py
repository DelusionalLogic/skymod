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
from .luaconfigproxy import LuaPackageConfigProxy
from .install_reason import InstallReason


class LocalLuaPackageConfigProxy(LuaPackageConfigProxy):
    def __init__(self, path, config, pkgsrc, pkgins, metadata):
        super().__init__(path, config, pkgsrc, pkgins)
        self.metadata = metadata

    @property
    def install_date(self):
        return self.metadata["install_date"]

    @property
    def reason(self):
        return InstallReason(self.metadata["reason"])

    @property
    def priority(self):
        if "priority" not in self.metadata:
            return 0
        return self.metadata["priority"]

    @property
    def is_local(self):
        return True

    def __lt__(self, other):
        return self.priority < other.priority
