const TOKEN_KEY = 'bob_jwt';

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}

async function getDeviceFingerprint() {
    const signals = [
        navigator.userAgent,
        navigator.platform,
        navigator.language,
        screen.width + 'x' + screen.height,
        screen.colorDepth,
        new Date().getTimezoneOffset(),
        navigator.hardwareConcurrency || 'unknown',
    ].join('|');

    const encoder = new TextEncoder();
    const data = encoder.encode(signals);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

async function sendLoginBehavior(token) {
    const fingerprint = await getDeviceFingerprint();

    fetch('/risk/calculate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
            behavior: {
                login_hour: new Date().getHours(),
                device_fingerprint: fingerprint,
            }
        }),
    }).catch(() => {
        // non-blocking — login should proceed even if this fails
    });
}

const loginForm = document.getElementById('loginForm');

if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;

        const submitBtn = loginForm.querySelector('button[type="submit"]');
        const originalBtnHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Signing in…';

        try {
            const res = await fetch(loginForm.action, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });

            const data = await res.json();

            if (!res.ok) {
                showLoginError(data.error || 'Login failed.');
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnHtml;
                return;
            }

            setToken(data.token);
            await sendLoginBehavior(data.token);

            if (data.is_admin) {
                window.location.href = '/admin_dashboard';
            } else {
                window.location.href = '/home';
            }

        } catch (err) {
            showLoginError('Could not reach the server. Try again.');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnHtml;
        }
    });
}

function showLoginError(message) {
    let el = document.getElementById('loginError');
    if (!el) {
        el = document.createElement('div');
        el.id = 'loginError';
        el.className = 'alert alert-error fade-in';
        loginForm.parentNode.insertBefore(el, loginForm);
    }
    el.textContent = message;
}