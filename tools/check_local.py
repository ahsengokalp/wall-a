"""Live HTTP and optional Ollama check; never saves a camera image to disk.

Run: python tools/check_local.py --model qwen3-vl:2b-instruct
"""

import argparse
import base64
import io
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
from PIL import Image, ImageDraw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', help='Also run an actual local vision inference.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'server.app:app', '--host', '127.0.0.1', '--port', str(port)], cwd=root, stdout=subprocess.DEVNULL)
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{port}', timeout=260, trust_env=False) as connection:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError('Server stopped before readiness.')
                try:
                    response = connection.get('/')
                    response.raise_for_status()
                    break
                except httpx.ConnectError:
                    time.sleep(.1)
            else:
                raise RuntimeError('Server did not start.')
            assert 'WALL-A' in response.text
            print('HTTP home: OK', flush=True)
            print('Health:', connection.get('/api/health').json(), flush=True)
            photo = Image.new('RGB', (400, 240), 'white')
            drawing = ImageDraw.Draw(photo)
            drawing.rectangle((40, 60, 150, 170), fill='red')
            drawing.ellipse((240, 60, 350, 170), fill='blue')
            output = io.BytesIO()
            photo.save(output, 'PNG')
            response = connection.post('/api/image', json={'image': base64.b64encode(output.getvalue()).decode()})
            response.raise_for_status()
            image = response.json()
            print('Real image upload: OK', flush=True)
            if args.model:
                started = time.monotonic()
                response = connection.post('/api/ask', json={
                    'model': args.model, 'image_id': image['id'],
                    'question': 'Bu görüntüdeki iki şeklin renkleri ve biçimleri neler? Kısa Türkçe cevap ver.',
                })
                if response.is_error:
                    raise RuntimeError(response.text)
                result = response.json()
                print(json.dumps({'answer': result['answer'], 'model_seconds': result['duration_seconds'],
                                  'wall_seconds': round(time.monotonic() - started, 1)}, ensure_ascii=False), flush=True)
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == '__main__':
    main()
