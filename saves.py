"""Discover and cache only the current user's saves. No save writes."""
from __future__ import annotations
from pathlib import Path
import threading
import gowsave


class SaveReader:
    def __init__(self, save_dir=None):
        self.save_dir = Path(save_dir) if save_dir else None
        self.lock = threading.Lock()
        self.stamp = None
        self.value = {}

    def read(self):
        with self.lock:
            dirs = [self.save_dir] if self.save_dir else gowsave.find_save_dirs()
            stamp = []
            for directory in dirs:
                for p in directory.glob('GOWRSAVE*'):
                    try:
                        s = p.stat()
                        stamp.append((str(p), s.st_size, s.st_mtime_ns))
                    except OSError:
                        continue
            stamp.sort()
            if self.stamp != stamp:
                self.value = gowsave.read(self.save_dir) if stamp else {}
                self.stamp = stamp
            return self.value
