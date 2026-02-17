import logging
import tempfile
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException, Response, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from api.auth import get_api_key
from api.models import (
    ATSRequest,
    CoverLetterRequest,
    ResumeRequest,
    TailorRequest,
)
from cli.generators.ai_generator import AIGenerator
from cli.generators.ats_generator import ATSGenerator
from cli.generators.cover_letter_generator import CoverLetterGenerator
from cli.generators.template import TemplateGenerator
from cli.utils.config import Config

# Configure logging
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Resume CLI API",
    version="1.0.0",
    description="""
## Overview

Resume CLI API provides programmatic access to resume generation, tailoring, and analysis features.

## Authentication

All endpoints (except `/health`) require an API key passed via the `X-API-Key` header.

## Features

- **Resume Rendering**: Generate PDF resumes from YAML data
- **AI Tailoring**: Customize resume content for specific job descriptions
- **ATS Checking**: Analyze resume compatibility with applicant tracking systems
- **Cover Letters**: Generate personalized cover letters for job applications
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def custom_openapi():
    """Generate custom OpenAPI schema with security scheme."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Resume CLI API",
        version="1.0.0",
        description="""
## Overview

Resume CLI API provides programmatic access to resume generation, tailoring, and analysis features.

## Authentication

All endpoints (except `/health`) require an API key passed via the `X-API-Key` header.

## Features

- **Resume Rendering**: Generate PDF resumes from YAML data
- **AI Tailoring**: Customize resume content for specific job descriptions
- **ATS Checking**: Analyze resume compatibility with applicant tracking systems
- **Cover Letters**: Generate personalized cover letters for job applications
        """,
        routes=app.routes,
    )

    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication. Get this from the `API_KEY` environment variable.",
        }
    }

    # Add security requirement to all endpoints except health
    for path, path_item in openapi_schema["paths"].items():
        if path != "/health":
            for method, method_item in path_item.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    method_item["security"] = [{"ApiKeyAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {"status": "healthy", "service": "resume-api"}


@app.get(
    "/v1/variants",
    dependencies=[Security(get_api_key)],
    summary="List available resume variants",
    description="Returns all configured resume variants from the default configuration. Variants define different resume configurations for different job types.",
    response_description="JSON object containing variant configurations",
    responses={
        200: {"description": "Successfully retrieved variant list"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def get_variants():
    config = Config()  # Uses default config path logic
    return config.get("variants")


@app.post(
    "/v1/render/pdf",
    dependencies=[Security(get_api_key)],
    summary="Render resume as PDF",
    description="Generates a PDF resume from the provided resume data using the specified variant template.",
    response_description="PDF file binary for download",
    responses={
        200: {"description": "PDF file successfully generated"},
        400: {"description": "Invalid request data"},
        401: {"description": "Invalid or missing API key"},
        500: {"description": "PDF generation failed"},
    },
)
async def render_pdf(request: ResumeRequest):
    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        resume_yaml_path = temp_path / "resume.yaml"

        # Dump resume_data to resume.yaml
        with open(resume_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(request.resume_data, f, default_flow_style=False)

        try:
            generator = TemplateGenerator(yaml_path=resume_yaml_path)

            # Generate PDF
            # We output to a temp file
            output_pdf = temp_path / "output.pdf"

            generator.generate(variant=request.variant, output_format="pdf", output_path=output_pdf)

            if not output_pdf.exists():
                raise HTTPException(status_code=500, detail="PDF generation failed")

            # Read bytes
            content = output_pdf.read_bytes()

            return Response(
                content=content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=resume-{request.variant}.pdf"
                },
            )

        except Exception as e:
            # Log the full exception for debugging
            logger.exception("Error during PDF generation", exc_info=e)
            # Return generic error message to client
            raise HTTPException(status_code=500, detail="PDF generation failed")


@app.post(
    "/v1/tailor",
    dependencies=[Security(get_api_key)],
    summary="AI-tailor resume for job description",
    description="Uses AI to customize resume content for a specific job description. Highlights relevant skills, reorders experience bullets, and emphasizes matching qualifications.",
    response_description="AI-tailored resume data in JSON format",
    responses={
        200: {"description": "Resume successfully tailored"},
        400: {"description": "Invalid request data"},
        401: {"description": "Invalid or missing API key"},
        500: {"description": "Resume tailoring failed"},
    },
)
async def tailor_resume(request: TailorRequest):
    try:
        # Initialize AI Generator
        config = Config()

        # We pass None for yaml_path as we use direct data
        generator = AIGenerator(yaml_path=None, config=config)

        tailored_data = generator.tailor_data(
            resume_data=request.resume_data, job_description=request.job_description
        )

        return tailored_data

    except Exception as e:
        # Log the full exception for debugging
        logger.exception("Error during resume tailoring", exc_info=e)
        # Return generic error message to client
        raise HTTPException(status_code=500, detail="Resume tailoring failed")


@app.post(
    "/v1/ats/check",
    dependencies=[Security(get_api_key)],
    summary="Check ATS compatibility score",
    description="Analyzes a resume against a job description to determine compatibility with Applicant Tracking Systems (ATS). Provides scores across multiple categories including format, keywords, section structure, contact info, and readability.",
    response_description="JSON object containing ATS score breakdown and recommendations",
    responses={
        200: {"description": "ATS check completed successfully"},
        400: {"description": "Invalid request data"},
        401: {"description": "Invalid or missing API key"},
        500: {"description": "ATS check failed"},
    },
)
async def ats_check(request: ATSRequest):
    """Check ATS compatibility score for a resume against a job description."""
    try:
        config = Config()

        # Create temporary YAML file from resume_data
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            resume_yaml_path = temp_path / "resume.yaml"

            with open(resume_yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(request.resume_data, f, default_flow_style=False)

            # Generate ATS report
            generator = ATSGenerator(yaml_path=resume_yaml_path, config=config)
            report = generator.generate_report(request.job_description, request.variant)

            # Convert to JSON-serializable format
            result = {
                "total_score": report.total_score,
                "total_possible": report.total_possible,
                "overall_percentage": report.overall_percentage,
                "summary": report.summary,
                "categories": {
                    name: {
                        "name": cat.name,
                        "score": cat.points_earned,
                        "max_score": cat.points_possible,
                        "percentage": cat.percentage,
                        "details": cat.details,
                        "suggestions": cat.suggestions,
                    }
                    for name, cat in report.categories.items()
                },
                "recommendations": report.recommendations,
            }

            return result

    except Exception as e:
        logger.exception("Error during ATS check", exc_info=e)
        raise HTTPException(status_code=500, detail="ATS check failed")


@app.post(
    "/v1/cover-letter",
    dependencies=[Security(get_api_key)],
    summary="Generate cover letter",
    description="Generates a personalized cover letter for a job application. Supports both interactive mode (with user responses) and non-interactive mode (AI-generated content). Can output in Markdown or PDF format.",
    response_description="JSON object containing generated cover letter content",
    responses={
        200: {"description": "Cover letter generated successfully"},
        400: {"description": "Invalid request data"},
        401: {"description": "Invalid or missing API key"},
        500: {"description": "Cover letter generation failed"},
    },
)
async def generate_cover_letter(request: CoverLetterRequest):
    """Generate a cover letter for a job application."""
    try:
        config = Config()

        # Create temporary YAML file from resume_data
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            resume_yaml_path = temp_path / "resume.yaml"

            with open(resume_yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(request.resume_data, f, default_flow_style=False)

            # Initialize cover letter generator
            generator = CoverLetterGenerator(yaml_path=resume_yaml_path, config=config)

            # Generate cover letter (always use non-interactive for API)
            # The provided answers will be used as context by the AI
            outputs, job_details = generator.generate_non_interactive(
                job_description=request.job_description,
                company_name=request.company_name,
                variant=request.variant,
                output_formats=[request.format],
            )

            # Return the generated content
            # Note: outputs["md"] contains the rendered markdown, outputs["pdf"] contains LaTeX
            if request.format == "md" and "md" in outputs:
                return {
                    "content": outputs["md"],
                    "format": "md",
                    "company": job_details.get("company", request.company_name or "Company"),
                    "position": job_details.get("position", ""),
                }
            elif request.format == "pdf" and "pdf" in outputs:
                # Compile LaTeX to PDF
                pdf_path = temp_path / "cover-letter.pdf"
                if generator._compile_pdf(pdf_path, outputs["pdf"]):
                    import base64

                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    return {
                        "content": base64.b64encode(pdf_bytes).decode("utf-8"),
                        "format": "pdf",
                        "company": job_details.get("company", request.company_name or "Company"),
                        "position": job_details.get("position", ""),
                    }
                else:
                    # Return LaTeX as fallback
                    return {
                        "content": outputs["pdf"],
                        "format": "tex",
                        "company": job_details.get("company", request.company_name or "Company"),
                        "position": job_details.get("position", ""),
                        "note": "PDF compilation failed, returning LaTeX",
                    }
            else:
                raise HTTPException(status_code=500, detail="Cover letter generation failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during cover letter generation", exc_info=e)
        raise HTTPException(status_code=500, detail="Cover letter generation failed")


# =========================================================================
# Analytics Endpoints for Dashboard
# =========================================================================
