# pan-rag-assignement/Dockerfile

# Use a lightweight Python base image with Debian 11 (Bullseye)
FROM python:3.10-slim-bullseye

# Install necessary system-level build tools and libraries for faiss-cpu,
# psycopg2-binary (PostgreSQL client), and poppler-utils (for PyPDFLoader).
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libblas-dev \
        liblapack-dev \
        gfortran \
        libssl-dev \
        libopenblas-dev \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker's build cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
# This copies your 'app' directory, and any other project files
COPY ./app /app/app

# Expose the port your FastAPI application will run on
EXPOSE 8000

# Command to run the FastAPI application with Uvicorn
# 'app.main:app' assumes your FastAPI app instance is named 'app' in 'app/main.py'
# '--host 0.0.0.0' makes the app accessible from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]