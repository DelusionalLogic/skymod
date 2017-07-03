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
    def is_local(self):
        return True
