import os

from utils.main import str_to_bool

SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = bool(str_to_bool(os.getenv("FLASK_DEBUG", "false")))

SERVER_NAME = os.getenv(
    "SERVER_NAME", "localhost:{0}".format(os.getenv("PORT", "8000"))
)
# SQLAlchemy.
pg_user = os.getenv("POSTGRES_USER", "ops")
pg_pass = os.getenv("POSTGRES_PASSWORD", "password")
pg_host = os.getenv("POSTGRES_HOST", "postgres")
pg_port = os.getenv("POSTGRES_PORT", "5432")
pg_db = os.getenv("POSTGRES_DB", pg_user)
db = f"postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", db)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Redis.
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Configure Pusher (you can leave the last 2 settings alone).
PUSHER_APP_ID = os.getenv("PUSHER_APP_ID", "123")
PUSHER_KEY = os.getenv("PUSHER_KEY", "123")
PUSHER_SECRET = os.getenv("PUSHER_SECRET", "123")
PUSHER_CLUSTER = os.getenv("PUSHER_CLUSTER", "us2")
PUSHER_SSL = True
PUSHER_AUTH_ENDPOINT = "/api/auth/pusher/"

# Configure AZURE OPENAI API
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", None)
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", None)

# Celery.
CELERY_CONFIG = {
    "broker_url": REDIS_URL,
    "result_backend": REDIS_URL,
    "include": [],
}
