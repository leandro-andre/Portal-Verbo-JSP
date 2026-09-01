import resend


class ResendEmailClient:
    provider = "resend"

    def __init__(self, api_key):
        self.api_key = api_key

    def send(self, params, *, idempotency_key=None):
        resend.api_key = self.api_key
        options = {"idempotency_key": idempotency_key} if idempotency_key else None
        return resend.Emails.send(params, options)
