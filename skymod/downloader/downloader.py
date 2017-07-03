from tqdm import tqdm
from skymod.dirhashmap import DirMap

from skymod.cfg import config as cfg

class DownloadAction(object):
    def __init__(self, handlers, uri, to):
        self.handlers = handlers
        self.uri = uri
        self.to = to

    def display(self):
        tqdm.write("Download {} to {}".format(self.uri, self.to))

    def execute(self):
        for handler in self.handlers:
            if handler.accept(self.uri):
                handler.fetch(self.uri, self.to)

class CopyAction(object):
    def __init__(self, from_, to):
        self.from_ = from_
        self.to = to

    def display(self):
        tqdm.write("Copy {} to {}".format(self.from_, self.to))

    def execute(self):
        self.from_.copy(self.to)

class Downloader(object):
    def __init__(self):
        self.handlers = set()
        self.cache = DirMap(cfg.cache.dir)

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

    def _files_to_actions(self, entries):
        actions = []
        uri_to_path = {}
        for (uri, to) in entries:
            if uri not in uri_to_path.keys():
                actions.append(DownloadAction(self.handlers, uri, to))
                uri_to_path[uri] = to
            else:
                print("{} was already downloaded in this transaction".format(uri))
                actions.append(CopyAction(uri_to_path[uri], to))
        return actions

    def fetch(self, entries):
        files = {}
        for (uri, filename) in entries:
            files[uri] = self.fetch_file(uri, filename)
        return files
