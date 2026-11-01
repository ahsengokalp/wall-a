import base64
import importlib
import io

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image

backend = importlib.import_module('server.app')


@pytest.fixture
def browser():
    backend.images.clear()
    with TestClient(backend.app) as connection:
        yield connection


def picture_bytes():
    output = io.BytesIO()
    Image.new('RGB', (80, 60), 'red').save(output, 'PNG')
    return output.getvalue()


def upload(browser):
    response = browser.post('/api/image', json={'image': base64.b64encode(picture_bytes()).decode()})
    assert response.status_code == 200
    return response.json()


def mock_network(monkeypatch, handler):
    monkeypatch.setattr(backend, 'client', lambda timeout=10: httpx.Client(transport=httpx.MockTransport(handler)))


def test_home_and_assets(browser):
    assert 'Önce dünyayı görelim.' in browser.get('/').text
    assert browser.get('/static/app.js').status_code == 200
    assert browser.get('/static/style.css').status_code == 200


def test_upload_real_image_and_reject_invalid(browser):
    image = upload(browser)
    assert (image['width'], image['height']) == (80, 60)
    assert base64.b64decode(image['image']).startswith(b'\xff\xd8')
    assert browser.post('/api/image', json={'image': 'invalid!'}).status_code == 400
    assert browser.post('/api/image', json={'image': base64.b64encode(b'not a photo').decode()}).status_code == 400


def test_memory_eviction(browser):
    oldest = upload(browser)['id']
    for _ in range(8):
        upload(browser)
    assert len(backend.images) == 8
    assert oldest not in backend.images


@pytest.mark.parametrize('address', ['127.0.0.1', '169.254.169.254', '8.8.8.8', 'localhost', 'http://192.168.1.5:11434', 'http://192.168.1.5/other', 'https://192.168.1.5', 'http://user:pass@192.168.1.5', 'http://[broken'])
def test_camera_rejects_non_device_targets(browser, address):
    assert browser.post('/api/capture', json={'address': address}).status_code == 400


def test_capture_real_image_contract(browser, monkeypatch):
    def handler(request):
        assert str(request.url) == 'http://192.168.1.50/capture'
        return httpx.Response(200, content=picture_bytes())
    mock_network(monkeypatch, handler)
    response = browser.post('/api/capture', json={'address': '192.168.1.50'})
    assert response.status_code == 200
    assert response.json()['source'].startswith('ESP32')


def test_capture_does_not_follow_redirect(browser, monkeypatch):
    mock_network(monkeypatch, lambda request: httpx.Response(302, headers={'Location': 'http://127.0.0.1:11434'}))
    assert browser.post('/api/capture', json={'address': '192.168.1.50'}).status_code == 502


def test_ollama_offline_is_visible(browser, monkeypatch):
    def offline(request):
        raise httpx.ConnectError('offline')
    mock_network(monkeypatch, offline)
    assert browser.get('/api/health').json()['ollama'] is False
    assert browser.get('/api/models').status_code == 503


def test_vision_question_uses_selected_snapshot(browser, monkeypatch):
    import json
    image = upload(browser)
    def handler(request):
        if request.url.path == '/api/tags':
            return httpx.Response(200, json={'models': [{'name': 'local:2b'}]})
        if request.url.path == '/api/show':
            return httpx.Response(200, json={'capabilities': ['vision']})
        payload = json.loads(request.content)
        assert payload['messages'][-1]['images'] == [image['image']]
        assert payload['messages'][-1]['content'] == 'Ne görüyorsun?'
        assert payload['stream'] is False
        assert payload['options']['num_gpu'] == 0
        return httpx.Response(200, json={'message': {'content': 'Kırmızı bir alan.'}, 'total_duration': 2_000_000_000})
    mock_network(monkeypatch, handler)
    response = browser.post('/api/ask', json={'image_id': image['id'], 'model': 'local:2b', 'question': 'Ne görüyorsun?'})
    assert response.status_code == 200
    assert response.json()['answer'] == 'Kırmızı bir alan.'
    assert response.json()['duration_seconds'] == 2


def test_text_only_model_cannot_analyze_photo(browser, monkeypatch):
    image = upload(browser)
    def handler(request):
        return httpx.Response(200, json={'models': [{'name': 'text:1b'}]} if request.url.path == '/api/tags' else {'capabilities': ['completion']})
    mock_network(monkeypatch, handler)
    assert browser.post('/api/ask', json={'image_id': image['id'], 'model': 'text:1b', 'question': 'Ne var?'}).status_code == 400


def test_cloud_models_are_excluded(browser, monkeypatch):
    mock_network(monkeypatch, lambda request: httpx.Response(200, json={'models': [{'name': 'remote:cloud', 'remote_host': 'https://ollama.com'}]}))
    assert browser.get('/api/models').json() == {'models': []}


def test_cross_origin_requests_blocked(browser):
    response = browser.post('/api/capture', json={'address': '192.168.1.50'}, headers={'Origin': 'https://example.com'})
    assert response.status_code == 403


def test_missing_snapshot_and_empty_question(browser):
    assert browser.post('/api/ask', json={'image_id': 'missing', 'model': 'local:2b', 'question': 'Ne var?'}).status_code == 404
    assert browser.post('/api/ask', json={'image_id': 'missing', 'model': 'local:2b', 'question': '  '}).status_code == 400
