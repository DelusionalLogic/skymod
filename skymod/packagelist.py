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
from colorama import Fore, Style


class InstalledTag(object):
    color = Fore.YELLOW

    def __init__(self, version):
        self.version = version

    def __str__(self):
        return "installed={}".format(self.version)


class WantedTag(object):
    color = Fore.GREEN

    def __init__(self):
        pass

    def __str__(self):
        return "wanted"


class PackageList(object):
    def __init__(self, list_=None):
        self.list_ = list_ or []
        self.tags = {i: [] for i in self.list_}

    def add_tag(self, package, tag):
        self.tags[package].append(tag)

    def present(self):
        for package in self.list_:
            tag_str = " ".join(
                ("{}[{}]".format(k.color, k) for k in self.tags[package])
            )
            print("{}/{} {}".format(
                Fore.MAGENTA + package.name + Style.RESET_ALL,
                package.version,
                tag_str
                ))

    def __iter__(self):
        return self.list_.__iter__()
