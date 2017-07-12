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
import skymod.repository
from .install_reason import InstallReason
from colorama import Style


def print_local_package(local_repo, package):
    required_by = [str(p) for p in local_repo.find_dependants(package)]
    deps = [str(d) for d in package.dependecies]

    bridges = set()
    for (b1, b2) in package.bridges:
        p1 = local_repo.find_package(
            skymod.repository.Query(b1)
        )
        p2 = local_repo.find_package(
            skymod.repository.Query(b2)
        )
        if p1 and p2:
            bridges.add("{}--{}".format(p1, p2))

    optdepends = []
    for opt_str in package.optdepends:
        optdepends.append(
            "{Style.BRIGHT}{}{Style.RESET_ALL} {}"
            .format(
                opt_str[0],
                opt_str[1],
                Style=Style
            )
        )

    info = {
        "Name": package.name,
        "Version": package.version,
        "Description": package.desc,
        "Installed on": package.install_date.strftime("%d/%m/%y"),
        "Provides": "  ".join(package.provides),
        "Depends On": "  ".join(deps),
        "Required By": "  ".join(required_by),
        "Conflicts with": "  ".join(package.conflicts),
        "Bridges": "  ".join(bridges),
        "Reason":
            "Explicitly installed"
            if package.reason == InstallReason.REQ
            else "Dependency",
        "Optional Dependecies": "\n\t" + "\n\t".join(optdepends),
    }
    for k, v in info.items():
        print("{Style.BRIGHT}{0:<22}{Style.RESET_ALL}: {1}".format(
            k,
            v,
            Style=Style
        ))
