import base64
import io
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
import pytest

from server.app import app
from server import vision


@pytest.fixture
def browser(tmp_path, monkeypatch):
    monkeypatch.setattr(vision, 'DB_PATH', tmp_path / 'people.sqlite3')
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample():
    path = Path(__file__).resolve().parents[1] / '.tools/vision-test-face.jpg'
    if not path.exists():
        pytest.skip('Optional OpenCV example photo absent; see docs/yuzler.md for integration check.')
    return path.read_bytes()


def encoded(raw):
    return base64.b64encode(raw).decode()


def test_people_listing_and_missing_delete(browser):
    assert browser.get('/api/people').json() == {'people': []}
    assert browser.delete('/api/people/not-present').status_code == 404


def test_blank_photo_cannot_register_person(browser):
    output = io.BytesIO()
    Image.new('RGB', (320, 240), 'white').save(output, 'JPEG')
    response = browser.post('/api/people', json={'name': 'Test', 'image': encoded(output.getvalue())})
    assert response.status_code == 400
    assert browser.get('/api/people').json() == {'people': []}


def test_real_enrollment_match_and_deletion(browser, sample):
    response = browser.post('/api/people', json={'name': 'Deneme Kişisi', 'image': encoded(sample)})
    assert response.status_code == 201, response.text
    person = response.json()
    assert set(person) == {'id', 'name', 'created_at'}
    assert browser.get('/api/people').json()['people'] == [person]
    assert browser.post('/api/people', json={'name': 'Deneme Kişisi', 'image': encoded(sample)}).status_code == 409
    image = browser.post('/api/image', json={'image': encoded(sample)}).json()
    result = browser.post('/api/vision/analyze', json={'image_id': image['id']})
    assert result.status_code == 200, result.text
    data = result.json()
    assert data['image_id'] == image['id']
    assert data['face_count'] == 1
    assert data['faces'][0]['person_id'] == person['id']
    assert data['faces'][0]['name'] == 'Deneme Kişisi'
    assert data['faces'][0]['similarity'] > .95
    assert all(0 <= value <= 1 for value in data['faces'][0]['box'])
    assert browser.delete('/api/people/' + person['id']).status_code == 200
    assert browser.get('/api/people').json() == {'people': []}
    unknown = browser.post('/api/vision/analyze', json={'image_id': image['id']}).json()
    assert unknown['faces'][0]['person_id'] is None
    assert unknown['faces'][0]['name'] == 'Bilinmeyen'


def test_registration_rejects_multiple_faces(browser, sample):
    with Image.open(io.BytesIO(sample)) as original:
        combined = Image.new('RGB', (original.width*2, original.height))
        combined.paste(original, (0, 0))
        combined.paste(original, (original.width, 0))
        output = io.BytesIO()
        combined.save(output, 'JPEG')
    result = browser.post('/api/people', json={'name': 'Test', 'image': encoded(output.getvalue())})
    assert result.status_code == 400
    assert browser.get('/api/people').json() == {'people': []}


def test_ambiguous_match_stays_unknown(browser, sample):
    for name in ['Aday 1', 'Aday 2']:
        assert browser.post('/api/people', json={'name': name, 'image': encoded(sample)}).status_code == 201
    image = browser.post('/api/image', json={'image': encoded(sample)}).json()
    result = browser.post('/api/vision/analyze', json={'image_id': image['id']}).json()
    assert result['faces'][0]['name'] == 'Bilinmeyen'
    assert result['faces'][0]['person_id'] is None


def test_vision_requires_existing_snapshot(browser):
    assert browser.post('/api/vision/analyze', json={'image_id': 'missing'}).status_code == 404


def test_names_cannot_be_empty(browser, sample):
    assert browser.post('/api/people', json={'name': '  ', 'image': encoded(sample)}).status_code == 400


def test_person_registration_blocks_cross_origin(browser, sample):
    assert browser.post('/api/people', json={'name': 'Test', 'image': encoded(sample)}, headers={'Origin': 'https://example.com'}).status_code == 403
    assert browser.get('/api/people').json() == {'people': []}
