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
from .add import AddTransaction
from .expander import Expander
from .errors import MissingDependencyError

from skymod.repository import Query
from skymod.package import InstallReason


class UpgradeTransaction(AddTransaction, Expander):
    def __init__(self, installed, repo, downloader):
        super().__init__(installed, repo, downloader, InstallReason.REQ)

    def _find_package_upgrade(self, package):
        # Ignore any package that is already in the targets array, regardless
        # of version
        if package in self.targets:
            return

        # Just search for the name and do the version comparison manually
        q = Query(package.name)
        remote_package = self.repo.find_literal(q)
        if remote_package.version > package.version:
            self.targets.add(remote_package)

    def _find_upgrade_required(self, targets):
        upgrade = set()
        for package in targets:
            assert(package.is_local)
            q = Query(package.name)
            remote_package = self.repo.find_literal(q)
            if remote_package is None:
                print("No remote package for {}".format(package))
                continue
            if remote_package.version > package.version:
                upgrade.add((package, remote_package))
        return upgrade

    # An upgrade transaction is the same as an add except it checks if anything
    # needs updating and adds that to the targets. So do that here
    def expand(self):
        # If theres no targets, expand to all local packages
        if not self.targets:
            self.targets = self.local_repo.get_all_packages()

        upgrades = self._find_upgrade_required(self.targets)
        self.removes = [u[0] for u in upgrades]
        self.installs = [u[1] for u in upgrades]
        self.targets = [u[1] for u in upgrades if u[0].reason == InstallReason.REQ]

        # So the dependencies might have changed. I don't think we want to
        # remove unused dependencies, but we do want to pull in new ones. We
        # might also stop providing something, which could invalidate some
        # other part of the local database.
        # Basically we will want to do the following:
        #   - Check if all dependencies are filled
        #   - Fill new ones (maybe asking?)
        #   - Check that all the people depending on us still have their
        #   dependencies filled after the transaction
        # During all of these steps we need to make sure that we aren't
        # matching packages that this transaction is going to remove, but
        # include packages we are about to install.

        # Find all packages touched by something we are removing

        new_missing = set()

        for package in self.removes:
            dependants = self.local_repo.find_dependants(package)
            for dependant in dependants:

                # If the dependant is queued for removal we don't really care
                # if we are going to break dependencies
                if dependant in self.removes:
                    continue

                for dep_str in dependant.dependecies:
                    q = Query(dep_str)
                    # If it didn't match before then we don't care
                    # This is important because we don't want to pop up and
                    # error now if the user purposefully broke some
                    # dependencies at some point, but if we are breaking
                    # something we want to report that
                    if not q.matches(package):
                        continue
                    # Are we going to install something that fixes it?
                    dep_sat = super()._find_satisfier_in_set(self.installs, q)
                    if dep_sat is not None:
                        continue
                    # Do we have something else that fixes it?
                    dep_sat = self.local_repo.find_package(
                        q,
                        exclude=self.removes
                    )
                    if dep_sat is not None:
                        continue
                    # This upgrade is going to be a problem
                    # @COMPLETE We should dump the package here as well.
                    new_missing.add((dependant, q))

        if len(new_missing) > 0:
            raise MissingDependencyError(new_missing)

        # @HACK: Reset removes, since the add transaction finds all packages
        # that are actually upgrades
        self.removes = []

        self.targets = self.installs
        super().expand()
        # (expanded, missing) = super()._expand_depedencies(
        #     self.local_repo,
        #     self.repo,
        #     self.installs,
        #     exclude=self.removes
        # )

        # self.depend_G = super().packages_to_graph(expanded)

        # try:
        #     cycle = next(nx.simple_cycles(self.depend_G))
        # except StopIteration:
        #     pass
        # else:
        #     raise TransactionCycleError(cycle)

        # touches = nx.topological_sort(self.depend_G, reverse=True)
        # self.installs = [target for target in touches if not target.is_local]

        # print(self.installs)
