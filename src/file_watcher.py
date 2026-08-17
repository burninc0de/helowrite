"""Event-based file watching for the editor."""

import os
from pathlib import Path
from typing import Any, Callable, Optional, Union

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class _FileEventHandler(FileSystemEventHandler):
    """Forward events for one file to a callback."""

    def __init__(self, path: Path, callback: Callable[[Path], None]) -> None:
        super().__init__()
        self.path = path
        self.callback = callback

    def _notify_if_current(self, path: Union[bytes, str]) -> None:
        if Path(os.fsdecode(path)).resolve() == self.path:
            self.callback(self.path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._notify_if_current(event.src_path)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._notify_if_current(event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._notify_if_current(event.dest_path)


class FileWatcher:
    """Watch a single file and invoke callbacks for external changes."""

    def __init__(self, callback: Callable[[Path], None]) -> None:
        self.callback = callback
        self._observer: Optional[Any] = None

    def start(self, path: Path) -> None:
        """Watch ``path`` by observing its parent directory."""
        self.stop()
        resolved_path = path.resolve()
        handler = _FileEventHandler(resolved_path, self.callback)
        observer = Observer()
        observer.schedule(handler, str(resolved_path.parent), recursive=False)
        observer.start()
        self._observer = observer

    def stop(self) -> None:
        """Stop watching and wait for the observer thread to finish."""
        if self._observer is None:
            return
        self._observer.stop()
        self._observer.join()
        self._observer = None
