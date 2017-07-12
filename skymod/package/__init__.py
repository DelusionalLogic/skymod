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
from .version import Version
from .localluaconfigproxy import LocalLuaPackageConfigProxy
from .install_reason import InstallReason
from .sourceline import SourceLine
from .printer import print_local_package

from skymod.config.runtimesandbox import RuntimeSandbox

import yaml

_runtime = RuntimeSandbox()

def load_package(path, pkgsrc, pkgins):
    config = _runtime.load_file(path)
    proxy = LuaPackageConfigProxy(path, config, pkgsrc, pkgins)
    return proxy

def load_local_package(path, pkgsrc, pkgins, metadata_path):
    config = _runtime.load_file(path)
    with open(metadata_path, "r") as infile:
        metadata = yaml.load(infile)
    proxy = LocalLuaPackageConfigProxy(path, config, pkgsrc, pkgins, metadata)
    return proxy
