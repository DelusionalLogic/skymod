from .packagerepo import PackageRepo
import git
import progressbar
from tqdm import tqdm
import time

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
    def __init__(self, root, remote):
        if not root.exists() or not (root/".git").exists():
            print("Cloning repo")
            with TqdmUpTo(miniters=1) as bar:
                self.repo = git.Repo.clone_from(remote, root, progress = bar.update_to)
        else:
            self.repo = git.Repo(root)
        self.remote = self.repo.remote()
        super().__init__(root)

    def update(self):
        with TqdmUpTo(miniters=1, total=100) as bar:
            self.remote.pull(progress = bar.update_to)
