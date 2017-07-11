from .packagerepo import PackageRepo
from .errors import AlreadyInstalledError
import skymod.package

from datetime import datetime

from skymod.cfg import config as cfg

import yaml
from path import Path


class LocalPackageRepo(PackageRepo):
    def __init__(self, root):
        super().__init__(root)

    def _load_package(self, path):
        pkgins = cfg.mo.mods_dir
        pkgsrc = cfg.source.dir

        config = skymod.package.load_local_package(
            path / "modbuild.lua",
            pkgsrc,
            pkgins,
            path / "meta.yml"
        )

        return config

    def add_package(self, reason, package):
        package_dir = self.root / package.name
        if package_dir.exists():
            raise AlreadyInstalledError("Package already installed " + package.name)
        package_dir.makedirs()

        package.path.copy(package_dir)

        with open(package_dir / "meta.yml", "w") as outfile:
            yaml.dump({
                "install_date": datetime.now(),
                "reason": reason.value,
            }, outfile)

    def remove_package(self, package):
        package_dir = self.root / package.name
        if not package_dir.exists():
            raise AlreadyInstalledError("Package not installed")
        package_dir.rmtree()

    def get_all_packages(self):
        files = set() 
        for p in self.root.dirs():
            if p.name.startswith("."):
                continue
            files.add(self._load_package(p))
        return files
