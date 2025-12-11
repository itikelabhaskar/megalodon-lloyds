FROM python:3.12-slim

# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Set environment variables for Cloud Run
ENV PORT=8080
ENV GOOGLE_GENAI_USE_VERTEXAI=1

WORKDIR /app

# Copy all files first (needed for editable install)
COPY . .

# Upgrade pip to the latest version
RUN pip install --no-cache-dir --upgrade pip
# Install uv
RUN pip install --no-cache-dir uv>=0.7.19

# Install project dependencies, sync to uv's lockfile
RUN uv sync --frozen

# Create .streamlit directory for config
RUN mkdir -p /root/.streamlit

# Create Streamlit config for Cloud Run
RUN echo '[server]\n\
headless = true\n\
port = 8080\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
' > /root/.streamlit/config.toml

# Expose the port
EXPOSE 8080

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8080/_stcore/health || exit 1

# Run Streamlit app
CMD ["uv", "run", "streamlit", "run", "streamlit_app/app.py", "--server.port=8080", "--server.address=0.0.0.0"]
