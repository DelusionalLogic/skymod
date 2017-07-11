from skymod.repository import Query

import skymod.query as Q


class Expander(object):
    def _find_satisfier_in_set(self, set_, query):
        for t in set_:
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

    def _find_satisfier(self, local_repo, repo, q):
        dep_package = self._find_satisfier_in_targets(q)
        if dep_package is not None:
            return dep_package
        dep_package = local_repo.find_package(q)
        if dep_package is not None:
            return dep_package

        candidates = repo.find_packages(q)

        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates.pop()
        candidates = sorted(candidates, key=self._rate_satisfier)
        return Q.option("Possible candidates for {}".format(q), candidates)

    def _expand_depedencies(self, local_repo, repo, targets):
        missing = set()
        queue = list(targets)
        seen = set()
        while queue:
            package = queue.pop()
            if package in seen:
                continue
            seen.add(package)

            for dep_name in package.dependecies:
                q = Query(dep_name)
                dep_package = self._find_satisfier(local_repo, repo, q)

                # We couldn't find a satisfier
                if dep_package is None:
                    missing.add((package, q))
                    continue

                queue.append(dep_package)
        return (seen, missing)
