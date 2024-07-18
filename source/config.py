from os import environ
from dotenv import load_dotenv


load_dotenv()

JWT_SECRET = environ['JWT_SECRET']

SECRET_KEY = environ['SECRET_KEY']

TORTOISE_CONFIG = {
    "connections": {
        "test_task": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {
                "file_path": ".test.db",
                "foreign_keys": "ON",
            },
        }
    },
    "apps": {
        "api": {"models": ["models"], "default_connection": "test_task"}
    }
}