# Use an official Python runtime as a parent image (slim version is smaller)
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir makes the image smaller
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script into the container at /app
COPY ingest_data.py .

# Command to run when the container launches
CMD ["python", "ingest_data.py"]
