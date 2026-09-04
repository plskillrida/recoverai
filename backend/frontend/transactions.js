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
// FORMAT DATE
// =====================================================

function formatDate(dateString) {

    if (!dateString) {
        return "-";
    }


    const date = new Date(dateString);


    if (isNaN(date.getTime())) {
        return dateString;
    }


    return date.toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    });

}


// =====================================================
// STATUS BADGE
// =====================================================

function getStatusBadge(status) {

    if (!status) {
        return `<span class="badge">-</span>`;
    }


    const normalized =
        status.toLowerCase();


    if (normalized === "failed") {

        return `
            <span class="badge badge-failed">
                FAILED
            </span>
        `;

    }


    if (
        normalized === "success" ||
        normalized === "captured" ||
        normalized === "paid"
    ) {

        return `
            <span class="badge badge-success">
                ${status.toUpperCase()}
            </span>
        `;

    }


    if (
        normalized === "pending" ||
        normalized === "initiated"
    ) {

        return `
            <span class="badge badge-pending">
                ${status.toUpperCase()}
            </span>
        `;

    }


    return `
        <span class="badge">
            ${status.toUpperCase()}
        </span>
    `;

}


// =====================================================
// RECOVERY BADGE
// =====================================================

function getRecoveryBadge(status) {

    if (!status) {

        return `
            <span class="badge">
                Not initiated
            </span>
        `;

    }


    const normalized =
        status.toLowerCase();


    if (normalized === "recovered") {

        return `
            <span class="badge badge-success">
                RECOVERED
            </span>
        `;

    }


    if (
        normalized === "initiated" ||
        normalized === "pending"
    ) {

        return `
            <span class="badge badge-pending">
                ${status.toUpperCase()}
            </span>
        `;

    }


    if (normalized === "failed") {

        return `
            <span class="badge badge-failed">
                FAILED
            </span>
        `;

    }


    return `
        <span class="badge">
            ${status.toUpperCase()}
        </span>
    `;

}


// =====================================================
// LOAD TRANSACTIONS
// =====================================================

async function loadTransactions() {

    const loading =
        document.getElementById("loading");

    const error =
        document.getElementById("error");

    const empty =
        document.getElementById("empty");

    const container =
        document.getElementById(
            "transactions-container"
        );

    const tableBody =
        document.getElementById("transactions");


    loading.style.display = "block";
    error.style.display = "none";
    empty.style.display = "none";
    container.style.display = "none";

    tableBody.innerHTML = "";


    try {

        const response =
            await authenticatedFetch(
                `${API_BASE}/dashboard/transactions`
            );


        if (!response.ok) {

            throw new Error(
                `Failed to load transactions (${response.status})`
            );

        }


        const data =
            await response.json();


        console.log(
            "Transactions API response:",
            data
        );


        let transactions = [];


        if (Array.isArray(data)) {

            transactions = data;

        } else if (
            Array.isArray(data.transactions)
        ) {

            transactions = data.transactions;

        } else if (
            Array.isArray(data.data)
        ) {

            transactions = data.data;

        }


        if (transactions.length === 0) {

            loading.style.display = "none";
            empty.style.display = "block";

            return;
        }


        transactions.forEach(transaction => {

            const row =
                document.createElement("tr");


            row.style.cursor = "pointer";


            row.innerHTML = `

                <td>
                    <strong class="mono">
                        ${transaction.payment_id || "-"}
                    </strong>
                </td>

                <td>
                    <strong>
                        ${formatCurrency(
                            transaction.amount,
                            transaction.currency
                        )}
                    </strong>
                </td>

                <td>
                    ${transaction.method || "-"}
                </td>

                <td>
                    ${getStatusBadge(
                        transaction.status
                    )}
                </td>

                <td>
                    ${getRecoveryBadge(
                        transaction.recovery_status
                    )}
                </td>

                <td>
                    ${formatDate(
                        transaction.created_at
                    )}
                </td>

                <td>
                    <span class="transaction-arrow">
                        →
                    </span>
                </td>

            `;


            row.addEventListener(
                "click",
                () => {

                    const paymentId =
                        transaction.payment_id;


                    if (!paymentId) {
                        return;
                    }


                    window.location.href =
                        `transaction.html?payment_id=${encodeURIComponent(
                            paymentId
                        )}`;

                }
            );


            tableBody.appendChild(row);

        });


        loading.style.display = "none";
        container.style.display = "block";


    }


    catch (errorObject) {

        console.error(
            "Transaction loading error:",
            errorObject
        );


        loading.style.display = "none";
        error.style.display = "block";


        document.getElementById(
            "error-message"
        ).textContent =
            errorObject.message;

    }

}


// =====================================================
// INITIALIZE
// =====================================================

document.addEventListener(
    "DOMContentLoaded",
    loadTransactions
);