from .add import AddTransaction
from .expander import Expander
from .errors import MissingDependencyError

from skymod.repository import Query


class UpgradeTransaction(AddTransaction, Expander):
    def __init__(self, installed, repo, downloader):
        super().__init__(installed, repo, downloader)

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
        self.targets = self.removes
        self.installs = [u[1] for u in upgrades]

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
            print("Checking {}".format(package))
            dependants = self.local_repo.find_dependants(package)
            for dependant in dependants:
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
