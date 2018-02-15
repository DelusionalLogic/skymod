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
from collections import namedtuple
from configparser import SafeConfigParser
from os.path import expanduser

from path import Path

_home = Path(expanduser("~"))


def to_bool(name):
    return name.lower() in ("true", )


ValueRecords = namedtuple("ValueRecords", "default, to_type")
_options = {
        "repo": {
            "dir": ValueRecords(_home / ".modbuild/repo", Path),
            "url": ValueRecords(
                "https://github.com/DelusionalLogic/modbuild-repo.git",
                str
            )
        },
        "cache": {
            "dir": ValueRecords(_home / ".modbuild/cache",  Path),
        },
        "local": {
            "dir": ValueRecords(_home / ".modbuild/local",  Path),
        },
        "source": {
            "dir": ValueRecords(_home / ".modbuild/source",  Path),
        },
        "mo": {
            "mods_dir": ValueRecords(Path(""),  Path),
            "profile_dir": ValueRecords(Path(""),  Path),
        },
        "nexus": {
            "username": ValueRecords("", str),
            "password": ValueRecords("", str),
        },
        "ll": {
            "username": ValueRecords("", str),
            "password": ValueRecords("", str),
        },
}


def _write_defaults(path):
    if not path.parent == "" and not path.parent.exists():
        path.parent.makedirs()
    cp = SafeConfigParser()

    for section, values in _options.items():
        cp.add_section(section)
        for name, value in values.items():
            cp.set(section, name, str(value.default))

    with open(path, "w") as f:
        cp.write(f)


def _write_missing(path):
    cp = SafeConfigParser()
    cp.read(path)

    for section, values in _options.items():
        if not cp.has_section(section):
            cp.add_section(section)
        for name, value in values.items():
            if not cp.has_option(section, name):
                cp.set(section, name, str(value.default))

    with open(path, "w") as f:
        cp.write(f)


class Section(object):
    def __init__(self, path, cp, name):
        self.path = path
        self.cp = cp
        self.name = name

    def __getattr__(self, name):
        return self[name]

    def __getitem__(self, key):
        section_default = _options[self.name]
        if key not in section_default:
            raise KeyError()
        t = section_default[key].to_type

        val = t(self.cp.get(self.name, key))
        return val

    def __setattr__(self, name, value):
        if name in ["path", "cp", "name"]:
            return super().__setattr__(name, value)
        self[name] = value

    def __setitem__(self, key, value):
        section_default = _options[self.name]
        if key not in section_default:
            raise KeyError()

        self.cp.set(self.name, key, str(value))
        with open(self.path, "w") as f:
            self.cp.write(f)


class Config(object):
    def __init__(self, path):
        self.path = path
        self.cp = SafeConfigParser()
        if not path.exists():
            _write_defaults(self.path)
        _write_missing(self.path)
        self.cp.read([self.path])

    def __getattr__(self, name):
        return self[name]

    def __getitem__(self, key):
        if key not in _options:
            raise KeyError()

        section = Section(self.path, self.cp, key)
        return section


class ConfRef(object):
    def __init__(self, val=None):
        self.val = val

    def __getattr__(self, key):
        return self.val.__getattr__(key)

    def __getitem__(self, key):
        return self.val.__getitem__(key)


def read_config(path=_home / ".modbuild/config.ini"):
    config.val = Config(path)


config = ConfRef()
