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

@app.get(
    "/v1/analytics/overview",
    dependencies=[Security(get_api_key)],
    summary="Get dashboard overview metrics",
    description="Returns key metrics for the dashboard overview including response rate, interview rate, offer rate, and total counts.",
    response_description="JSON object containing overview metrics",
    responses={
        200: {"description": "Successfully retrieved overview metrics"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def get_analytics_overview():
    """Get overview metrics for the dashboard."""
    try:
        from cli.integrations.tracking import TrackingIntegration

        config = Config()
        tracker = TrackingIntegration(config)
        return tracker.get_response_rate_gauge()
    except Exception as e:
        logger.exception("Error getting analytics overview", exc_info=e)
        return {
            "response_rate": 0,
            "interview_rate": 0,
            "offer_rate": 0,
            "total_applications": 0,
            "interviews": 0,
            "offers": 0,
        }


@app.get(
    "/v1/analytics/by-status",
    dependencies=[Security(get_api_key)],
    summary="Get applications by status",
    description="Returns application counts grouped by status (applied, interview, offer, rejected, etc.). Useful for pie chart visualization.",
    response_description="JSON object mapping status to count",
    responses={
        200: {"description": "Successfully retrieved status breakdown"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def get_analytics_by_status():
    """Get application counts by status."""
    try:
        from cli.integrations.tracking import TrackingIntegration

        config = Config()
        tracker = TrackingIntegration(config)
        return tracker.get_applications_by_status()
    except Exception as e:
        logger.exception("Error getting analytics by status", exc_info=e)
        return {}


@app.get(
    "/v1/analytics/timeline",
    dependencies=[Security(get_api_key)],
    summary="Get applications timeline",
    description="Returns daily application counts for the specified time period. Useful for line chart visualization.",
    response_description="Array of objects with date and count",
    responses={
        200: {"description": "Successfully retrieved timeline data"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def get_analytics_timeline(days: int = 90):
    """
    Get application timeline data.

    Args:
        days: Number of days to look back (default: 90)
    """
    try:
        from cli.integrations.tracking import TrackingIntegration

        config = Config()
        tracker = TrackingIntegration(config)
        return tracker.get_applications_timeline(days=days)
    except Exception as e:
        logger.exception("Error getting analytics timeline", exc_info=e)
        return []


@app.get(
    "/v1/analytics/variants",
    dependencies=[Security(get_api_key)],
    summary="Get variant performance metrics",
    description="Returns performance metrics for each resume variant including response rate, interview rate, and offer rate. Useful for bar chart comparison.",
    response_description="Array of variant performance objects",
    responses={
        200: {"description": "Successfully retrieved variant performance data"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def get_analytics_variants():
    """Get performance metrics by resume variant."""
    try:
        from cli.integrations.tracking import TrackingIntegration

        config = Config()
        tracker = TrackingIntegration(config)
        return tracker.get_variant_performance()
    except Exception as e:
        logger.exception("Error getting variant analytics", exc_info=e)
        return []


@app.get(
    "/v1/analytics/companies",
    dependencies=[Security(get_api_key)],
    summary="Get company analytics",
    description="Returns analytics grouped by company including application counts, statuses, and roles.",
    response_description="Array of company analytics objects",
    responses={
        200: {"description": "Successfully retrieved company analytics"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def get_analytics_companies():
    """Get analytics by company."""
    try:
        from cli.integrations.tracking import TrackingIntegration

        config = Config()
        tracker = TrackingIntegration(config)
        return tracker.get_company_analytics()
    except Exception as e:
        logger.exception("Error getting company analytics", exc_info=e)
        return []


@app.get(
    "/v1/analytics/sources",
    dependencies=[Security(get_api_key)],
    summary="Get application source breakdown",
    description="Returns application counts by source (LinkedIn, Direct, Referral, etc.).",
    response_description="Array of source breakdown objects",
    responses={
        200: {"description": "Successfully retrieved source breakdown"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def get_analytics_sources():
    """Get application counts by source."""
    try:
        from cli.integrations.tracking import TrackingIntegration

        config = Config()
        tracker = TrackingIntegration(config)
        return tracker.get_source_breakdown()
    except Exception as e:
        logger.exception("Error getting source analytics", exc_info=e)
        return []


@app.get(
    "/v1/analytics/dashboard",
    dependencies=[Security(get_api_key)],
    summary="Get complete dashboard data",
    description="Returns all dashboard metrics in a single response including overview, status breakdown, timeline, variant performance, company analytics, and source breakdown.",
    response_description="Comprehensive dashboard data object",
    responses={
        200: {"description": "Successfully retrieved complete dashboard data"},
        401: {"description": "Invalid or missing API key"},
    },
)
async def get_dashboard_data():
    """Get complete dashboard data."""
    try:
        from cli.integrations.tracking import TrackingIntegration

        config = Config()
        tracker = TrackingIntegration(config)
        return tracker.get_dashboard_data()
    except Exception as e:
        logger.exception("Error getting dashboard data", exc_info=e)
        return {
            "overview": {},
            "by_status": {},
            "timeline": [],
            "variant_performance": [],
            "company_analytics": [],
            "source_breakdown": [],
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
