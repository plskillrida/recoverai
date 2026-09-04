const API_BASE = "http://127.0.0.1:8000";


// =====================================================
// FORMAT CURRENCY
// =====================================================

function formatCurrency(amount, currency = "INR") {

    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: currency,
        maximumFractionDigits: 0
    }).format((amount || 0) / 100);

}


// =====================================================
// FORMAT STATUS
// =====================================================

function formatStatus(status) {

    if (!status) {
        return "Not initiated";
    }

    return status
        .replace(/_/g, " ")
        .replace(/\b\w/g, char => char.toUpperCase());

}


// =====================================================
// GET PAYMENT ID
// =====================================================

function getPaymentId() {

    const params =
        new URLSearchParams(
            window.location.search
        );

    return params.get("payment_id");

}


// =====================================================
// VERIFY RECOVERY
// =====================================================

async function verifyRecovery(paymentId) {

    try {

        const response =
            await authenticatedFetch(
                `${API_BASE}/recovery/verify/${encodeURIComponent(
                    paymentId
                )}`
            );


        if (!response.ok) {

            console.warn(
                `Recovery verification failed: ${response.status}`
            );

            return null;
        }


        return await response.json();

    }


    catch (error) {

        console.warn(
            "Recovery verification error:",
            error
        );

        return null;
    }

}


// =====================================================
// LOAD TRANSACTION
// =====================================================

async function loadTransaction() {

    const paymentId =
        getPaymentId();


    if (!paymentId) {

        showError(
            "No payment ID was provided."
        );

        return;
    }


    try {

        const response =
            await authenticatedFetch(
                `${API_BASE}/dashboard/transactions/${encodeURIComponent(
                    paymentId
                )}`
            );


        if (!response.ok) {

            throw new Error(
                `Transaction not found (${response.status})`
            );

        }


        const data =
            await response.json();


        const transaction =
            data.transaction;


        const decision =
            data.decision;


        // ---------------------------------------------
        // PAYMENT SUMMARY
        // ---------------------------------------------

        document.getElementById(
            "amount"
        ).textContent =
            formatCurrency(
                transaction.amount,
                transaction.currency
            );


        document.getElementById(
            "status"
        ).textContent =
            transaction.status
                ? transaction.status.toUpperCase()
                : "-";


        document.getElementById(
            "method"
        ).textContent =
            transaction.method || "-";


        document.getElementById(
            "method-detail"
        ).textContent =
            transaction.method || "-";


        document.getElementById(
            "recovery-status"
        ).textContent =
            formatStatus(
                transaction.recovery_status
            );


        // ---------------------------------------------
        // PAYMENT INFORMATION
        // ---------------------------------------------

        document.getElementById(
            "payment-id"
        ).textContent =
            transaction.payment_id;


        document.getElementById(
            "order-id"
        ).textContent =
            transaction.order_id || "-";


        document.getElementById(
            "currency"
        ).textContent =
            transaction.currency || "-";


        document.getElementById(
            "error-code"
        ).textContent =
            transaction.error_code || "-";


        document.getElementById(
            "error-description"
        ).textContent =
            transaction.error_description || "-";


        document.getElementById(
            "created-at"
        ).textContent =
            transaction.created_at || "-";


        // ---------------------------------------------
        // AI DECISION
        // ---------------------------------------------

        document.getElementById(
            "ai-action"
        ).textContent =
            formatStatus(
                decision?.action ||
                "No action"
            );


        document.getElementById(
            "ai-reason"
        ).textContent =
            decision?.reason ||
            "No reason available.";


        // ---------------------------------------------
        // RECOVERY
        // ---------------------------------------------

        const recoveryArea =
            document.getElementById(
                "recovery-area"
            );


        if (transaction.recovery_link) {

            const verification =
                await verifyRecovery(
                    paymentId
                );


            let recoveryStatus =
                transaction.recovery_status ||
                "initiated";


            let verificationText = "";


            if (verification) {

                if (
                    verification.status ===
                    "recovered"
                ) {

                    recoveryStatus =
                        "recovered";


                    verificationText =
                        "Payment verified by Razorpay";

                }


                else if (
                    verification.status ===
                    "pending"
                ) {

                    recoveryStatus =
                        "pending";


                    verificationText =
                        "Awaiting customer payment";

                }


                else if (
                    verification.status ===
                    "verification_unavailable"
                ) {

                    verificationText =
                        "Verification unavailable";

                }

            }


            recoveryArea.innerHTML = `

                <div class="recovery-info">

                    <div>
                        <span>Status</span>

                        <strong>
                            ${formatStatus(
                                recoveryStatus
                            )}
                        </strong>
                    </div>


                    <div>
                        <span>Recovery Link</span>

                        <strong>
                            ${transaction.recovery_link}
                        </strong>
                    </div>


                    ${
                        verification?.recovery_link_id
                        ?
                        `
                        <div>
                            <span>Payment Link ID</span>

                            <strong>
                                ${verification.recovery_link_id}
                            </strong>
                        </div>
                        `
                        :
                        ""
                    }


                    ${
                        verificationText
                        ?
                        `
                        <div>
                            <span>Verification</span>

                            <strong>
                                ${verificationText}
                            </strong>
                        </div>
                        `
                        :
                        ""
                    }

                </div>


                <br>


                <a
                    href="${transaction.recovery_link}"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="recovery-button"
                >
                    ${
                        recoveryStatus === "recovered"
                        ? "Open Recovery Link"
                        : "Continue Recovery"
                    }
                </a>

            `;

        }


        else {

            recoveryArea.innerHTML = `

                <p>
                    No recovery link has been created
                    for this transaction.
                </p>

            `;

        }


        // ---------------------------------------------
        // SHOW PAGE
        // ---------------------------------------------

        document.getElementById(
            "loading"
        ).style.display = "none";


        document.getElementById(
            "transaction-content"
        ).style.display = "block";

    }


    catch (error) {

        console.error(
            "Transaction loading error:",
            error
        );


        showError(
            error.message
        );

    }

}


// =====================================================
// ERROR
// =====================================================

function showError(message) {

    document.getElementById(
        "loading"
    ).style.display = "none";


    document.getElementById(
        "error"
    ).style.display = "block";


    document.getElementById(
        "error-message"
    ).textContent =
        message;

}


// =====================================================
// INITIALIZE
// =====================================================

document.addEventListener(
    "DOMContentLoaded",
    loadTransaction
);