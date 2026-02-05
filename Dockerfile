FROM python:3.11-slim

# Install system dependencies
# We use a curated list of texlive packages to support PDF generation via Pandoc/XeLaTeX
# without the massive size of texlive-full.
RUN apt-get update && apt-get install -y \
    git \
    pandoc \
    texlive-xetex \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
COPY api/requirements.txt api/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

# Copy source code
COPY . .

# Install the package
RUN pip install -e .

# Expose port
EXPOSE 8000

# Command
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
