"""Run PlatformIO with its downloads contained in this project."""

import argparse
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['build', 'upload', 'monitor'])
parser.add_argument('--port', default='COM5')
args = parser.parse_args()
build_env = os.environ.copy()
build_env['PLATFORMIO_CORE_DIR'] = str(root / '.tools' / 'pio-core')
command = [sys.executable, '-m', 'platformio']
if args.action == 'monitor':
    command += ['device', 'monitor', '--port', args.port, '--baud', '115200', '--dtr', '0', '--rts', '0']
else:
    command += ['run', '--project-dir', str(root / 'firmware')]
    if args.action == 'upload':
        command += ['--target', 'upload', '--upload-port', args.port]
raise SystemExit(subprocess.call(command, env=build_env, cwd=root))
