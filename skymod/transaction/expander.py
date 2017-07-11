from skymod.repository import Query

import skymod.query as Q

import networkx as nx


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
                    raise Exception(
                        "Tried to make a graph out of packages that "
                        "have unresolved dependencies: " + str(q)
                    )
                G.add_edge(package, dep_package)
        return G
