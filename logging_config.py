import logging.config

# Single toggle for mirroring every log record to stdout in addition to the
# file. Flip this to False to go back to file-only logging.
LOG_TO_CONSOLE = False


class SingleLineFormatter(logging.Formatter):
    """Collapses embedded newlines so one log record is always one physical
    line — multi-line record content (e.g. a ThinkingBlock's text) would
    otherwise split across several unprefixed lines when the file is read
    back line-by-line. Applies after the normal formatting, so it also
    collapses exception tracebacks onto one line; that's an accepted
    tradeoff of the "always one line" guarantee.
    """

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        return formatted.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": SingleLineFormatter,
            "format": "%(asctime)s %(levelname)-8s %(name)s %(actor)-6s->    %(message)s",
            # Records from outside this app (anthropic, httpx2, ...), reaching
            # root's handlers, never carry an "actor" field — this fallback is
            # what stops %(actor)s from raising KeyError on those.
            "defaults": {"actor": ""},
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
        # Mirrors every record the file handler gets, at the same level, to
        # stdout — same formatter, so console lines look identical to the
        # file's. This is separate from (and will appear alongside) the
        # app's own print() calls, which stay as the plain-text console UX.
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "default",
            "level": "DEBUG",
        },
    },
    # This is the app's own namespace (matches the package dir) — DEBUG here
    # is what lets ThinkingBlock content through. propagate=False stops it
    # from also going through root's handler a second time.
    "loggers": {
        "src.filesystem_agent": {
            "handlers": ["file", "console"] if LOG_TO_CONSOLE else ["file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
    # Root catches everything else (anthropic, httpx2, httpcore2, ...) at
    # WARNING+ only — their INFO/DEBUG internals (full request/response
    # dumps, TLS handshake steps) would otherwise flood this file.
    "root": {
        "handlers": ["file", "console"] if LOG_TO_CONSOLE else ["file"],
        "level": "WARNING",
    },
}


def setup_logging() -> None:
    logging.config.dictConfig(LOGGING)
