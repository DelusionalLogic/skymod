import skymod.package
from .query import Mod
from .query import Query

from skymod.cfg import config as cfg

from colorama import Fore, Style
from path import Path

from fuzzywuzzy import process

class PackageRepo(object):
    def __init__(self, root):
        self.root = root

    def _load_package(self, path):
        pkgins = cfg.mo.dir / "mods"
        pkgsrc = cfg.source.dir
        config = skymod.package.load_package(
            path / "modbuild.lua", pkgsrc, pkgins
        )

        return config

    def _all_packages(self):
        return filter(
            lambda e: not e.name.startswith("."),
            self.root.dirs()
        )

    def find_literal(self, query):
        package_dir = self.root / query.name
        if not package_dir.exists():
            return None
        config = self._load_package(package_dir)
        if config is None:
            return None
        if query.matches(config):
            return config
        return None

    def _find_provider(self, query, exclude):
        candidates = set()
        for p in self._all_packages():
            candidate = self._load_package(p)
            if candidate is None or candidate in exclude:
                continue
            if query.matches(candidate):
                # @ENHANCEMENT This is a nice debug thing, but it clutters
                # a lot.  Maybe we can find some way of having this only when
                # we install something new
                # print("{} provides {}".format(
                #     Style.BRIGHT + str(candidate) + Style.RESET_ALL,
                #     Style.BRIGHT + str(query) + Style.RESET_ALL))
                candidates.add(candidate)
        return candidates

    def search(self, terms):
        return [
            self._load_package(e[0]) for e in
                process.extractBests(
                    terms,
                    self._all_packages(),
                    score_cutoff=10,
                    limit = 10
                )
        ]

    def _does_depend(self, p1, p2):
        for dep_query in p1.dependecies:
            q = Query(dep_query)
            if q.matches(p2):
                return True
        return False

    def find_bridges(self, p1, p2, exclude=set()):
        bridges = set()
        for p in self._all_packages():
            candidate = self._load_package(p)

            if candidate in exclude:
                continue

            for bridge in candidate.bridges:
                b1 = Query(bridge[0])
                b2 = Query(bridge[1])
                if b1.matches(p1) and b2.matches(p2):
                    bridges.add(candidate)
                elif b2.matches(p1) and b1.matches(p2):
                    bridges.add(candidate)
        return bridges

    def find_dependants(self, package):
        dep = []
        for p in self._all_packages():
            candidate = self._load_package(p)
            if self._does_depend(candidate, package):
                dep.append(candidate)
                continue
        return dep

    def find_package(self, query, exclude=set()):
        matches = self.find_packages(query, exclude=exclude)
        if matches:
            return matches.pop()
        return None

    def find_packages(self, query, exclude=set()):
        if len(query.name) < 2:
            raise ValueError("names shorter than 2 characters are not supported")
        if query.name not in (e.name for e in exclude):
            package = self.find_literal(query)
            if package:
                return { package }
        #Literal package not found, looking for a provider
        package = self._find_provider(query, exclude)
        return package

