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

@patch("api.main.TemplateGenerator")
def test_render_pdf_missing_output_file(MockTemplateGenerator):
    # Mock generator instance
    mock_instance = MockTemplateGenerator.return_value

    # Side effect that does not create the expected output file
    def side_effect(variant, output_format, output_path):
        # Intentionally do not create output_path
        return None

    mock_instance.generate.side_effect = side_effect

    with patch.dict(os.environ, {}, clear=True):
        response = client.post(
            "/v1/render/pdf",
            json={"resume_data": mock_resume_data, "variant": "base"}
        )

    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == "PDF generation failed"

@patch("api.main.TemplateGenerator")
def test_render_pdf_generation_exception(MockTemplateGenerator):
    # Mock generator instance
    mock_instance = MockTemplateGenerator.return_value

    # Simulate an exception during PDF generation
    mock_instance.generate.side_effect = RuntimeError("generation failed")

    with patch.dict(os.environ, {}, clear=True):
        response = client.post(
            "/v1/render/pdf",
            json={"resume_data": mock_resume_data, "variant": "base"}
        )

    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == "PDF generation failed"

def test_auth_failure_get_variants():
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

def test_auth_failure_tailor():
    # Set API key in env
    with patch.dict(os.environ, {"RESUME_API_KEY": "secret"}):
        payload = {
            "resume_data": mock_resume_data,
            "job_description": "Job desc",
        }

        # Request without key
        response = client.post("/v1/tailor", json=payload)
        assert response.status_code == 403

        # Request with wrong key
        response = client.post(
            "/v1/tailor",
            json=payload,
            headers={"X-API-KEY": "wrong"},
        )
        assert response.status_code == 403

        # Request with correct key
        # Mock AIGenerator to avoid actual call
        with patch("api.main.AIGenerator") as MockAIGenerator:
             MockAIGenerator.return_value.tailor_data.return_value = {}
             response = client.post(
                "/v1/tailor",
                json=payload,
                headers={"X-API-KEY": "secret"},
            )
        assert response.status_code == 200

def test_auth_failure_render_pdf():
    # Set API key in env
    with patch.dict(os.environ, {"RESUME_API_KEY": "secret"}):
        payload = {"resume_data": mock_resume_data, "variant": "base"}

        # Request without key
        response = client.post("/v1/render/pdf", json=payload)
        assert response.status_code == 403

        # Request with wrong key
        response = client.post(
            "/v1/render/pdf",
            json=payload,
            headers={"X-API-KEY": "wrong"},
        )
        assert response.status_code == 403

        # Request with correct key
        # Mock TemplateGenerator
        with patch("api.main.TemplateGenerator") as MockGen:
            # Side effect to create file
            def side_effect(variant, output_format, output_path):
                with open(output_path, "wb") as f:
                    f.write(b"PDF")
            MockGen.return_value.generate.side_effect = side_effect

            response = client.post(
                "/v1/render/pdf",
                json=payload,
                headers={"X-API-KEY": "secret"},
            )
        assert response.status_code == 200
