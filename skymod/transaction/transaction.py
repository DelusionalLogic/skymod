from .state import TransactionState

from skymod.repository import Query

from path import Path
from colorama import Style, Fore
import patoolib
from tqdm import tqdm


class Transaction(object):
    def __init__(self, local_repo, repo, downloader):
        self.targets = set()
        self.unresolved = []
        self.upgrades = []
        self.new_targets = []
        self.local_repo = local_repo
        self.repo = repo
        self.downloader = downloader

        self.state = TransactionState.INIT

    def add(self, target):
        assert(self.state == TransactionState.INIT)
        self.targets.add(target)

    def expand(self):
        raise NotImplementedError()

    def prepare(self):
        raise NotImplementedError()

    def _commit_package(self, target):
        raise NotImplementedError()

    def commit(self):
        assert(self.state == TransactionState.PREPARED)

        for target in self.targets:
            self._commit_package(target)

        self.state = TransactionState.COMMITTED
