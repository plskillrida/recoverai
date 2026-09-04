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
    ).format(amount / 100);

}


// =====================================================
// STATUS BADGE
// =====================================================

function getStatusClass(status) {

    if (!status) {
        return "recovery-status";
    }

    return `recovery-status ${status.toLowerCase()}`;

}


// =====================================================
// LOAD RECOVERIES
// =====================================================

async function loadRecoveries() {

    const tableBody =
        document.getElementById(
            "recoveries"
        );


    if (!tableBody) {
        return;
    }


    try {

        tableBody.innerHTML = `
            <tr>
                <td
                    colspan="7"
                    class="loading"
                >
                    Loading recoveries...
                </td>
            </tr>
        `;


        const response =
            await authenticatedFetch(
                `${API_BASE}/recoveries`
            );


        if (!response.ok) {

            throw new Error(
                `Recoveries request failed: ${response.status}`
            );

        }


        const recoveries =
            await response.json();


        tableBody.innerHTML = "";


        // =================================================
        // EMPTY STATE
        // =================================================

        if (
            recoveries.length === 0
        ) {

            tableBody.innerHTML = `
                <tr>
                    <td
                        colspan="7"
                        class="loading"
                    >
                        No recovery attempts yet.
                    </td>
                </tr>
            `;

            updateMetrics([]);

            return;
        }


        // =================================================
        // METRICS
        // =================================================

        updateMetrics(
            recoveries
        );


        // =================================================
        // TABLE
        // =================================================

        recoveries.forEach(
            recovery => {

                const row =
                    document.createElement(
                        "tr"
                    );


                const status =
                    recovery.recovery_status ||
                    "initiated";


                const recoveryLink =
                    recovery.recovery_link;


                let linkHTML = `
                    <span>
                        Not created
                    </span>
                `;


                if (recoveryLink) {

                    linkHTML = `
                        <a
                            href="${recoveryLink}"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="recovery-link"
                        >
                            Open Link
                        </a>
                    `;

                }


                const paymentHTML = `
                    <a
                        href="transaction.html?id=${encodeURIComponent(
                            recovery.payment_id
                        )}"
                        class="payment-link"
                    >
                        ${recovery.payment_id}
                    </a>
                `;


                const action =
                    recovery.action ||
                    "retry_payment";


                row.innerHTML = `

                    <td>
                        ${paymentHTML}
                    </td>


                    <td>
                        ${formatCurrency(
                            recovery.amount,
                            recovery.currency
                        )}
                    </td>


                    <td>
                        ${action}
                    </td>


                    <td>
                        ${linkHTML}
                    </td>


                    <td>
                        <span
                            class="${getStatusClass(status)}"
                        >
                            ${status}
                        </span>
                    </td>


                    <td>
                        ${recovery.method || "-"}
                    </td>


                    <td>

                        <button
                            type="button"
                            class="verify-button"
                            onclick="verifyRecovery('${recovery.payment_id}')"
                        >
                            Verify
                        </button>

                    </td>

                `;


                tableBody.appendChild(
                    row
                );

            }
        );


    } catch (error) {

        console.error(
            "Recoveries error:",
            error
        );


        tableBody.innerHTML = `
            <tr>
                <td
                    colspan="7"
                    class="loading"
                >
                    Could not load recoveries.
                </td>
            </tr>
        `;

    }

}


// =====================================================
// UPDATE METRICS
// =====================================================

function updateMetrics(
    recoveries
) {

    const totalLinks =
        recoveries.filter(
            recovery =>
                recovery.recovery_link
        ).length;


    const initiated =
        recoveries.filter(
            recovery =>
                recovery.recovery_status ===
                "initiated"
        ).length;


    const recovered =
        recoveries.filter(
            recovery =>
                recovery.recovery_status ===
                "recovered"
        ).length;


    const recoveredRevenue =
        recoveries
            .filter(
                recovery =>
                    recovery.recovery_status ===
                    "recovered"
            )
            .reduce(
                (
                    total,
                    recovery
                ) =>
                    total +
                    (
                        recovery.amount ||
                        0
                    ),
                0
            );


    const totalElement =
        document.getElementById(
            "total-links"
        );

    if (totalElement) {

        totalElement.textContent =
            totalLinks;

    }


    const initiatedElement =
        document.getElementById(
            "initiated-count"
        );

    if (initiatedElement) {

        initiatedElement.textContent =
            initiated;

    }


    const recoveredElement =
        document.getElementById(
            "recovered-count"
        );

    if (recoveredElement) {

        recoveredElement.textContent =
            recovered;

    }


    const revenueElement =
        document.getElementById(
            "recovered-revenue"
        );

    if (revenueElement) {

        revenueElement.textContent =
            formatCurrency(
                recoveredRevenue
            );

    }

}


// =====================================================
// VERIFY RECOVERY
// =====================================================

async function verifyRecovery(
    paymentId
) {

    try {

        const response =
            await authenticatedFetch(
                `${API_BASE}/recovery/verify/${encodeURIComponent(
                    paymentId
                )}`
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Verification failed"
            );

        }


        console.log(
            "Recovery verification:",
            data
        );


        if (
            data.status ===
            "recovered"
        ) {

            alert(
                "Recovery verified successfully."
            );

        } else {

            alert(
                `Recovery status: ${data.status}`
            );

        }


        await loadRecoveries();


    } catch (error) {

        console.error(
            "Recovery verification error:",
            error
        );


        alert(
            error.message ||
            "Unable to verify recovery."
        );

    }

}


// =====================================================
// INITIALIZE
// =====================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadRecoveries();

    }
);