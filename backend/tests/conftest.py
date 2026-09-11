import os

# Must be set before app.config is imported, since Settings validates JWT_SECRET
# at import time and the test suite has no .env to read.
os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-32-characters-long")
