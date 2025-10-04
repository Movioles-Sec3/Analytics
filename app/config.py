from os import getenv

# Backend base URL for data APIs
# Edit this value or set the environment variable BACKEND_BASE_URL
BACKEND_BASE_URL = getenv("BACKEND_BASE_URL", "http://localhost:8000/")
