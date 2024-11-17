// Helper to update main content
function updateMainContent(content) {
    document.getElementById("main-content").innerHTML = content;
}

// Load Dashboard Home
function loadHome() {
    updateMainContent(`
        <h2>Welcome to RSV Admin Dashboard</h2>
        <section class="options">
            <article class="option" onclick="loadSendConsignments()">
                <img src="/static/images/shipping.png" alt="Shipping" style="width: 100%; border-radius: 8px;">
                <h2>Shipping</h2>
                <p>Send your consignments and manage your shipments efficiently.</p>
            </article>
        </section>
    `);
}

// Generate area options dynamically
function generateAreaOptions(areas) {
    return areas.map(area => `
        <label>
            <input type="checkbox" class="areaCheckbox" value="${area}"> ${area}
        </label>
    `).join('');
}

// Load Send Consignments Section
function loadSendConsignments() {
    updateMainContent(`
        <h2>Send Consignments</h2>
        <form id="sendForm" class="send-form">
            <div class="form-group">
                <label for="agent">Select Delivery Agent:</label>
                <select id="agentSelect" name="agent" required>
                    <option value="" disabled selected>Select an agent</option>
                    <option value="agent1">Agent 1</option>
                    <option value="agent2">Agent 2</option>
                </select>
            </div>
            <div class="form-group">
                <label>Select Areas:</label>
                <div id="areaSelection" class="area-selection">
                    ${generateAreaOptions([
                        "Marathahalli", "Sarjapur Road", "Electronic City", 
                        "HSR Layout", "Koramangala", "Whitefield", 
                        "BTM Layout", "Bellandur", "Tin Factory", "Banashankari"
                    ])}
                </div>
            </div>
            <button onclick="sendConsignment()">Send Consignment</button>
        </form>
        <div id="mapsContainer"></div>
    `);

    document.getElementById("sendForm").addEventListener("submit", handleSendFormSubmit);
}

// Handle send consignment form submission
function handleSendFormSubmit(event) {
    event.preventDefault();
    sendConsignment();
}

// Send consignment
function sendConsignment() {
    const agent = document.querySelector('#agentSelect').value;
    const areas = Array.from(document.querySelectorAll('.areaCheckbox:checked')).map(cb => cb.value);

    fetch('http://127.0.0.1:5000/send-consignment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ agent, areas })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Consignment sent successfully!");
            // Display the route map or update the UI
        } else {
            alert("Failed to send consignment.");
        }
    })
    .catch(error => console.error("Error:", error));
}

// Load My Account Section
function loadMyAccount() {
    updateMainContent(`
        <h2>My Account</h2>
        <div class="account-details">
            <p><strong>Username:</strong> admin</p>
            <p><strong>Email:</strong> admin@example.com</p>
            <button onclick="logout()" class="btn">Logout</button>
        </div>
    `);
}

// Logout function
function logout() {
    document.cookie = "sessionId=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    localStorage.removeItem('sessionToken');

    alert("You have been logged out.");
    window.location.href = "/login"; // Redirect to login route
}
