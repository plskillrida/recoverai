def calculate_recoverability(transaction):
    """
    Calculate how likely a failed payment is to be recoverable.

    Score range: 0-100
    """

    score = 50
    reasons = []

    amount = transaction["amount"] or 0
    error_code = transaction["error_code"]
    method = transaction["method"]

    # Smaller failed payments are generally easier to recover.
    if amount <= 50000:
        score += 15
        reasons.append("Low-value transaction")

    elif amount <= 200000:
        score += 10
        reasons.append("Moderate-value transaction")

    else:
        score -= 10
        reasons.append("High-value transaction")

    # Some failures are more suitable for recovery attempts.
    if error_code == "BAD_REQUEST_ERROR":
        score += 10
        reasons.append("Potentially recoverable payment error")

    elif error_code == "GATEWAY_ERROR":
        score += 20
        reasons.append("Possible temporary gateway failure")

    elif error_code:
        score -= 5
        reasons.append(f"Payment error: {error_code}")

    # Card payments can potentially be recovered through
    # an alternative payment flow such as a Payment Link.
    if method == "card":
        score += 5
        reasons.append("Alternative payment flow available")

    # Keep score within bounds.
    score = max(0, min(score, 100))

    if score >= 70:
        risk_level = "HIGH"
        recommended_action = "PAYMENT_LINK"

    elif score >= 40:
        risk_level = "MEDIUM"
        recommended_action = "RETRY"

    else:
        risk_level = "LOW"
        recommended_action = "ESCALATE"

    return {
        "score": score,
        "risk_level": risk_level,
        "recommended_action": recommended_action,
        "reasons": reasons,
    }