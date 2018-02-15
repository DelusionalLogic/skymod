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
import networkx as nx

import skymod.query as Q
from skymod.repository import Query


class Expander(object):
    def _find_satisfier_in_set(self, set_, query, exclude=set()):
        for t in set_:
            if t in exclude:
                continue
            if query.matches(t):
                return t
        return None

    def _find_satisfier_in_targets(self, query):
        return self._find_satisfier_in_set(self.targets, query)

    # We estimate how well this fits into our current setup by calculating the
    # ratio of dependencies already satisfied to total dependencies
    def _rate_satisfier(self, local_repo, package):
        if not package.dependecies:
            return 0
        cnt = 0
        for dep_str in package.dependecies:
            q = Query(dep_str)
            if self.local_repo.find_package(q) is not None:
                continue
            cnt += 1
        return cnt / len(package.dependecies)

    # @COMPLETE Maybe this should be some kind of strategy/mixin
    def _find_satisfier(self, local_repo, repo, q, targets, exclude):
        dep_package = self._find_satisfier_in_set(
            targets,
            q,
        )
        if dep_package is not None:
            return dep_package
        dep_package = local_repo.find_package(q, exclude=exclude)
        if dep_package is not None:
            return dep_package

        candidates = repo.find_packages(q, exclude=exclude)

        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates.pop()
        candidates = sorted(
            candidates,
            key=lambda x: self._rate_satisfier(local_repo, x)
        )
        return Q.option("Possible candidates for {}".format(q), candidates)

    def _expand_depedencies(
        self,
        local_repo,
        repo,
        targets,
        exclude=set()
    ):
        missing = set()
        resolved = set(targets)
        queue = list(targets)
        seen = set()
        while queue:
            package = queue.pop()
            if package in seen:
                continue
            seen.add(package)

            # We don't want to expand dependencies for a package that is
            # already installed. The user might have intentionally ignored
            # dependencies when they installed the package, so we are just
            # going to assume they know what they are doing.
            if package.is_local:
                continue

            for dep_name in package.dependecies:
                q = Query(dep_name)
                dep_package = self._find_satisfier(
                    local_repo,
                    repo,
                    q,
                    targets,
                    exclude=exclude
                )

                # We couldn't find a satisfier
                if dep_package is None:
                    missing.add((package, q))
                    continue

                resolved.add(dep_package)
                queue.append(dep_package)
        return (resolved, missing)

    def packages_to_graph(self, targets):
        G = nx.DiGraph()
        for package in targets:
            G.add_node(package)
            for dep_name in package.dependecies:
                q = Query(dep_name)
                dep_package = self._find_satisfier_in_set(targets, q)
                if dep_package is None:
                    # Swallow the error, since this is expected in some cases
                    continue
                    # raise Exception(
                    #     "Tried to make a graph out of packages that "
                    #     "have unresolved dependencies: " + str(q)
                    # )
                G.add_edge(package, dep_package)
        return G
