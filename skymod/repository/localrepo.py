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
from datetime import datetime

import yaml

import skymod.package
from skymod.cfg import config as cfg

from .errors import AlreadyInstalledError
from .packagerepo import PackageRepo


class LocalPackageRepo(PackageRepo):
    def __init__(self, organizer, root):
        super().__init__(organizer, root)

    def _load_package(self, path):
        pkgins = self.organizer.getModsDir()
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
