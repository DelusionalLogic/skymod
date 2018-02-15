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
import patoolib
from colorama import Fore, Style
from path import Path
from tqdm import tqdm

from skymod.repository import Query

from .state import TransactionState


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
