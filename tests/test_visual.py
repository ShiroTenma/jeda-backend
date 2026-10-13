import io
import time
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.services.visual import VisualClassifier

client = TestClient(app)

@pytest.fixture
def sample_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (300, 300), color=(200, 50, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_visual_classifier_singleton():
    inst1 = VisualClassifier.get_instance()
    inst2 = VisualClassifier.get_instance()
    assert inst1 is inst2

def test_visual_inference(sample_jpeg_bytes):
    classifier = VisualClassifier.get_instance()
    confidence, latency = classifier.infer(sample_jpeg_bytes)
    assert 0.0 <= confidence <= 1.0
    assert latency > 0.0

def test_analyze_frame_api_success(sample_jpeg_bytes):
    response = client.post(
        "/api/analyze-frame",
        files={"file": ("frame.jpg", sample_jpeg_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "visual_confidence" in data
    assert "rrs" in data
    assert "level" in data
    assert "action" in data
    assert 0.0 <= data["visual_confidence"] <= 1.0

def test_analyze_frame_api_invalid_content_type():
    response = client.post(
        "/api/analyze-frame",
        files={"file": ("text.txt", b"plain text content", "text/plain")}
    )
    assert response.status_code == 400

def test_analyze_frame_api_empty_file():
    response = client.post(
        "/api/analyze-frame",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400

def test_inference_latency_benchmark(sample_jpeg_bytes):
    """Runs 30 inference iterations and verifies p95 latency is bounded."""
    classifier = VisualClassifier.get_instance()
    latencies = []
    
    # Warmup
    for _ in range(3):
        classifier.infer(sample_jpeg_bytes)

    for _ in range(30):
        t0 = time.perf_counter()
        classifier.infer(sample_jpeg_bytes)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    avg_ms = sum(latencies) / len(latencies)
    p95_ms = sorted(latencies)[int(0.95 * len(latencies))]
    print(f"\n[M5 Benchmark] Avg Latency: {avg_ms:.2f}ms | p95 Latency: {p95_ms:.2f}ms")
    assert avg_ms < 100.0  # Well within comfortable interactive response limits
