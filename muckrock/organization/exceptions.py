"""Exceptions for the organization application."""


class PaymentActionRequired(Exception):
    """Raised when a charge requires client-side 3DS/SCA confirmation.

    Carries the client_secret needed for stripe.confirmCardPayment() and the
    payment_intent_id for the follow-up confirmation request to squarelet.
    """

    def __init__(self, client_secret, payment_intent_id):
        self.client_secret = client_secret
        self.payment_intent_id = payment_intent_id
        super().__init__(f"Payment requires action: {payment_intent_id}")
