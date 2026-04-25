FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy only the files needed for dependency resolution first
# This helps with caching
COPY pyproject.toml .python-version ./

# Install dependencies using uv
RUN uv pip install --system -e .

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
