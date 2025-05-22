import os

import dj_database_url

from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        conn_max_age=0,
        conn_health_checks=True,
        ssl_require=False,
    ),
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Disabling these because it's enforced at the ingress level on GKE
# SECURE_HSTS_SECONDS = 60
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 60
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.mailgun.org"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = "noreply@mail.attendee.dev"
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_EMAIL_VERIFICATION = "optional"

ADMINS = []

if os.getenv("ERROR_REPORTS_RECEIVER_EMAIL_ADDRESS"):
    ADMINS.append(
        (
            "Attendee Error Reports Email Receiver",
            os.getenv("ERROR_REPORTS_RECEIVER_EMAIL_ADDRESS"),
        )
    )

SERVER_EMAIL = "noreply@mail.attendee.dev"

# Needed on GKE
CSRF_TRUSTED_ORIGINS = ["https://*.attendee.dev"]

csrf_origins = os.getenv("CSRF_TRUSTED_ORIGINS")
if csrf_origins:
    CSRF_TRUSTED_ORIGINS = csrf_origins.split(",")


# Log more stuff in staging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
