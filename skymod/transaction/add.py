from .transaction import Transaction
from .state import TransactionState
from .errors import TransactionCycleError, ConflictError, MissingDependencyError
from skymod.package import InstallReason
import networkx as nx

from skymod.dirhashmap import DirMap

from skymod.cfg import config as cfg

from skymod.config.vfs import VirtualFS

from colorama import Style, Fore
import patoolib
from tqdm import tqdm

from skymod.repository import Query
import skymod.query as Q


class AddTransaction(Transaction):
    def __init__(self, installed, repo, downloader):
        super().__init__(installed, repo, downloader)
        self.source_map = DirMap(cfg.source.dir)

    def _find_satisfier_in_targets(self, query):
        for t in self.targets:
            if query.matches(t):
                return t
        return None

    def _find_satisfier(self, q):
        dep_package = self._find_satisfier_in_targets(q)
        if dep_package is not None:
            return dep_package
        dep_package = self.local_repo.find_package(q)
        if dep_package is not None:
            return dep_package

        candidates = self.repo.find_packages(q)

        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates.pop()
        return Q.option("Possible candidates for {}".format(q), candidates)

    def _expand_dependencies_to_graph(self):
        assert(self.state == TransactionState.INIT)
        missing = set()
        G = nx.DiGraph()
        queue = list(self.targets)
        seen = set(self.targets)
        while queue:
            package = queue.pop()
            G.add_node(package)
            for dep_name in package.dependecies:
                q = Query(dep_name)
                dep_package = self._find_satisfier(q)
                if dep_package is None:
                    missing.add( (package, q) )
                    self.unresolved.append(q)
                    continue

                G.add_edge(package, dep_package)
                if not dep_package in seen:
                    seen.add(dep_package)
                    queue.append(dep_package)
        return (G, missing)

    def _sort_deps_to_targets(self):
        assert(self.state == TransactionState.INIT)
        self.touches = nx.topological_sort(self.depend_G, reverse=True)
        self.installs = [target for target in self.touches if not target.is_local]

    def _does_bridge(self, p1, p2):
        # Do we have a bridge already installed?
        installed_bridges = self.local_repo.find_bridges(p1, p2)
        if installed_bridges:
            return True

        # Do any of the packages we are about to install offer to bridge this?
        for package in self.installs:
            for bridge in package.bridges:
                b1 = Query(bridge[0])
                b2 = Query(bridge[1])
                if b1.matches(p1) and b2.matches(p2):
                    return True
                elif b2.matches(p1) and b1.matches(p2):
                    return True
        return False

    def _find_conflicts(self):
        # Find conflicts inside targets
        conflicts = set()
        for t in self.installs:
            for conflict in t.conflicts:
                cq = Query(conflict)
                for tc in self.installs:
                    if cq.matches(tc) and not self._does_bridge(t, tc):
                        conflicts.add((t, tc))

        local_packages = self.local_repo.get_all_packages()
        # Find conflicts from targets to local_repo
        for t in self.installs:
            for conflict in t.conflicts:
                cq = Query(conflict)
                for lp in local_packages:
                    if cq.matches(lp) and not self._does_bridge(t, lp):
                        conflicts.add((t, lp))

        # Find conflicts from local_repo to targets
        for lp in local_packages:
            for conflict in lp.conflicts:
                cq = Query(conflict)
                for tc in self.installs:
                    if cq.matches(tc) and not self._does_bridge(lp, tc):
                        conflicts.add((lp, tc))
        return conflicts

    def expand(self):
        assert(self.state == TransactionState.INIT)

        (self.depend_G, missing) = self._expand_dependencies_to_graph()

        if len(missing) > 0:
            raise MissingDependencyError(missing)

        try:
            cycle = next(nx.simple_cycles(self.depend_G))
        except StopIteration:
            pass
        else:
            raise TransactionCycleError(cycle)

        self._sort_deps_to_targets()

        conflicts = self._find_conflicts()
        if len(conflicts) > 0:
            # There were at least some conflicts
            raise ConflictError(conflicts)
        self.state = TransactionState.EXPANDED

    def prepare(self):
        assert(self.state == TransactionState.EXPANDED)
        for package in self.touches:
            if not package.is_local:
                # Search for just the name to check if we have any version locally
                q = Query(package.name)
                local_package = self.local_repo.find_package(q)
                # If we have something we want to remove it first, we call that
                # an "upgrade"
                if local_package is None:
                    continue
                self.upgrades.append(local_package)

        # Preload all the fetches into a set of files to get, by doing so we
        # can have a global download progress bar, and also get all the
        # interactivity out of the way
        fetches = set()
        for t in self.installs:
            print("Collecting sources from {}".format(t.name))
            for s in t.sources:
                fetches.add( (s.uri, s.filename) )

        # Actually do the downloads
        files = self.downloader.fetch(fetches)

        # Lets extract the archives into hashed folder names as well. This will
        # require us to translate the paths coming out of the scripts, but so
        # be it
        for (uri, archive_path) in files.items():
            if self.source_map.has_key(uri):
                continue

            with self.source_map.atomic_add(uri) as unpack_dir:
                print("Extracting {Style.BRIGHT}{Fore.MAGENTA}{}{Style.RESET_ALL}".format(uri, Style=Style, Fore=Fore))
                patoolib.extract_archive(archive_path, outdir=unpack_dir, interactive=False, verbosity=-1)

        # Populate the package_files list with the operations to complete
        for t in self.installs:
            vfs = VirtualFS()
            # Create the source name lookup table
            for s in t.sources:
                filename_noext = s.get_name()
                p = self.source_map.get(s.uri)
                vfs.remap(filename_noext, p)
            t.package(vfs)

        # @COMPLETE package_files should probably be checked for problems
        # BEFORE we allow a commit

        self.state = TransactionState.PREPARED

    def _commit_package(self, target):
        is_upgrade = False
        # Remove all the upgrades first, they'll be installed again when we get
        # to installing
        for t in self.upgrades:
            if t.name == target.name:
                is_upgrade = True
                if target.pkgins.exists():
                    target.pkgins.rmtree()
                self.local_repo.remove_package(t)
                break

        print("{} package {}".format("Upgrading" if is_upgrade else "Installing", target))

        # This is where we do the actual installation. We will need to
        # translate all the paths, since we are doing some hash/caching earlier
        srcdir = target.pkgsrc
        insdir = target.pkgins
        insdir.mkdir()
        for (f, t) in tqdm(target.config.package_files):
            from_ = srcdir / f
            to = insdir / t

            if from_.isdir():
                if not to.exists():
                    to.makedirs()
            else:
                to_dir = to.parent
                if not to_dir.exists():
                    to_dir.makedirs()
                from_.copy(to)

        # If the package isn't in the targets then we must have pulled it in as a dependency
        reason = InstallReason.DEP
        if target in self.targets:
            reason = InstallReason.REQ

        self.local_repo.add_package(reason, target)
        pass

    def commit(self):
        assert(self.state == TransactionState.PREPARED)

        for target in self.installs:
            self._commit_package(target)

        self.state = TransactionState.COMMITTED
