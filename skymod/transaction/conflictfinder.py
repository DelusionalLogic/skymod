from skymod.repository import Query


class ConflictFinder(object):
    def _does_bridge(self, local_repo, targets, p1, p2):
        # Do we have a bridge already installed?
        installed_bridges = local_repo.find_bridges(p1, p2)
        if installed_bridges:
            return True

        # Do any of the packages we are about to install offer to bridge this?
        for package in targets:
            for bridge in package.bridges:
                b1 = Query(bridge[0])
                b2 = Query(bridge[1])
                if b1.matches(p1) and b2.matches(p2):
                    return True
                elif b2.matches(p1) and b1.matches(p2):
                    return True
        return False

    def _find_conflicts(self, targets, local_repo):
        # Find conflicts inside targets
        conflicts = set()
        for t in targets:
            for conflict in t.conflicts:
                cq = Query(conflict)
                for tc in targets:
                    # Packages don't conflict with themselves
                    if t == tc:
                        continue
                    if (cq.matches(tc) and
                            not self._does_bridge(local_repo, targets, t, tc)):
                        conflicts.add((t, tc))

        local_packages = local_repo.get_all_packages()
        # Find conflicts from targets to local_repo
        for t in targets:
            for conflict in t.conflicts:
                cq = Query(conflict)
                for lp in local_packages:
                    # Packages don't conflict with themselves
                    if t == lp:
                        continue
                    if (cq.matches(lp) and
                            not self._does_bridge(local_repo, targets, t, lp)):
                        conflicts.add((t, lp))

        # Find conflicts from local_repo to targets
        for lp in local_packages:
            for conflict in lp.conflicts:
                cq = Query(conflict)
                for tc in targets:
                    # Packages don't conflict with themselves
                    if lp == tc:
                        continue
                    if (cq.matches(tc) and
                            not self._does_bridge(local_repo, targets, lp, tc)): # NOQA
                        conflicts.add((lp, tc))
        return conflicts
