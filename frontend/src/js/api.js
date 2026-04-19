const API_URL = "http://localhost:8000";

async function apiFetch(endpoint, method = 'GET', data = null) {
    const rolId = localStorage.getItem('rol_id') || '1';
    
    const config = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-Rol-Id': rolId
        }
    };

    if (data) {
        config.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_URL}${endpoint}`, config);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || result.mensaje || 'Error en la petición');
        }

        return { status: response.status, data: result };
    } catch (error) {
        console.error("Error en API Fetch:", error);
        return { status: 500, error: error.message };
    }
}

function checkAuth() {
    const userId = localStorage.getItem('usuario_id');
    if (!userId && !window.location.pathname.includes('login.html') && !window.location.pathname.includes('registro.html')) {
        window.location.href = 'login.html';
    }
}