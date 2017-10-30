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
from .transaction import Transaction
from .state import TransactionState
from .errors import (
    TransactionCycleError,
    ConflictError,
    MissingDependencyError,
)
from .conflictfinder import ConflictFinder
from .expander import Expander

from skymod.package import InstallReason
import networkx as nx

from skymod.dirhashmap import DirMap

from skymod.cfg import config as cfg

from skymod.config.vfs import VirtualFS

from colorama import Style, Fore
import patoolib
from tqdm import tqdm

from skymod.repository import Query


class AddTransaction(Transaction, ConflictFinder, Expander):
    def __init__(self, installed, repo, downloader, reason, cache=None):
        super().__init__(installed, repo, downloader)
        self.source_map = cache or DirMap(cfg.source.dir)
        self.removes = []
        self.reason = reason

    def _sort_deps_to_targets(self):
        assert(self.state == TransactionState.INIT)
        self.touches = list(reversed(list(nx.topological_sort(self.depend_G))))
        self.installs = [
            target for target in self.touches if not target.is_local
        ]

    def expand(self):
        assert(self.state == TransactionState.INIT)

        (expanded, missing) = self._expand_depedencies(
            self.local_repo,
            self.repo,
            self.targets,
            exclude=self.removes
        )
        if len(missing) > 0:
            raise MissingDependencyError(missing)

        self.depend_G = super().packages_to_graph(expanded)

        try:
            cycle = next(nx.simple_cycles(self.depend_G))
        except StopIteration:
            pass
        else:
            raise TransactionCycleError(cycle)

        self._sort_deps_to_targets()

        # Find all the packages that are upgrades rather than installs
        for package in expanded:
            if not package.is_local:
                # Search for just the name to check if we have any version
                # locally
                q = Query(package.name)
                local_package = self.local_repo.find_package(q)
                # If we have something we want to remove it first, we call that
                # an "upgrade"
                if local_package is None:
                    continue
                self.removes.append(local_package)

        conflicts = super()._find_conflicts(self.installs, self.local_repo)
        if len(conflicts) > 0:
            # There were at least some conflicts
            raise ConflictError(conflicts)
        self.state = TransactionState.EXPANDED

    def prepare(self):
        assert(self.state == TransactionState.EXPANDED)

        # Preload all the fetches into a set of files to get, by doing so we
        # can have a global download progress bar.
        fetches = set()
        for t in self.installs:
            print("Collecting sources from {}".format(t.name))
            for s in t.sources:
                fetches.add((s.uri, s.filename))

        # Actually do the downloads
        files = self.downloader.fetch(fetches)

        # Lets extract the archives into hashed folder names as well. This will
        # require us to translate the paths coming out of the scripts, but so
        # be it
        for uri, (archive_path, org_filename) in files.items():
            if uri in self.source_map:
                continue

            with self.source_map.atomic_add(uri) as unpack_dir:
                print(
                    "Extracting "
                    "{Style.BRIGHT}{Fore.MAGENTA}{}{Style.RESET_ALL}"
                    .format(uri, Style=Style, Fore=Fore)
                )
                patoolib.util.check_existing_filename(archive_path)
                mime, encoding = patoolib.util.guess_mime_mimedb(org_filename)

                if mime in patoolib.ArchiveMimetypes:
                    format_ = patoolib.ArchiveMimetypes[mime]

                if format_ == encoding:
                    encoding = None

                patoolib._extract_archive(
                    archive_path,
                    outdir=unpack_dir,
                    interactive=False,
                    verbosity=-1,
                    format=format_,
                    compression=encoding,
                )

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

        # @COMPLETE We should check if there's space on the disk for a copy of
        # package_files before we allow a commit. Currently a lack of space
        # breaks a package install. This can cause various issues.

        # @COMPLETE we should check if we can remove the packages first if it's
        # an upgrade

        self.state = TransactionState.PREPARED

    def _commit_package(self, target):
        is_upgrade = False
        desc = "{} package {}".format(
            "Upgrading" if is_upgrade else "Installing",
            target.name
        )

        # This is where we do the actual installation. We will need to
        # translate all the paths, since we are doing some hash/caching earlier
        srcdir = target.pkgsrc
        insdir = target.pkgins
        insdir.mkdir()
        for (f, t) in tqdm(target.config.package_files, desc=desc):
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

        # If the package isn't in the targets then we must have pulled it in as
        # a dependency
        reason = InstallReason.DEP
        if target in self.targets:
            # If it's an explicit requirement we want to use the reason
            # provided by the instantiator
            reason = self.reason

        self.local_repo.add_package(reason, target)
        pass

    def commit(self):
        assert(self.state == TransactionState.PREPARED)

        for target in self.removes:
            # Remove all the upgrades first, they'll be installed again when we
            # get to installing
            print("Removing {}".format(target))
            if target.pkgins.exists():
                target.pkgins.rmtree()
            self.local_repo.remove_package(target)

        for target in self.installs:
            self._commit_package(target)

        self.state = TransactionState.COMMITTED
