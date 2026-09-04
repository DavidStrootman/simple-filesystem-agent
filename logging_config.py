import logging.config

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "agent.log",
            "maxBytes": 1_000_000,
            "backupCount": 3,
            "formatter": "default",
            "level": "DEBUG",
        },
    },
    # This is the app's own namespace (matches the package dir) — DEBUG here
    # is what lets ThinkingBlock content through. propagate=False stops it
    # from also going through root's handler a second time.
    "loggers": {
        "src.filesystem_agent": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
    # Root catches everything else (anthropic, httpx2, httpcore2, ...) at
    # WARNING+ only — their INFO/DEBUG internals (full request/response
    # dumps, TLS handshake steps) would otherwise flood this file.
    # No console handler anywhere — print() elsewhere in the app remains
    # the console-facing UX and is untouched by this configuration.
    "root": {
        "handlers": ["file"],
        "level": "WARNING",
    },
}


def setup_logging() -> None:
    logging.config.dictConfig(LOGGING)
