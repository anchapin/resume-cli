import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

# Mock data
mock_resume_data = {"meta": {"version": "1.0"}, "contact": {"name": "Test User"}, "experience": []}


def test_get_variants():
    # Ensure no API key required for this test (dev mode behavior)
    with patch.dict(os.environ, {"RESUME_INSECURE_MODE": "true"}, clear=True):
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

    with patch.dict(os.environ, {"RESUME_INSECURE_MODE": "true"}, clear=True):
        response = client.post(
            "/v1/render/pdf", json={"resume_data": mock_resume_data, "variant": "base"}
        )

    assert response.status_code == 200
    assert response.content == b"PDF CONTENT"
    assert response.headers["content-type"] == "application/pdf"


@patch("api.main.AIGenerator")
def test_tailor_resume(MockAIGenerator):
    mock_instance = MockAIGenerator.return_value
    mock_instance.tailor_data.return_value = {"tailored": "data"}

    with patch.dict(os.environ, {"RESUME_INSECURE_MODE": "true"}, clear=True):
        response = client.post(
            "/v1/tailor", json={"resume_data": mock_resume_data, "job_description": "Job desc"}
        )

    assert response.status_code == 200
    assert response.json() == {"tailored": "data"}


@patch("api.main.TemplateGenerator")
def test_render_pdf_missing_output_file(MockTemplateGenerator):
    """Test that /v1/render/pdf returns 500 when PDF file is not created."""
    # Mock generator instance
    mock_instance = MockTemplateGenerator.return_value

    # Side effect that does not create the expected output file
    def side_effect(variant, output_format, output_path):
        # Intentionally do not create output_path
        return None

    mock_instance.generate.side_effect = side_effect

    with patch.dict(os.environ, {"RESUME_INSECURE_MODE": "true"}, clear=True):
        response = client.post(
            "/v1/render/pdf", json={"resume_data": mock_resume_data, "variant": "base"}
        )

    assert response.status_code == 500
    # Expect JSON error payload with "detail" key (FastAPI default)
    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body
    assert "failed" in body["detail"].lower()


@patch("api.main.TemplateGenerator")
def test_render_pdf_generation_exception(MockTemplateGenerator):
    """Test that /v1/render/pdf returns 500 when PDF generation raises an exception."""
    # Mock generator instance
    mock_instance = MockTemplateGenerator.return_value

    # Simulate an exception during PDF generation
    mock_instance.generate.side_effect = RuntimeError("generation failed")

    with patch.dict(os.environ, {"RESUME_INSECURE_MODE": "true"}, clear=True):
        response = client.post(
            "/v1/render/pdf", json={"resume_data": mock_resume_data, "variant": "base"}
        )

    assert response.status_code == 500
    # Expect JSON error payload with "detail" key
    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body
    assert "failed" in body["detail"].lower()


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


@patch("api.main.AIGenerator")
def test_auth_failure_tailor(MockAIGenerator):
    """Test auth failures for /v1/tailor POST endpoint."""
    # Mock tailor_data to return successfully
    mock_instance = MockAIGenerator.return_value
    mock_instance.tailor_data.return_value = {"tailored": "data"}

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
        response = client.post(
            "/v1/tailor",
            json=payload,
            headers={"X-API-KEY": "secret"},
        )
        assert response.status_code == 200


@patch("api.main.TemplateGenerator")
def test_auth_failure_render_pdf(MockTemplateGenerator):
    """Test auth failures for /v1/render/pdf POST endpoint."""
    # Mock generate to create a dummy PDF file
    mock_instance = MockTemplateGenerator.return_value

    def side_effect(variant, output_format, output_path):
        with open(output_path, "wb") as f:
            f.write(b"PDF CONTENT")

    mock_instance.generate.side_effect = side_effect

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
        response = client.post(
            "/v1/render/pdf",
            json=payload,
            headers={"X-API-KEY": "secret"},
        )
        assert response.status_code == 200


def test_render_pdf_validation_error_missing_resume_data():
    """Test that /v1/render/pdf returns 422 when resume_data is missing."""
    with patch.dict(os.environ, {"RESUME_INSECURE_MODE": "true"}, clear=True):
        response = client.post("/v1/render/pdf", json={"variant": "base"})

    assert response.status_code == 422
    body = response.json()
    assert isinstance(body.get("detail"), list)
    assert body["detail"][0]["loc"][-1] == "resume_data"
    assert "required" in body["detail"][0]["msg"].lower()


@patch("api.main.TemplateGenerator")
def test_render_pdf_uses_default_variant_when_not_specified(MockTemplateGenerator):
    """Test that /v1/render/pdf uses default 'base' variant when not specified."""
    # Mock generator instance
    mock_instance = MockTemplateGenerator.return_value

    def side_effect(variant, output_format, output_path):
        # Verify that variant is 'base' (the default)
        assert variant == "base"
        with open(output_path, "wb") as f:
            f.write(b"PDF CONTENT")

    mock_instance.generate.side_effect = side_effect

    with patch.dict(os.environ, {"RESUME_INSECURE_MODE": "true"}, clear=True):
        # Don't specify variant - should default to "base"
        response = client.post("/v1/render/pdf", json={"resume_data": mock_resume_data})

    assert response.status_code == 200


def test_tailor_validation_error_missing_resume_data():
    """Test that /v1/tailor returns 422 when resume_data is missing."""
    with patch.dict(os.environ, {"RESUME_INSECURE_MODE": "true"}, clear=True):
        response = client.post("/v1/tailor", json={"job_description": "Job desc"})

    assert response.status_code == 422
    body = response.json()
    assert isinstance(body.get("detail"), list)
    assert body["detail"][0]["loc"][-1] == "resume_data"
    assert "required" in body["detail"][0]["msg"].lower()


def test_tailor_validation_error_missing_job_description():
    """Test that /v1/tailor returns 422 when job_description is missing."""
    with patch.dict(os.environ, {"RESUME_INSECURE_MODE": "true"}, clear=True):
        response = client.post("/v1/tailor", json={"resume_data": mock_resume_data})

    assert response.status_code == 422
    body = response.json()
    assert isinstance(body.get("detail"), list)
    assert body["detail"][0]["loc"][-1] == "job_description"
    assert "required" in body["detail"][0]["msg"].lower()
