from .luaconfigproxy import LuaPackageConfigProxy
from .version import Version
from .localluaconfigproxy import LocalLuaPackageConfigProxy
from .install_reason import InstallReason
from .sourceline import SourceLine

from config.runtimesandbox import RuntimeSandbox

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
