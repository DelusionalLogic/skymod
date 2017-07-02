from path import Path

class LocalLuaPackageConfigProxy(LuaPackageConfigProxy):
    def __init__(self, path, config, pkgsrc, pkgins, metadata):
        super().__init__(path, config, pkgsrc, pkgins)
        self.metadata = metadata

    @property
    def install_date(self):
        return self.metadata["install_date"]

    @property
    def is_local(self):
        return True
