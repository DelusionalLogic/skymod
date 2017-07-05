from colorama import Style, Fore


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
