from path import Path
from configparser import SafeConfigParser
from collections import namedtuple

from os.path import expanduser
_home = Path(expanduser("~"))

def to_bool(name):
    return name.lower() in ("true", )

ValueRecords = namedtuple("ValueRecords", "default, to_type")
_options = {
        "repo": {
            "dir": ValueRecords(_home / ".modbuild/repo", Path),
        },
        "cache": {
            "dir": ValueRecords(_home / ".modbuild/cache",  Path)
        },
        "local": {
            "dir": ValueRecords(_home / ".modbuild/local",  Path)
        },
        "source": {
            "dir": ValueRecords(_home / ".modbuild/source",  Path)
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
    if not path.parent.exists():
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

config = Config(Path("./test.ini"))
