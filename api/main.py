from fastapi import FastAPI, HTTPException, Security, Depends, Response
from fastapi.responses import JSONResponse
import tempfile
import shutil
import os
import json
import yaml
import logging
from pathlib import Path

from api.models import ResumeRequest, TailorRequest
from api.auth import get_api_key
from cli.generators.template import TemplateGenerator
from cli.generators.ai_generator import AIGenerator
from cli.utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Resume API", version="1.0.0")

@app.get("/v1/variants", dependencies=[Security(get_api_key)])
async def get_variants():
    config = Config() # Uses default config path logic
    return config.get("variants")

@app.post("/v1/render/pdf", dependencies=[Security(get_api_key)])
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

            generator.generate(
                variant=request.variant,
                output_format="pdf",
                output_path=output_pdf
            )

            if not output_pdf.exists():
                logger.error("PDF file was not created by generator")
                raise HTTPException(status_code=500, detail="PDF generation failed")

            # Read bytes
            content = output_pdf.read_bytes()

            return Response(
                content=content,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=resume-{request.variant}.pdf"}
            )

        except HTTPException:
            raise
        except Exception as e:
            # Clean up handled by TemporaryDirectory, but catching to return error
            logger.exception("Error during PDF generation", exc_info=e)
            raise HTTPException(status_code=500, detail="PDF generation failed")

@app.post("/v1/tailor", dependencies=[Security(get_api_key)])
async def tailor_resume(request: TailorRequest):
    try:
        # Initialize AI Generator
        config = Config()

        # We pass None for yaml_path as we use direct data
        generator = AIGenerator(yaml_path=None, config=config)

        tailored_data = generator.tailor_data(
            resume_data=request.resume_data,
            job_description=request.job_description
        )

        return tailored_data

    except Exception as e:
        logger.exception("Error during resume tailoring", exc_info=e)
        raise HTTPException(status_code=500, detail="Tailoring failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
