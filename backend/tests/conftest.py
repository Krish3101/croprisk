import os

# Must be set before app.config is imported, since Settings validates JWT_SECRET
# at import time.
os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-32-characters-long")

# Environment variables win over backend/.env, so blank the keys here. Otherwise a
# developer's real keys would send the tests to OpenWeather and OpenRouter.
os.environ["OPENWEATHER_API_KEY"] = ""
os.environ["OPENROUTER_API_KEY"] = ""
