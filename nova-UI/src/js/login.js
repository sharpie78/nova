document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const submitBtn = form.querySelector('input[type="submit"]');
    const messageDiv = document.getElementById("message");

    let userExists = true;

    passwordInput.addEventListener("focus", async () => {
        const username = usernameInput.value.trim();
        if (!username) {
            submitBtn.value = "Register and Login";
            userExists = false;
            return;
        }

        try {
            const res = await fetch(`http://localhost:56969/user-exists/${username}`);
            const data = await res.json();
            userExists = data.exists;
            submitBtn.value = userExists ? "Login" : "Register and Login";
        } catch (err) {
            console.error("Error checking user existence:", err);
            messageDiv.innerHTML = `<p class="error">Error contacting server</p>`;
        }
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        if (!username || !password) return;

        const requestData = {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        };

        try {
            if (userExists) {
                // Try login
                const response = await fetch("http://localhost:56969/login", requestData);
                const data = await response.json();
                if (response.ok) {
                    localStorage.setItem("jwtToken", data.token);
                    localStorage.setItem("username", username);

                    window.location.href = "dashboard.html";
                } else {
                    messageDiv.innerHTML = `<p class="error">${data.detail}</p>`;
                }
            } else {
                // Register then login
                const regRes = await fetch("http://localhost:56969/register", requestData);
                const regData = await regRes.json();
                if (!regRes.ok) {
                    messageDiv.innerHTML = `<p class="error">${regData.detail}</p>`;
                    return;
                }

                // Now try login
                const loginRes = await fetch("http://localhost:56969/login", requestData);
                const loginData = await loginRes.json();
                if (loginRes.ok) {
                    localStorage.setItem("jwtToken", loginData.token);
                    localStorage.setItem("username", username);

                    window.location.href = "dashboard.html";
                } else {
                    messageDiv.innerHTML = `<p class="error">${loginData.detail}</p>`;
                }
            }
        } catch (err) {
            console.error("Login/Register error:", err);
            messageDiv.innerHTML = `<p class="error">Error communicating with server</p>`;
        }
    });
});
