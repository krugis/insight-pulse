// frontend/js/api.js

// API_BASE_URL is defined in frontend/js/utils.js
// Ensure frontend/js/utils.js is loaded BEFORE this file in your HTML

// Helper function to get the stored access token
function getAccessToken() {
    return localStorage.getItem('accessToken');
}

// Helper function to set the access token
function setAccessToken(token) {
    localStorage.setItem('accessToken', token);
}

// Helper function to remove the access token (logout)
function removeAccessToken() {
    localStorage.removeItem('accessToken');
}

// Generic API request handler
async function apiRequest(method, endpoint, data = null, requiresAuth = true) {
    const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    };

    if (requiresAuth) {
        const token = getAccessToken();
        if (!token) {
            console.error('Authentication required, but no token found.');
            // Redirect to login page if no token
            window.location.href = 'login.html';
            throw new Error('No access token found.');
        }
        headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        method: method,
        headers: headers
    };

    if (data) {
        config.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

        if (response.status === 401) {
            console.warn('Authentication expired or invalid. Redirecting to login.');
            removeAccessToken();
            window.location.href = 'login.html';
            return; // Prevent further processing
        }

        if (!response.ok) {
            const errorData = await response.json();
            console.error(`API Error (${response.status}):`, errorData);
            throw new Error(errorData.detail || `API request failed with status ${response.status}`);
        }

        // For 204 No Content, response.json() would throw an error
        if (response.status === 204) {
            return null;
        }

        return await response.json();
    } catch (error) {
        console.error('Network or API call error:', error);
        throw error;
    }
}

// --- Specific API Functions ---

// Authentication
async function registerUser(email, password) {
    return apiRequest('POST', '/register', { email, password }, false); // No auth needed for register
}

async function loginUser(email, password) {
    // Note: FastAPI's /token endpoint expects x-www-form-urlencoded for OAuth2PasswordRequestForm
    // So we need a special handling for this specific endpoint.
    const headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    };
    const body = new URLSearchParams({ username: email, password: password });

    const response = await fetch(`${API_BASE_URL}/token`, {
        method: 'POST',
        headers: headers,
        body: body.toString()
    });

    if (!response.ok) {
        const errorData = await response.json();
        console.error(`Login Error (${response.status}):`, errorData);
        throw new Error(errorData.detail || `Login failed with status ${response.status}`);
    }
    const data = await response.json();
    setAccessToken(data.access_token); // Store token on successful login
    return data;
}

// User Management
async function getCurrentUser() {
    return apiRequest('GET', '/users/me');
}

async function updateCurrentUser(userData) {
    return apiRequest('PATCH', '/users/me', userData);
}

// Agent Management
async function createAgent(agentData) {
    // agentData should match the BFF's AgentCreate schema
    return apiRequest('POST', '/agents/', agentData);
}

async function getAllAgents() {
    return apiRequest('GET', '/agents/');
}

async function getAgentDetails(agentId) {
    return apiRequest('GET', `/agents/${agentId}`);
}

async function updateAgentStatus(agentId, newStatus) {
    return apiRequest('PATCH', `/agents/${agentId}/status`, { status: newStatus });
}

async function deleteAgent(agentId) {
    return apiRequest('DELETE', `/agents/${agentId}`); // 204 No Content expected
}

async function getAgentRuns(agentId) {
    return apiRequest('GET', `/agents/${agentId}/runs`);
}

async function updateAgentDetails(agentId, agentData) {
    // agentData should match the BFF's AgentUpdate schema (app/schemas/agent.py)
    return apiRequest('PATCH', `/agents/${agentId}`, agentData);
}