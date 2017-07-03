import hashlib
from contextlib import contextmanager

class DirMap(object):
    def __init__(self, container_dir):
        self.container_dir = container_dir

        # Transaction stuff

        # Since no SHA-1 hash is TEMP we can safely use that as a temp dir name
        # in tree
        self.temp = self.container_dir / "TEMP"
        # Set when we know where the destination of a current transaction is
        # going. If this is not None a transaction is running
        self.transaction_dest = None
        # Create the container dir if it doesn't exist
        if not self.container_dir.exists():
            self.container_dir.mkdir()

    def _get_path_safe(self, key):
        key_hash = hashlib.sha1(key.encode()).hexdigest()
        key_path = self.container_dir / key_hash
        return key_path

    def has_key(self, key):
        key_path = self._get_path_safe(key)
        if key_path.exists():
            return True
        return False

    def alloc(self, key):
        if self.has_key(key):
            raise KeyError("{} already in map".format(key))

        self.transaction_dest = self._get_path_safe(key)
        if self.temp.exists():
            self.temp.rmtree()
        self.temp.mkdir()
        return self.temp

    def abort(self):
        self.temp.rmtree()
        self.transaction_dest = None

    def commit(self):
        self.temp.rename(self.transaction_dest)
        self.transaction_dest = None

    @contextmanager
    def atomic_add(m, key):
        h = m.alloc(key)
        try: 
            yield h
        except Exception:
            m.abort()
            raise
        m.commit()

    def get(self, key):
        if not self.has_key(key):
            raise KeyError("{} not in map".format(key))

        key_path = self._get_path_safe(key)
        return key_path

    def remove(self, key):
        key_path = self._get_path_safe(key)
        key_path.rmtree()

