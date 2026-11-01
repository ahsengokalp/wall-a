"""Read boot diagnostics after flashing our firmware, without Wi-Fi secrets."""

import argparse
import json
from pathlib import Path
import re
import time

import serial

parser = argparse.ArgumentParser()
parser.add_argument('--port', default='COM5')
parser.add_argument('--reset', action='store_true')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
result = {'port': args.port, 'camera_ready': False, 'network_ready': False}
connection = serial.Serial(port=None, baudrate=115200, timeout=.25)
connection.dtr = False
connection.rts = False
connection.port = args.port
try:
    connection.open()
    if args.reset:
        connection.rts = True
        time.sleep(.15)
        connection.rts = False
    deadline = time.monotonic() + 45
    buffer = b''
    while time.monotonic() < deadline:
        buffer += connection.read(1024)
        while b'\n' in buffer:
            line, buffer = buffer.split(b'\n', 1)
            text = line.decode('utf-8', errors='replace').strip()
            # Only print our known diagnostics, not unrelated firmware messages.
            if not text.startswith(('WALL_A_', 'CAMERA_', 'FIRST_FRAME', 'NETWORK_', 'AP_ERROR', 'HTTP_ERROR', 'WIFI_CONNECTING')):
                continue
            print(text, flush=True)
            sensor = re.search(r'sensor_pid=(0x[0-9a-fA-F]+)', text)
            if sensor:
                result['sensor_pid'] = sensor.group(1)
            if text.startswith('FIRST_FRAME'):
                result['first_frame'] = text
            if text.startswith('NETWORK_READY'):
                address = re.search(r'ip=([\d.]+)', text)
                mode = re.search(r'mode=(\w+)', text)
                result.update(network_ready=True, camera_ready='camera_ready=true' in text,
                              ip=address.group(1) if address else None,
                              mode=mode.group(1) if mode else None)
                deadline = 0
                break
finally:
    connection.close()
output = root / '.tools' / 'board-status.json'
output.parent.mkdir(exist_ok=True)
output.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result), flush=True)
raise SystemExit(0 if result['network_ready'] and result['camera_ready'] else 1)
