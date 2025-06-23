# Use python 3.10  as base image
FROM python:3.10

# Set the environment variable to prevent python from writing pyc files and for unbuffered output with logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

#Set the working directory in the container
WORKDIR /messaging_app

#Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /messaging_app/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /messaging_app/

# Collect static files if needed
RUN python manage.py collectstatic --noinput

# Expose port 8000
EXPOSE 8000

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]