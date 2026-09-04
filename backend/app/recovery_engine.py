def analyze_payment(transaction):
    """
    Analyze a failed transaction and determine:
    - whether recovery is appropriate
    - recommended recovery action
    - priority
    - confidence
    - reason for the decision
    """

    status = transaction.get("status")
    method = transaction.get("method")
    error_code = transaction.get("error_code")
    error_description = transaction.get("error_description")

    # --------------------------------------------------
    # 1. Payment must actually be failed
    # --------------------------------------------------

    if status != "failed":
        return {
            "eligible": False,
            "reason": "Payment is not failed",
            "action": "none",
            "priority": "low",
            "confidence": 1.0
        }

    # --------------------------------------------------
    # 2. Missing failure information
    # --------------------------------------------------

    if not error_code:
        return {
            "eligible": False,
            "reason": "Failure reason is unavailable",
            "action": "manual_review",
            "priority": "medium",
            "confidence": 0.60
        }

    # --------------------------------------------------
    # 3. Card payment failure
    # --------------------------------------------------

    if error_code == "BAD_REQUEST_ERROR" and method == "card":

        return {
            "eligible": True,
            "reason": (
                "Card payment failed with a recoverable error. "
                "A secure payment link can allow the customer "
                "to retry the payment."
            ),
            "action": "retry_payment",
            "strategy": "payment_link",
            "priority": "high",
            "confidence": 0.94
        }

    # --------------------------------------------------
    # 4. Other payment methods
    # --------------------------------------------------

    if error_code == "BAD_REQUEST_ERROR":

        return {
            "eligible": True,
            "reason": (
                "Payment failed with a potentially recoverable "
                "error and can be retried."
            ),
            "action": "retry_payment",
            "strategy": "payment_link",
            "priority": "medium",
            "confidence": 0.85
        }

    # --------------------------------------------------
    # 5. Known authentication failures
    # --------------------------------------------------

    if error_code in {
        "AUTHENTICATION_ERROR",
        "GATEWAY_ERROR"
    }:

        return {
            "eligible": False,
            "reason": (
                "Payment infrastructure or authentication "
                "failure detected. Automatic retry is unsafe."
            ),
            "action": "manual_review",
            "priority": "medium",
            "confidence": 0.90
        }

    # --------------------------------------------------
    # 6. Unknown failures
    # --------------------------------------------------

    return {
        "eligible": False,
        "reason": (
            f"Unknown failure type: {error_code}. "
            f"{error_description or ''}".strip()
        ),
        "action": "manual_review",
        "priority": "medium",
        "confidence": 0.65
    }