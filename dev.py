#!/usr/bin/env python3
"""
HeloWrite Development Server with Hot Reload
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class AppReloader(FileSystemEventHandler):
    """Handles file changes and restarts the app."""

    def __init__(self, app_path: str):
        self.app_path = app_path
        self.process = None
        self.restart_app()

    def on_modified(self, event):
        """Called when a file is modified."""
        if event.src_path.endswith(".py"):
            print(f"\n🔄 File changed: {event.src_path}")
            self.restart_app()

    def restart_app(self):
        """Restart the HeloWrite app."""
        # Kill existing process
        if self.process and self.process.poll() is None:
            print("🛑 Stopping previous instance...")
            try:
                # Kill the whole process group to ensure child subprocesses exit
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except Exception:
                try:
                    self.process.terminate()
                except Exception:
                    pass
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                except Exception:
                    try:
                        self.process.kill()
                    except Exception:
                        pass

        # Start new process
        print("🚀 Starting HeloWrite...")
        try:
            self.process = subprocess.Popen(
                [sys.executable, self.app_path] + sys.argv[2:],
                stdout=sys.stdout,
                stderr=sys.stderr,
                stdin=sys.stdin,
                start_new_session=True,
            )
        except Exception as e:
            print(f"❌ Failed to start app: {e}")

    def stop(self):
        """Stop the reloader and cleanup."""
        if self.process and self.process.poll() is None:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except Exception:
                try:
                    self.process.terminate()
                except Exception:
                    pass
            try:
                self.process.wait(timeout=2)
            except Exception:
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                except Exception:
                    try:
                        self.process.kill()
                    except Exception:
                        pass


def main():
    """Main development server function."""
    if len(sys.argv) < 2:
        print("Usage: python dev.py app.py [args...]")
        print("Example: python dev.py app.py sample.md")
        sys.exit(1)

    app_path = sys.argv[1]
    if not os.path.exists(app_path):
        print(f"❌ App file not found: {app_path}")
        sys.exit(1)

    print("🔥 HeloWrite Development Server")
    print("Watching for file changes... (Ctrl+C to stop)")
    print("-" * 50)

    # Create the app directory watcher
    app_dir = Path(app_path).parent
    observer = Observer()
    reloader = AppReloader(app_path)

    # Watch the app directory and src/ directory for Python file changes
    observer.schedule(reloader, str(app_dir), recursive=True)
    # Also watch the src/ directory specifically
    src_dir = app_dir / "src"
    if src_dir.exists():
        observer.schedule(reloader, str(src_dir), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down development server...")
        observer.stop()
        reloader.stop()
        observer.join()
        print("✅ Development server stopped.")


if __name__ == "__main__":
    main()
