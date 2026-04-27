# Use Microsoft's mirrored Python image to avoid Docker Hub rate limits in ACR builds
FROM mcr.microsoft.com/devcontainers/python:3.9-bookworm

# Set the working directory in the container
WORKDIR /app

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

# Run the application directly and honor Railway's injected PORT variable
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
