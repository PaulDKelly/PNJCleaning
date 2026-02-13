# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (e.g., for MySQL client if needed)
# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libffi-dev

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt



# Copy the rest of the application code
COPY . .

# Expose port 8000 for the app
EXPOSE 8000

# Make the start script executable
RUN chmod +x start.sh

# Run start.sh when the container launches
# Run the application directly to avoid CRLF issues with start.sh
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
