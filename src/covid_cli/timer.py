import sys
import time
import threading
from colorama import Fore, Style

class LiveTimer:
    def __init__(self, message: str):
        self.message = message
        self.start_time = None
        self._stop_event = threading.Event()
        self._thread = None

    def _animate(self):
        while not self._stop_event.is_set():
            elapsed = time.time() - self.start_time
            mins, secs = divmod(int(elapsed), 60)
            timer_str = f"[{mins:02d}:{secs:02d}]"
            sys.stdout.write(f"\r{Fore.CYAN}Agent: ⏳ {self.message} {timer_str}{Style.RESET_ALL}")
            sys.stdout.flush()
            # Sleep in small increments to respond quickly to stop_event
            for _ in range(10):
                if self._stop_event.is_set():
                    break
                time.sleep(0.1)

    def __enter__(self):
        self.start_time = time.time()
        self._stop_event.clear()
        sys.stdout.write(f"\r{Fore.CYAN}Agent: ⏳ {self.message} [00:00]{Style.RESET_ALL}")
        sys.stdout.flush()
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        # Clear the line
        sys.stdout.write("\r" + " " * 100 + "\r")
        sys.stdout.flush()
