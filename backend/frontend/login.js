const API_BASE = "http://127.0.0.1:8000";


// =====================================================
// CHECK EXISTING LOGIN
// =====================================================

function checkExistingLogin() {

    const token =
        localStorage.getItem("recoverai-token");


    if (token) {

        window.location.href =
            "index.html";

    }

}


// =====================================================
// LOGIN
// =====================================================

async function login(
    username,
    password
) {

    const errorElement =
        document.getElementById(
            "login-error"
        );


    errorElement.textContent = "";


    try {

        const response =
            await fetch(
                `${API_BASE}/auth/login`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        username: username,
                        password: password
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Login failed"
            );

        }


        // Save authentication

        localStorage.setItem(
            "recoverai-token",
            data.access_token
        );


        localStorage.setItem(
            "recoverai-username",
            data.username
        );


        // IMPORTANT:
        // Dashboard is index.html

        window.location.href =
            "index.html";


    } catch (error) {

        console.error(
            "Login error:",
            error
        );


        errorElement.textContent =
            error.message;

    }

}


// =====================================================
// PAGE INITIALIZATION
// =====================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        checkExistingLogin();


        const form =
            document.getElementById(
                "login-form"
            );


        if (!form) {
            return;
        }


        form.addEventListener(
            "submit",
            async event => {

                event.preventDefault();


                const username =
                    document.getElementById(
                        "username"
                    ).value.trim();


                const password =
                    document.getElementById(
                        "password"
                    ).value;


                await login(
                    username,
                    password
                );

            }
        );

    }
);