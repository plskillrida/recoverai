const API_BASE = "http://127.0.0.1:8000";


// =====================================================
// CURRENCY
// =====================================================

function formatCurrency(
    amount,
    currency = "INR"
) {

    return new Intl.NumberFormat(
        "en-IN",
        {
            style: "currency",
            currency: currency,
            maximumFractionDigits: 0
        }
    ).format(
        (amount || 0) / 100
    );
}


// =====================================================
// DASHBOARD SUMMARY
// =====================================================

async function loadDashboard() {

    try {

        const response =
            await authenticatedFetch(
                `${API_BASE}/dashboard/summary`
            );


        if (!response.ok) {

            throw new Error(
                `Dashboard request failed: ${response.status}`
            );

        }


        const data =
            await response.json();


        // =================================================
        // REVENUE AT RISK
        // =================================================

        const riskElement =
            document.getElementById(
                "revenue-risk"
            );


        if (riskElement) {

            riskElement.textContent =
                formatCurrency(
                    data.revenue_at_risk
                );

        }


        // =================================================
        // REVENUE RECOVERED
        // =================================================

        const recoveredElement =
            document.getElementById(
                "revenue-recovered"
            );


        if (recoveredElement) {

            recoveredElement.textContent =
                formatCurrency(
                    data.revenue_recovered
                );

        }


        // =================================================
        // RECOVERY RATE
        // =================================================

        const rate =
            Math.max(
                0,
                Math.min(
                    100,
                    Number(
                        data.recovery_rate
                    ) || 0
                )
            );


        const rateElement =
            document.getElementById(
                "recovery-rate"
            );


        if (rateElement) {

            rateElement.textContent =
                `${rate}%`;

        }


        // =================================================
        // FAILED PAYMENTS
        // =================================================

        const failedElement =
            document.getElementById(
                "failed-payments"
            );


        if (failedElement) {

            failedElement.textContent =
                data.failed_payments;

        }


        // =================================================
        // RECOVERY LINKS
        // =================================================

        const linksElement =
            document.getElementById(
                "recovery-links"
            );


        if (linksElement) {

            linksElement.textContent =
                data.recovery_links;

        }


        // =================================================
        // OVERVIEW — AT RISK
        // =================================================

        const overviewRisk =
            document.getElementById(
                "overview-risk"
            );


        if (overviewRisk) {

            overviewRisk.textContent =
                formatCurrency(
                    data.revenue_at_risk
                );

        }


        // =================================================
        // OVERVIEW — RECOVERED
        // =================================================

        const overviewRecovered =
            document.getElementById(
                "overview-recovered"
            );


        if (overviewRecovered) {

            overviewRecovered.textContent =
                formatCurrency(
                    data.revenue_recovered
                );

        }


        // =================================================
        // INTERACTIVE RECOVERY CIRCLE
        // =================================================

        const circleRate =
            document.getElementById(
                "circle-rate"
            );


        const recoveryCircle =
            document.getElementById(
                "recovery-circle"
            );


        if (circleRate) {

            circleRate.textContent =
                `${rate}%`;

        }


        if (recoveryCircle) {

            recoveryCircle.style.setProperty(
                "--recovery-progress",
                `${rate}%`
            );


            recoveryCircle.dataset.progress =
                `${rate}% recovered — ` +
                `${formatCurrency(
                    data.revenue_recovered
                )} recovered`;

        }


        // =================================================
        // AI DECISION
        // =================================================

        const aiDecision =
            document.getElementById(
                "ai-decision"
            );


        if (
            aiDecision &&
            data.ai_decision
        ) {

            const decision =
                data.ai_decision;


            let icon = "✓";


            if (
                decision.action ===
                "retry_payment"
            ) {

                icon = "↻";

            }


            if (
                decision.action ===
                "manual_review"
            ) {

                icon = "!";

            }


            aiDecision.innerHTML = `

                <div class="decision-icon">
                    ${icon}
                </div>

                <div>

                    <strong>
                        ${decision.action}
                    </strong>

                    <p>
                        ${decision.reason}
                    </p>

                    ${
                        decision.priority
                        ? `
                            <p>
                                Priority:
                                <strong>
                                    ${decision.priority}
                                </strong>
                            </p>
                        `
                        : ""
                    }

                </div>

            `;

        }


    } catch (error) {

        console.error(
            "Dashboard error:",
            error
        );

    }

}


// =====================================================
// TRANSACTIONS
// =====================================================

async function loadTransactions() {

    try {

        const response =
            await authenticatedFetch(
                `${API_BASE}/dashboard/transactions`
            );


        if (!response.ok) {

            throw new Error(
                `Transaction request failed: ${response.status}`
            );

        }


        const transactions =
            await response.json();


        const tableBody =
            document.getElementById(
                "transactions-body"
            );


        if (!tableBody) {
            return;
        }


        tableBody.innerHTML = "";


        if (
            transactions.length === 0
        ) {

            tableBody.innerHTML = `

                <tr>

                    <td
                        colspan="6"
                        class="loading"
                    >
                        No failed payments found.
                    </td>

                </tr>

            `;

            return;

        }


        transactions.forEach(
            transaction => {

                const row =
                    document.createElement(
                        "tr"
                    );


                const recoveryStatus =
                    transaction.recovery_status ||
                    "Not initiated";


                let recoveryHTML = `

                    <span>
                        Not created
                    </span>

                `;


                if (
                    transaction.recovery_link
                ) {

                    recoveryHTML = `

                        <a
                            href="${transaction.recovery_link}"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="recovery-link"
                        >
                            Open Link
                        </a>

                    `;

                }


                // =================================================
                // CLICKABLE PAYMENT ID
                // =================================================

                const paymentHTML = `

                    <a
                        href="transaction.html?id=${encodeURIComponent(
                            transaction.payment_id
                        )}"
                        class="payment-link"
                    >
                        ${transaction.payment_id}
                    </a>

                `;


                row.innerHTML = `

                    <td>
                        ${paymentHTML}
                    </td>

                    <td>
                        ${formatCurrency(
                            transaction.amount,
                            transaction.currency
                        )}
                    </td>

                    <td>
                        ${transaction.method || "-"}
                    </td>

                    <td>
                        ${transaction.error_code || "-"}
                    </td>

                    <td>

                        <div class="recovery-cell">

                            ${recoveryHTML}

                            <span class="recovery-status">
                                ${recoveryStatus}
                            </span>

                        </div>

                    </td>

                    <td>

                        <span class="status-badge">
                            ${transaction.status}
                        </span>

                    </td>

                `;


                tableBody.appendChild(
                    row
                );

            }
        );


    } catch (error) {

        console.error(
            "Transaction loading error:",
            error
        );


        const tableBody =
            document.getElementById(
                "transactions-body"
            );


        if (tableBody) {

            tableBody.innerHTML = `

                <tr>

                    <td
                        colspan="6"
                        class="loading"
                    >
                        Could not connect to RecoverAI backend.
                    </td>

                </tr>

            `;

        }

    }

}


// =====================================================
// INITIALIZE
// =====================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadDashboard();

        loadTransactions();

    }
);