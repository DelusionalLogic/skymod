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
from .packagerepo import PackageRepo
import git
from tqdm import tqdm


class TqdmUpTo(tqdm):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.first = True

    def update_to(self, op_code, cur_count, max_count=None, message=""):
        # Skip the first update, because for some reason it's broken
        if self.first:
            self.first = False
            return
        if max_count is not None:
            self.total = max_count
            self.n = cur_count
        self.update(cur_count - self.n)


class GitRemotePackageRepo(PackageRepo):
    def __init__(self, organizer, root, remote):
        if not root.exists() or not (root/".git").exists():
            print("Cloning repo")
            with TqdmUpTo(miniters=1) as bar:
                self.repo = git.Repo.clone_from(
                    remote,
                    root,
                    progress=bar.update_to
                )
        else:
            self.repo = git.Repo(root)
        self.remote = self.repo.remote()
        super().__init__(organizer, root)

    def update(self):
        with TqdmUpTo(miniters=1, total=100) as bar:
            self.remote.pull(progress=bar.update_to)
