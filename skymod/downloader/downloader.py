from tqdm import tqdm
from skymod.dirhashmap import DirMap

from skymod.cfg import config as cfg


class Downloader(object):
    def __init__(self, cache=None):
        self.handlers = set()
        self.cache = cache or DirMap(cfg.cache.dir)

    def add_handler(self, handler):
        self.handlers.add(handler)

    def fetch_file(self, uri, filename):
        # Is the uri cached
        if self.cache.has_key(uri):
            tqdm.write("{} found in cache".format(uri))
            return self.cache.get(uri) / "file"

        with self.cache.atomic_add(uri) as dl_cache:
            for handler in self.handlers:
                if handler.accept(uri):
                    handler.fetch(uri, dl_cache / "file")

        return self.cache.get(uri) / "file"

    def fetch(self, entries):
        files = {}
        for (uri, filename) in entries:
            files[uri] = self.fetch_file(uri, filename)
        return files
