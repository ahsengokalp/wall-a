"""Local face detection and explicitly enrolled face templates, independent of Ollama."""

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import threading
import time
import uuid

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'data' / 'people.sqlite3'
MODEL_VERSION = 'sface-2021dec'
MATCH_THRESHOLD = 0.45
MATCH_MARGIN = 0.05


def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    database = sqlite3.connect(DB_PATH, timeout=10)
    database.row_factory = sqlite3.Row
    database.execute('PRAGMA secure_delete=ON')
    database.execute('CREATE TABLE IF NOT EXISTS people (id TEXT PRIMARY KEY, name TEXT NOT NULL, name_key TEXT UNIQUE NOT NULL, feature BLOB NOT NULL, model TEXT NOT NULL, created_at TEXT NOT NULL)')
    database.commit()
    return database


def list_people():
    with closing(connection()) as database:
        return [dict(row) for row in database.execute('SELECT id,name,created_at FROM people ORDER BY created_at DESC')]


def known_people():
    import numpy as np
    with closing(connection()) as database:
        result = []
        for row in database.execute('SELECT id,name,feature FROM people WHERE model=?', (MODEL_VERSION,)):
            feature = np.frombuffer(row['feature'], dtype='<f4')
            if feature.size == 128 and np.isfinite(feature).all():
                result.append({'id': row['id'], 'name': row['name'], 'feature': feature})
        return result


class VisionEngine:
    def __init__(self):
        self.lock = threading.RLock()
        self.detector = None
        self.recognizer = None

    def ensure(self):
        if self.detector is not None:
            return
        try:
            import cv2
        except ImportError:
            raise HTTPException(503, 'Yüz araçları kurulu değil. requirements.txt bağımlılıklarını kur.')
        detection = ROOT / 'models/face_detection_yunet_2023mar.onnx'
        recognition = ROOT / 'models/face_recognition_sface_2021dec.onnx'
        if not detection.exists() or not recognition.exists():
            raise HTTPException(503, 'Yüz modelleri eksik. Terminalde .\\.venv\\Scripts\\python.exe tools/setup_vision.py çalıştır.')
        try:
            cv2.setNumThreads(2)
            detector = cv2.FaceDetectorYN.create(str(detection), '', (320, 320), 0.9, 0.3, 100)
            recognizer = cv2.FaceRecognizerSF.create(str(recognition), '')
        except cv2.error:
            raise HTTPException(503, 'Yüz modeli açılamadı. Model kurulumunu ve OpenCV sürümünü kontrol et.')
        self.detector, self.recognizer = detector, recognizer

    def inspect(self, raw, features=False):
        started = time.perf_counter()
        with self.lock:
            self.ensure()
            import cv2
            import numpy as np
            image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                raise HTTPException(400, 'Görüntü yüz algılama için okunamadı.')
            height, width = image.shape[:2]
            ratio = min(1, 640 / max(width, height))
            if ratio < 1:
                image = cv2.resize(image, (round(width * ratio), round(height * ratio)))
            height, width = image.shape[:2]
            self.detector.setInputSize((width, height))
            try:
                _, detected = self.detector.detect(image)
                faces = []
                for row in detected if detected is not None else []:
                    x, y, w, h = [float(value) for value in row[:4]]
                    left, top = max(0, x), max(0, y)
                    right, bottom = min(width, x+w), min(height, y+h)
                    if right <= left or bottom <= top:
                        continue
                    center = (left + right) / (2 * width)
                    face = {'box': [left/width, top/height, (right-left)/width, (bottom-top)/height],
                            'detection_score': round(float(row[-1]), 3),
                            'position': 'sol' if center < .4 else 'sağ' if center > .6 else 'orta',
                            'size_pixels': min(w, h), 'feature': None}
                    if features and min(w, h) >= 40:
                        aligned = self.recognizer.alignCrop(image, row)
                        feature = self.recognizer.feature(aligned).flatten().astype('<f4')
                        norm = float(np.linalg.norm(feature))
                        if norm > 0 and np.isfinite(feature).all():
                            face['feature'] = feature / norm
                    faces.append(face)
            except cv2.error:
                raise HTTPException(503, 'Yüz analizi başarısız oldu. Başka bir kareyle yeniden dene.')
        return faces, round((time.perf_counter() - started) * 1000, 1)


engine = VisionEngine()


def analyze(raw):
    records = known_people()
    faces, duration = engine.inspect(raw, features=bool(records))
    output = []
    for face in faces:
        matches = sorted(((float(face['feature'] @ record['feature']), record) for record in records), key=lambda pair: pair[0], reverse=True) if face['feature'] is not None else []
        accepted = bool(matches and matches[0][0] >= MATCH_THRESHOLD and (len(matches) == 1 or matches[0][0] - matches[1][0] >= MATCH_MARGIN))
        record = matches[0][1] if accepted else None
        output.append({'box': face['box'], 'position': face['position'], 'detection_score': face['detection_score'],
                       'person_id': record['id'] if record else None, 'name': record['name'] if record else 'Bilinmeyen',
                       'similarity': round(matches[0][0], 3) if matches else None})
    return {'faces': output, 'face_count': len(output), 'duration_ms': duration,
            'known_count': len(records), 'method': 'YuNet + SFace', 'match_threshold': MATCH_THRESHOLD}


def enroll(name, raw):
    name = name.strip()
    if not name or len(name) > 80 or any(ord(character) < 32 for character in name):
        raise HTTPException(400, '1–80 karakterlik bir kişi adı yaz.')
    faces, _ = engine.inspect(raw, features=True)
    if len(faces) != 1:
        raise HTTPException(400, 'Kayıt fotoğrafında tam olarak bir yüz bulunmalı. Önden ve aydınlık bir fotoğraf seç.')
    feature = faces[0]['feature']
    if feature is None:
        raise HTTPException(400, 'Yüz çok küçük veya okunamadı. Daha yakın ve net bir fotoğraf seç.')
    item = {'id': uuid.uuid4().hex, 'name': name, 'created_at': datetime.now(timezone.utc).isoformat()}
    try:
        with closing(connection()) as database, database:
            if database.execute('SELECT COUNT(*) FROM people').fetchone()[0] >= 100:
                raise HTTPException(400, 'En fazla 100 kişi kaydedilebilir.')
            database.execute('INSERT INTO people VALUES (?,?,?,?,?,?)',
                             (item['id'], name, name.casefold(), feature.astype('<f4').tobytes(), MODEL_VERSION, item['created_at']))
    except sqlite3.IntegrityError:
        raise HTTPException(409, 'Bu ad zaten kayıtlı. Farklı ad kullan veya eski kaydı sil.')
    return item


def delete_person(identifier):
    with closing(connection()) as database, database:
        cursor = database.execute('DELETE FROM people WHERE id=?', (identifier,))
        if cursor.rowcount == 0:
            raise HTTPException(404, 'Kişi kaydı bulunamadı.')
    return {'deleted': identifier}
