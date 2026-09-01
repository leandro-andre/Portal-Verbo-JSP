class EmailConfigurationError(Exception):
    """Raised when transactional e-mail is not configured for sending."""


class EmailDeliveryError(Exception):
    """Raised when the transactional e-mail provider rejects or fails a send."""
