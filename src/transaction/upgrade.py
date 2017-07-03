from .add import AddTransaction
from .state import TransactionState
from .errors import TransactionCycleError, ConflictError, MissingDependencyError
from package import InstallReason
import networkx as nx

from dirhashmap import DirMap

from cfg import config as cfg
import hashlib

from config.vfs import VirtualFS

from path import Path
from colorama import Style, Fore
import patoolib
from tqdm import tqdm

from repository import Query
import query as Q


class UpgradeTransaction(AddTransaction):
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

    # An upgrade transaction is the same as an add except it checks if anything
    # needs updating and adds that to the targets. So do that here
    def expand(self):
        for package in self.local_repo.get_all_packages():
            # This procedure adds the upgrades to the target list
            upgrade = self._find_package_upgrade(package)

        super().expand()
