# Use a specific, stable Python version for your container.
# Python 3.11 is recommended for broader compatibility and stability.
FROM python:3.11-slim-bookworm 

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container's working directory
COPY requirements.txt .

# Install Python dependencies from the requirements file.
# --no-cache-dir reduces the size of the Docker image.
RUN pip install --no-cache-dir -r requirements.txt

# Copy your server code and schemas.py into the container.
# The `.` means copy all content from the current build context (your voice-assistant-mcp-server folder)
# into the WORKDIR (/app) inside the container.
COPY mcp_server.py .
COPY schemas.py . 

# Expose the port where FastMCP runs.
# This tells Docker that the container listens on this port.
EXPOSE 8000

# Define the command to run your FastMCP server when the container starts.
# `uvicorn <module>:<function_that_returns_app> --host 0.0.0.0 --port 8000`
# This tells Uvicorn to import `mcp_server` module and call the `main()` function within it.
CMD ["uvicorn", "mcp_server:main", "--host", "0.0.0.0", "--port", "8000"]