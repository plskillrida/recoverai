const API_BASE = "http://127.0.0.1:8000";


// =====================================================
// THEME
// =====================================================

function setTheme(theme) {

    if (theme === "light") {

        document.body.classList.add(
            "light-mode"
        );

        localStorage.setItem(
            "recoverai-theme",
            "light"
        );

    }

    else {

        document.body.classList.remove(
            "light-mode"
        );

        localStorage.setItem(
            "recoverai-theme",
            "dark"
        );

    }


    updateThemeButtons();

}


function updateThemeButtons() {

    const theme =
        localStorage.getItem(
            "recoverai-theme"
        ) || "dark";


    const darkButton =
        document.getElementById(
            "dark-theme"
        );


    const lightButton =
        document.getElementById(
            "light-theme"
        );


    if (darkButton) {

        darkButton.classList.toggle(
            "active",
            theme === "dark"
        );

    }


    if (lightButton) {

        lightButton.classList.toggle(
            "active",
            theme === "light"
        );

    }

}


function applySavedTheme() {

    const theme =
        localStorage.getItem(
            "recoverai-theme"
        ) || "dark";


    if (theme === "light") {

        document.body.classList.add(
            "light-mode"
        );

    }

    else {

        document.body.classList.remove(
            "light-mode"
        );

    }


    updateThemeButtons();

}


// =====================================================
// BACKEND STATUS
// =====================================================

async function checkBackend() {

    const status =
        document.getElementById(
            "backend-status"
        );


    if (!status) {
        return;
    }


    try {

        const response =
            await fetch(
                `${API_BASE}/health`
            );


        if (!response.ok) {
            throw new Error(
                "Backend unavailable"
            );
        }


        status.innerHTML = `
            <span class="status-dot"></span>

            <span class="status-online">
                Operational
            </span>
        `;

    }


    catch (error) {

        console.error(
            "Backend health check failed:",
            error
        );


        status.innerHTML = `
            <span class="status-dot offline-dot"></span>

            <span class="status-offline">
                Offline
            </span>
        `;

    }

}


// =====================================================
// INITIALIZE
// =====================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        applySavedTheme();

        checkBackend();

    }
);