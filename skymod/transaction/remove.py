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
from .errors import DependencyBreakError, ConflictError

from skymod.repository import Query
from skymod.package import InstallReason


# To remove a package we just delete the pkgins and remove the package from the
# local database
class RemoveTransaction(Transaction):
    def __init__(self, installed, repo, downloader):
        super().__init__(installed, repo, downloader)
        pass

    def _find_satisfier_in_targets(self, query):
        for t in self.targets:
            if query.matches(t):
                return t
        return None

    def _dependencies_filled_by_other(self, package):
        for dep_string in package.dependecies:
            dep_packages = self.local_repo.find_packages(
                Query(dep_string),
                exclude=self.targets
            )
            if not dep_packages:
                return False
        return True

    def _find_downstreams(self):
        dependants = set()
        for package in self.targets:
            for dep in self.local_repo.find_dependants(package):
                if self._dependencies_filled_by_other(dep):
                    continue
                if dep not in self.targets:
                    dependants.add((dep, package))
        return dependants

    def _does_bridge_after(self, p1, p2):
        installed_bridges = self.local_repo.find_bridges(p1, p2, self.targets)
        if installed_bridges:
            return True

    # Check for a potential conflict between two package
    def _check_conflict(self, p1, p2):
        # Does p1 conflict with p2
        for conflict in p1.conflicts:
            cq = Query(conflict)
            if cq.matches(p2) and not self._does_bridge_after(p1, p2):
                return (p1, p2)

        # Does p2 conflict with p1
        for conflict in p2.conflicts:
            cq = Query(conflict)
            if cq.matches(p1) and not self._does_bridge_after(p2, p1):
                return p2, p1

    # A package might bridge dependecies
    # To check those we enumerate all the bridges and check that they would be
    # fine
    def _find_bridge_conflicts(self):
        conflicts = set()
        for package in self.removes:
            for (b1, b2) in package.bridges:
                p1 = self.local_repo.find_package(Query(b1))
                p2 = self.local_repo.find_package(Query(b2))
                if not p1 or not p2:
                    # One of the sides were not installed, which means it's
                    # fine
                    continue
                if p1 in self.removes or p2 in self.removes:
                    # We are about to remove one of the sides. It's fine
                    continue
                conflict = self._check_conflict(p1, p2)
                if conflict:
                    conflicts.add((package, conflict))
        return conflicts

    # @SPEED This is very slow and should probably be sped up. I don't know how
    # though
    def _get_owned(self):
        owned = set(self.targets)
        # Here we want to process the same package multiple times
        queue = set(self.targets)
        while queue:
            package = queue.pop()
            if package.reason == InstallReason.DEP:
                for depa in self.local_repo.find_dependants(package):
                    if depa not in owned:
                        break
                else:
                    owned.add(package)
            for dep_str in package.dependecies:
                deps = self.local_repo.find_packages(Query(dep_str))
                for dep in deps:
                    queue.add(dep)
        return owned

    # Expanding a remove transaction is where we select the packages which no
    # longer have any install reason
    def expand(self):
        assert(self.state == TransactionState.INIT)

        # Remove all the packages that are owned by a target
        # (dependencies that are no longer needed)
        self.removes = self._get_owned()
        # @COMPLETE Support removal on unnecessary dependencies

        # Ensure that we don't remove a bridge
        conflicts = self._find_bridge_conflicts()
        if conflicts:
            raise ConflictError(conflicts)

        dependants = self._find_downstreams()
        if dependants:
            raise DependencyBreakError(dependants)

        self.state = TransactionState.EXPANDED

    # Make sure that when we call commit in a second nothing fails
    # This includes checking that we don't break any dependencies
    def prepare(self):
        assert(self.state == TransactionState.EXPANDED)

        self.state = TransactionState.PREPARED

    def _commit_package(self, target):
        self.local_repo.remove_package(target)
        target.pkgins.rmtree()

    def commit(self):
        assert(self.state == TransactionState.PREPARED)

        for target in self.removes:
            self._commit_package(target)

        self.state = TransactionState.COMMITTED
