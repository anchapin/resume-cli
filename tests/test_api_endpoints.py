from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import pytest
import os
from api.main import app

client = TestClient(app)

# Mock data
mock_resume_data = {
    "meta": {"version": "1.0"},
    "contact": {"name": "Test User"},
    "experience": []
}

def test_get_variants():
    # Ensure no API key required for this test (dev mode behavior)
    with patch.dict(os.environ, {}, clear=True):
        response = client.get("/v1/variants")
        assert response.status_code == 200
        variants = response.json()
        assert isinstance(variants, dict)
        assert "base" in variants

@patch("api.main.TemplateGenerator")
def test_render_pdf(MockTemplateGenerator):
    # Mock generator instance
    mock_instance = MockTemplateGenerator.return_value

    # Mock generate side effect to create a dummy file
    def side_effect(variant, output_format, output_path):
        with open(output_path, "wb") as f:
            f.write(b"PDF CONTENT")

    mock_instance.generate.side_effect = side_effect

    with patch.dict(os.environ, {}, clear=True):
        response = client.post(
            "/v1/render/pdf",
            json={"resume_data": mock_resume_data, "variant": "base"}
        )

    assert response.status_code == 200
    assert response.content == b"PDF CONTENT"
    assert response.headers["content-type"] == "application/pdf"

@patch("api.main.AIGenerator")
def test_tailor_resume(MockAIGenerator):
    mock_instance = MockAIGenerator.return_value
    mock_instance.tailor_data.return_value = {"tailored": "data"}

    with patch.dict(os.environ, {}, clear=True):
        response = client.post(
            "/v1/tailor",
            json={"resume_data": mock_resume_data, "job_description": "Job desc"}
        )

    assert response.status_code == 200
    assert response.json() == {"tailored": "data"}

def test_auth_failure():
    # Set API key in env
    with patch.dict(os.environ, {"RESUME_API_KEY": "secret"}):
        # Request without key
        response = client.get("/v1/variants")
        assert response.status_code == 403

        # Request with wrong key
        response = client.get("/v1/variants", headers={"X-API-KEY": "wrong"})
        assert response.status_code == 403

        # Request with correct key
        response = client.get("/v1/variants", headers={"X-API-KEY": "secret"})
        assert response.status_code == 200
