import os
import signal
import subprocess
import sys
from pathlib import Path
from watchfiles import watch

ROOT = Path('/app')
CONFIG = ROOT / 'langgraph.json'
AGENTS = ROOT / 'agents'

CMD = [
    'langgraph', 'dev',
    '--host', '0.0.0.0',
    '--port', '8000',
    '--config', 'langgraph.json',
    '--no-reload',
    '--no-browser',
]


def run_server():
    print('[watcher] starting langgraph:', ' '.join(CMD), flush=True)
    return subprocess.Popen(CMD)


def main():
    proc = run_server()
    try:
        for changes in watch(CONFIG, AGENTS, stop_event=None):
            print(f'[watcher] detected changes: {changes}', flush=True)
            # Restart the server
            if proc.poll() is None:
                try:
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                except Exception as e:
                    print(f'[watcher] error terminating: {e}', flush=True)
            proc = run_server()
    except KeyboardInterrupt:
        pass
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == '__main__':
    sys.exit(main())
