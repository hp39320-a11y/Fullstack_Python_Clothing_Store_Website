# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Collect static files
RUN python storeproject/manage.py collectstatic --noinput

# Expose port (Render sets PORT environment variable, we specify a default just in case)
EXPOSE 8000

# Start command
# We run migrations first to ensure the database schema is up-to-date.
CMD sh -c "python storeproject/manage.py migrate && gunicorn --chdir storeproject --bind 0.0.0.0:${PORT:-8000} storeproject.wsgi:application"
