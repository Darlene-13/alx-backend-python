# Use python 3.10  as base image
FROM python:3.10

# Set the environment variable to prevent python from writing pyc files and for unbuffered output with logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

#Set the working directory in the container
WORKDIR /messaging_app

# Install MySQL dependencies and PostgreSQL client in one efficient layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        default-libmysqlclient-dev \
        libmariadb-dev \
        build-essential \
        libssl-dev \
        libffi-dev && \
        netcat-openbsd && \
        rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /messaging_app/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /messaging_app/

#Create entrypoint script
COPY entrypoint /messaging_app/entrypoint
RUN chmod +x /messaging_app/entrypoint

# Collect static files if needed
RUN python manage.py collectstatic --noinput || echo "Static files collection skipped"

# Expose port 8000
EXPOSE 8000

# Run the application
ENTRYPOINT ["/messaging_app/entrypoint"]
CMD ["python3", "manage.py", "runserver", "-p", "8000", "0.0.0.0"]