import os
import time

class FileLock:
    def __init__(self, lock_file):
        self.lock_file = lock_file
        self._locked = False

    def acquire(self, timeout=30):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                self.fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                self._locked = True
                return True
            except FileExistsError:
                time.sleep(1)
        return False

    def release(self):
        if self._locked:
            os.close(self.fd)
            os.remove(self.lock_file)
            self._locked = False

    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"Could not acquire lock on {self.lock_file}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release() 