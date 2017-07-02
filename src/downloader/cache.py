from path import Path
import hashlib

class FsCache(object):
    def __init__(self, path):
        self.path = path
        # Make the cache
        if not self.path.exists():
            self.path.makedirs()

    # The filename is only a hint. We are allowed to do return whatever path we
    # want
    def get_path(self, key, filename):
        key_hash = hashlib.md5(key.encode()).hexdigest()
        key_dir = self.path / key_hash
        # Do we already have a value for this key?
        if key_dir.exists():
            # Just get the first file in the dir
            # @WINDOWS probably wont function on windows, since that includes
            # . and ..
            return key_dir.files()[0]
        key_dir.mkdir()
        return key_dir / filename

