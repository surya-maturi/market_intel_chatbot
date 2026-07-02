class UpstreamServiceError(Exception):
    """Raised when an external API call fails after retries are exhausted."""


class IntentClassificationError(Exception):
    """Raised when the LLM intent response cannot be parsed/validated."""
