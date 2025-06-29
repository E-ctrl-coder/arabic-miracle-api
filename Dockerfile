# Use a slim Python image
FROM python:3.11-slim

# Install Java (headless JDK) and unzip for sanity checks
RUN apt-get update && \
    apt-get install -y default-jdk-headless unzip && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /usr/src/app

# Copy all your app files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Render expects
ENV PORT 10000
EXPOSE 10000

# Launch with Gunicorn
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000"]
