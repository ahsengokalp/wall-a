"""Download OpenCV Zoo models; validate published Git-LFS SHA-256 values."""

import hashlib
from pathlib import Path
import urllib.request

root = Path(__file__).resolve().parents[1] / 'models'
models = [
    ('face_detection_yunet', 'face_detection_yunet_2023mar.onnx', '8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4'),
    ('face_recognition_sface', 'face_recognition_sface_2021dec.onnx', '0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79'),
]
root.mkdir(exist_ok=True)
for directory, name, digest in models:
    destination = root / name
    if not destination.exists() or hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
        url = f'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/{directory}/{name}'
        print('Downloading', name, flush=True)
        with urllib.request.urlopen(url, timeout=90) as response:
            content = response.read(45 * 1024 * 1024)
        if hashlib.sha256(content).hexdigest() != digest:
            raise RuntimeError('Model hash mismatch: ' + name)
        temporary = destination.with_suffix('.download')
        temporary.write_bytes(content)
        temporary.replace(destination)
    with urllib.request.urlopen(f'https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/{directory}/LICENSE', timeout=30) as response:
        (root / (directory + '.LICENSE')).write_bytes(response.read())
    print('Verified', name, flush=True)
