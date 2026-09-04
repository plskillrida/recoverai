// =====================================================
// RECOVERAI AUTHENTICATION
// =====================================================


// =====================================================
// TOKEN HELPERS
// =====================================================

function getAuthToken() {
    return localStorage.getItem("recoverai-token");
}


function getUsername() {
    return localStorage.getItem("recoverai-username");
}


// =====================================================
// REQUIRE LOGIN
// =====================================================

function requireAuth() {

    const token = getAuthToken();

    if (!token) {
        window.location.href = "login.html";
        return false;
    }

    return true;
}


// =====================================================
// AUTHENTICATED FETCH
// =====================================================

async function authenticatedFetch(url, options = {}) {

    const token = getAuthToken();

    if (!token) {

        window.location.href = "login.html";

        throw new Error(
            "Authentication required"
        );
    }


    const headers = {
        ...(options.headers || {}),
        "Authorization": `Bearer ${token}`
    };


    const response = await fetch(
        url,
        {
            ...options,
            headers
        }
    );


    // Token expired / invalid

    if (response.status === 401) {

        localStorage.removeItem(
            "recoverai-token"
        );

        localStorage.removeItem(
            "recoverai-username"
        );

        window.location.href =
            "login.html";

        throw new Error(
            "Authentication expired"
        );
    }


    return response;
}


// =====================================================
// LOGOUT
// =====================================================

function logout() {

    localStorage.removeItem(
        "recoverai-token"
    );

    localStorage.removeItem(
        "recoverai-username"
    );

    window.location.href =
        "login.html";
}


// =====================================================
// ADD LOGOUT BUTTON
// =====================================================

function addLogoutButton() {

    const sidebarBottom =
        document.querySelector(
            ".sidebar-bottom"
        );


    if (!sidebarBottom) {
        return;
    }


    // Don't create another button
    // if the page already has one.

    if (
        sidebarBottom.querySelector(
            ".logout-button"
        )
    ) {
        return;
    }


    const button =
        document.createElement("button");


    button.type = "button";

    button.className =
        "logout-button";

    button.textContent =
        "Logout";


    button.addEventListener(
        "click",
        logout
    );


    sidebarBottom.appendChild(
        button
    );
}


// =====================================================
// AUTOMATIC AUTH GUARD
// =====================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const page =
            window.location.pathname
                .split("/")
                .pop();


        const publicPages = [
            "",
            "login.html"
        ];


        if (
            !publicPages.includes(page)
        ) {

            requireAuth();

            addLogoutButton();

        }

    }
);