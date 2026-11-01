"""Check real device JPEG and optionally the running Python panel; no disk images."""

import argparse
import base64
import io
import json
from pathlib import Path

import httpx
from PIL import Image

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--address')
parser.add_argument('--panel', default='http://127.0.0.1:8000')
args = parser.parse_args()
address = args.address or json.loads((root / '.tools/board-status.json').read_text())['ip']
with httpx.Client(timeout=20, trust_env=False, follow_redirects=False) as connection:
    status = connection.get(f'http://{address}/status')
    status.raise_for_status()
    info = status.json()
    assert info['camera_ready'], 'Camera is not ready.'
    print('Device status:', json.dumps(info), flush=True)
    photo = connection.get(f'http://{address}/capture')
    photo.raise_for_status()
    with Image.open(io.BytesIO(photo.content)) as picture:
        picture.load()
        assert picture.format == 'JPEG'
        print('Device JPEG:', picture.size, len(photo.content), 'bytes', flush=True)
    try:
        response = connection.post(args.panel + '/api/capture', json={'address': address})
        response.raise_for_status()
        data = response.json()
        with Image.open(io.BytesIO(base64.b64decode(data['image']))) as picture:
            picture.load()
            print('Panel capture:', picture.size, 'image_id=' + data['id'], flush=True)
    except httpx.HTTPError as error:
        print('Device works, but panel check failed:', type(error).__name__, flush=True)
        raise SystemExit(2)
