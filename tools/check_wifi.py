"""Windows scan metadata for configured SSID; never prints network credentials."""

import ast
import ctypes
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[1]
settings = (root / 'firmware/include/wifi_config.h').read_text(encoding='utf-8')
match = re.search(r'^#define WALL_A_WIFI_SSID\s+(".*")', settings, re.M)
try:
    target = ast.literal_eval(match.group(1)) if match else ''
except (ValueError, SyntaxError):
    raise SystemExit('SSID string could not be parsed. Check C++ quoting in wifi_config.h.')
response = subprocess.run(['netsh', 'wlan', 'show', 'networks', 'mode=bssid'], capture_output=True)
found = False
channels = set()
bands = set()
for encoding in ['utf-8', f'cp{ctypes.windll.kernel32.GetOEMCP()}', 'cp1254']:
    active = False
    for line in response.stdout.decode(encoding, errors='replace').splitlines():
        ssid = re.match(r'^SSID\s+\d+\s*:\s*(.*)$', line.strip())
        if ssid:
            active = ssid.group(1).strip() == target
            found |= active
        if active and re.search(r'(Channel|Kanal)\s*:', line, re.I):
            channels.add(line.split(':', 1)[1].strip())
        if active and re.search(r'(Band|Bant)\s*:', line, re.I):
            bands.add(line.split(':', 1)[1].strip())
print({'configured_ssid_visible': found, 'channels': sorted(channels),
       'bands': sorted(bands), 'scan_returncode': response.returncode})
