const API_URL = 'http://localhost:5000/api';

// Helper function to get authentication headers
function getAuthHeaders() {
    const token = sessionStorage.getItem('token');
    const headers = {
        'Content-Type': 'application/json'
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

// Role configurations
const roleConfig = {
    client: {
        icon: '👤',
        message: 'You are logged in as a Client. You can request events and manage your bookings.'
    },
    planner: {
        icon: '📋',
        message: 'You are logged in as an Event Planner. You can view and manage assigned events.'
    },
    admin: {
        icon: '👨‍💼',
        message: 'You are logged in as an Administrator. You have full access to the system.'
    }
};

function toggleForm(form) {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    if (form === 'login') {
        loginForm.classList.add('active');
        registerForm.classList.remove('active');
        clearMessages();
    } else {
        registerForm.classList.add('active');
        loginForm.classList.remove('active');
        clearMessages();
    }
}

function clearMessages() {
    document.getElementById('loginMessage').classList.remove('show', 'success', 'error');
    document.getElementById('registerMessage').classList.remove('show', 'success', 'error');
    document.getElementById('emailCheckMessage').textContent = '';
}

function showMessage(elementId, message, type) {
    const messageEl = document.getElementById(elementId);
    messageEl.textContent = message;
    messageEl.classList.add('show', type);
}

function showLoading(elementId, show) {
    const loadingEl = document.getElementById(elementId);
    if (show) {
        loadingEl.classList.add('show');
    } else {
        loadingEl.classList.remove('show');
    }
}

async function checkEmailExists() {
    const email = document.getElementById('registerEmail').value;
    const messageEl = document.getElementById('emailCheckMessage');

    if (!email) {
        messageEl.textContent = '';
        return;
    }

    try {
        const response = await fetch(`${API_URL}/check-email`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (data.exists) {
            messageEl.textContent = '❌ This email is already registered';
            messageEl.style.color = '#dc3545';
        } else {
            messageEl.textContent = '✓ Email is available';
            messageEl.style.color = '#28a745';
        }
    } catch (error) {
        messageEl.textContent = '';
    }
}

async function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    if (!email || !password) {
        showMessage('loginMessage', 'Please fill in all fields', 'error');
        return;
    }

    showLoading('loginLoading', true);

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (data.success) {
            // Store user data and JWT token in session storage
            sessionStorage.setItem('user', JSON.stringify(data.user));
            sessionStorage.setItem('token', data.token);
            
            // Show welcome page
            showWelcomePage(data.user);
            showMessage('loginMessage', 'Login successful! Redirecting...', 'success');
        } else {
            showMessage('loginMessage', data.message || 'Login failed', 'error');
        }
    } catch (error) {
        showMessage('loginMessage', 'Error connecting to server: ' + error.message, 'error');
    } finally {
        showLoading('loginLoading', false);
    }
}

async function handleRegister(event) {
    event.preventDefault();

    const username = document.getElementById('registerUsername').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const role = document.querySelector('input[name="role"]:checked').value;

    if (!username || !email || !password) {
        showMessage('registerMessage', 'Please fill in all fields', 'error');
        return;
    }

    // Check password strength
    if (password.length < 6) {
        showMessage('registerMessage', 'Password must be at least 6 characters', 'error');
        return;
    }

    showLoading('registerLoading', true);

    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                email,
                password,
                role
            })
        });

        const data = await response.json();

        if (data.success) {
            // Store user data and JWT token
            sessionStorage.setItem('user', JSON.stringify(data.user));
            sessionStorage.setItem('token', data.token);
            showMessage('registerMessage', data.message + ' Redirecting to login...', 'success');
            
            // Auto-populate login form and switch to it
            setTimeout(() => {
                document.getElementById('loginEmail').value = email;
                document.getElementById('loginPassword').value = password;
                toggleForm('login');
            }, 1500);
        } else {
            showMessage('registerMessage', data.message || 'Registration failed', 'error');
        }
    } catch (error) {
        showMessage('registerMessage', 'Error connecting to server: ' + error.message, 'error');
    } finally {
        showLoading('registerLoading', false);
    }
}

function showWelcomePage(user) {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const welcomePage = document.getElementById('welcomePage');
    const clientDashboard = document.getElementById('clientDashboard');
    const plannerDashboard = document.getElementById('plannerDashboard');
    const plannerLanding = document.getElementById('plannerLanding');
    const adminLanding = document.getElementById('adminLanding');
    const adminEventsDashboard = document.getElementById('adminEventsDashboard');

    loginForm.classList.remove('active');
    registerForm.classList.remove('active');

    // If client, show client dashboard
    if (user.role === 'client') {
        welcomePage.classList.remove('active');
        clientDashboard.classList.add('active');
        plannerDashboard.classList.remove('active');
        plannerLanding.classList.remove('active');
        adminLanding.classList.remove('active');
        adminEventsDashboard.classList.remove('active');
        document.body.classList.remove('login-view');
        
        // Populate dashboard info
        document.getElementById('dashboardUserName').textContent = user.username;
        document.getElementById('dashboardUserEmail').textContent = user.email;
        document.getElementById('dashboardDisplayName').textContent = user.username;
        document.getElementById('dashboardDisplayEmail').textContent = user.email;
        
        // Load events
        loadClientEvents(user.id);
    } 
    // If planner, show planner landing page
    else if (user.role === 'planner') {
        welcomePage.classList.remove('active');
        clientDashboard.classList.remove('active');
        plannerDashboard.classList.remove('active');
        plannerLanding.classList.add('active');
        adminLanding.classList.remove('active');
        adminEventsDashboard.classList.remove('active');
        document.body.classList.remove('login-view');
        
        // Store user in session for navigation
        sessionStorage.setItem('currentPlannerUser', JSON.stringify(user));
        
        // Populate landing page info
        document.getElementById('plannerLandingName').textContent = user.username;
        document.getElementById('plannerLandingEmail').textContent = user.email;
        document.getElementById('plannerLandingEventCount').textContent = '0 events';
        
        // Load events
        loadPlannerEvents(user.id);
    }
    // If admin, show admin landing page
    else if (user.role === 'admin') {
        welcomePage.classList.remove('active');
        clientDashboard.classList.remove('active');
        plannerDashboard.classList.remove('active');
        plannerLanding.classList.remove('active');
        adminLanding.classList.add('active');
        adminEventsDashboard.classList.remove('active');
        document.body.classList.remove('login-view');
        
        // Store user in session for navigation
        sessionStorage.setItem('currentAdminUser', JSON.stringify(user));
        
        // Populate landing page info
        document.getElementById('adminLandingName').textContent = user.username;
        document.getElementById('adminLandingEmail').textContent = user.email;
        document.getElementById('adminLandingEventCount').textContent = '0 events';
        
        // Load events
        loadAdminEvents(user.id);
    }
    // Otherwise show welcome page (for other roles)
    else {
        clientDashboard.classList.remove('active');
        plannerDashboard.classList.remove('active');
        plannerLanding.classList.remove('active');
        adminLanding.classList.remove('active');
        adminEventsDashboard.classList.remove('active');
        welcomePage.classList.add('active');
        document.body.classList.add('login-view');

        // Update welcome page with user data
        const config = roleConfig[user.role] || roleConfig.client;
        document.getElementById('welcomeIcon').textContent = config.icon;
        document.getElementById('welcomeMessage').textContent = config.message;
        document.getElementById('displayName').textContent = user.username;
        document.getElementById('displayEmail').textContent = user.email;
        document.getElementById('displayRole').textContent = user.roleDisplay;

        const roleBadge = document.getElementById('roleBadge');
        roleBadge.textContent = user.role.toUpperCase();
        roleBadge.className = `role-badge ${user.role}`;
    }
}

function navigateToPlannerSystem(system) {
    if (system === 'booking') {
        // Show the booking dashboard
        const plannerLanding = document.getElementById('plannerLanding');
        const plannerDashboard = document.getElementById('plannerDashboard');
        
        plannerLanding.classList.remove('active');
        plannerDashboard.classList.add('active');
    } else {
        // For now, show a message that other systems are coming soon
        alert(`${system.charAt(0).toUpperCase() + system.slice(1)} system is coming soon!`);
    }
}

function navigateToPlannerLanding() {
    // Go back to the planner landing page
    const plannerLanding = document.getElementById('plannerLanding');
    const plannerDashboard = document.getElementById('plannerDashboard');
    
    plannerDashboard.classList.remove('active');
    plannerLanding.classList.add('active');
}

async function loadClientEvents(userId) {
    try {
        const response = await fetch(`${API_URL}/client/events`, {
            headers: getAuthHeaders()
        });
        const data = await response.json();

        if (data.success) {
            displayEvents(data.events);
            updateEventCount(data.events.length);
        } else {
            displayEvents([]);
            updateEventCount(0);
        }
    } catch (error) {
        console.error('Error loading events:', error);
        displayEvents([]);
        updateEventCount(0);
    }
}

async function loadPlannerEvents(userId) {
    try {
        const response = await fetch(`${API_URL}/planner/events`, {
            headers: getAuthHeaders()
        });
        const data = await response.json();

        if (data.success) {
            displayPlannerEvents(data.events);
            displayNextEvent(data.events);
            updatePlannerEventCount(data.events.length);
        } else {
            displayPlannerEvents([]);
            displayNextEvent([]);
            updatePlannerEventCount(0);
        }
    } catch (error) {
        console.error('Error loading planner events:', error);
        displayPlannerEvents([]);
        displayNextEvent([]);
        updatePlannerEventCount(0);
    }
}

function updatePlannerEventCount(count) {
    document.getElementById('plannerEventCount').textContent = count + ' ' + (count === 1 ? 'event' : 'events');
    // Also update the landing page count
    const landingCountEl = document.getElementById('plannerLandingEventCount');
    if (landingCountEl) {
        landingCountEl.textContent = count + ' ' + (count === 1 ? 'event' : 'events');
    }
}

function displayNextEvent(events) {
    const container = document.getElementById('nextEventContainer');

    if (events.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <div class="empty-state-text">No upcoming events</div>
                <div style="font-size: 13px; color: #bbb;">You have no assigned events yet</div>
            </div>
        `;
        return;
    }

    // Get the first (next) event
    const nextEvent = events[0];
    const eventDate = new Date(nextEvent.event_date);
    const formattedDate = eventDate.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    const statusClass = `status-${nextEvent.status.toLowerCase().replace(/ /g, '-')}`;

    container.innerHTML = `
        <div class="event-card" style="border-left: 4px solid #68a062; background-color: #f0f8f0;">
            <div class="event-card-header">
                <div class="event-card-title" style="font-size: 16px; font-weight: bold;">🌟 ${nextEvent.title || `Next Event #${nextEvent.id}`}</div>
                <div class="event-status-badge ${statusClass}">${nextEvent.status}</div>
            </div>
            <div class="event-card-details">
                <div class="event-detail">
                    <strong>👤 Client</strong>
                    ${nextEvent.client_name}
                </div>
                <div class="event-detail">
                    <strong>📧 Email</strong>
                    ${nextEvent.client_email}
                </div>
                <div class="event-detail">
                    <strong>📅 Date & Time</strong>
                    ${formattedDate}
                </div>
                <div class="event-detail">
                    <strong>💰 Budget</strong>
                    $${nextEvent.price_total.toFixed(2)}
                </div>
                <div class="event-detail">
                    <strong>📍 Location</strong>
                    ${nextEvent.location || 'Not specified'}
                </div>
                <div class="event-detail">
                    <strong>✓ Payment</strong>
                    ${nextEvent.payment_confirmed ? '✅ Confirmed' : '⏳ Pending'}
                </div>
                ${nextEvent.notes ? `
                    <div class="event-detail" style="grid-column: 1 / -1;">
                        <strong>📝 Notes</strong>
                        ${nextEvent.notes}
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

function displayPlannerEvents(events) {
    const container = document.getElementById('plannerEventsContainer');

    if (events.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <div class="empty-state-text">No events assigned</div>
                <div style="font-size: 13px; color: #bbb;">Check back later for new assignments</div>
            </div>
        `;
        return;
    }

    container.innerHTML = '<div class="events-list">' + events.map((event, index) => {
        const eventDate = new Date(event.event_date);
        const formattedDate = eventDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        const statusClass = `status-${event.status.toLowerCase().replace(/ /g, '-')}`;
        const isNext = index === 0 ? 'border-left: 4px solid #68a062; background-color: #f0f8f0;' : '';
        
        // Show action buttons for pre-approval events
        const actionButtons = event.status === 'pre-approval' ? `
            <div class="event-action-buttons" style="margin-top: 15px; display: flex; gap: 10px;">
                <button class="btn-accept" onclick="acceptEvent(${event.id})" style="flex: 1; padding: 10px; background-color: #68a062; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: 500;">✓ Accept</button>
                <button class="btn-decline" onclick="declineEvent(${event.id})" style="flex: 1; padding: 10px; background-color: #cd657a; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: 500;">✗ Decline</button>
            </div>
        ` : '';

        return `
            <div class="event-card" style="${isNext}">
                <div class="event-card-header">
                    <div class="event-card-title">${index === 0 ? '🌟 ' : ''}${event.title || `Event #${event.id}`}</div>
                    <div class="event-status-badge ${statusClass}">${event.status}</div>
                </div>
                <div class="event-card-details">
                    <div class="event-detail">
                        <strong>👤 Client</strong>
                        ${event.client_name}
                    </div>
                    <div class="event-detail">
                        <strong>📧 Email</strong>
                        ${event.client_email}
                    </div>
                    <div class="event-detail">
                        <strong>📅 Date & Time</strong>
                        ${formattedDate}
                    </div>
                    <div class="event-detail">
                        <strong>💰 Budget</strong>
                        $${event.price_total.toFixed(2)}
                    </div>
                    <div class="event-detail">
                        <strong>📍 Location</strong>
                        ${event.location || 'Not specified'}
                    </div>
                    <div class="event-detail">
                        <strong>✓ Payment</strong>
                        ${event.payment_confirmed ? '✅ Confirmed' : '⏳ Pending'}
                    </div>
                    ${event.notes ? `
                        <div class="event-detail" style="grid-column: 1 / -1;">
                            <strong>📝 Notes</strong>
                            ${event.notes}
                        </div>
                    ` : ''}
                </div>
                ${actionButtons}
            </div>
        `;
    }).join('') + '</div>';
}

async function acceptEvent(eventId) {
    const user = JSON.parse(sessionStorage.getItem('user'));
    if (!user) {
        alert('User not found');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/planner/accept-event`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                event_id: eventId
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(`✓ Event "${data.event.title}" accepted successfully!`);
            loadPlannerEvents(user.id);
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (error) {
        console.error('Error accepting event:', error);
        alert('Failed to accept event');
    }
}

async function declineEvent(eventId) {
    const user = JSON.parse(sessionStorage.getItem('user'));
    if (!user) {
        alert('User not found');
        return;
    }

    if (!confirm('Are you sure you want to decline this event? It can be reassigned to another planner.')) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/planner/decline-event`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                event_id: eventId
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(`✗ Event "${data.event.title}" declined successfully. Event can now be reassigned.`);
            loadPlannerEvents(user.id);
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (error) {
        console.error('Error declining event:', error);
        alert('Failed to decline event');
    }
}

function updateEventCount(count) {
    document.getElementById('dashboardEventCount').textContent = count + ' ' + (count === 1 ? 'event' : 'events');
}

function displayEvents(events) {
    const container = document.getElementById('eventsContainer');

    if (events.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <div class="empty-state-text">No events yet</div>
                <div style="font-size: 13px; color: #bbb;">Create your first event above to get started</div>
            </div>
        `;
        return;
    }

    container.innerHTML = '<div class="events-list">' + events.map(event => {
        const eventDate = new Date(event.event_date);
        const formattedDate = eventDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        const statusClass = `status-${event.status.toLowerCase().replace(/ /g, '-')}`;

        return `
            <div class="event-card">
                <div class="event-card-header">
                    <div class="event-card-title">${event.title || `Event #${event.id}`}</div>
                    <div class="event-status-badge ${statusClass}">${event.status}</div>
                </div>
                <div class="event-card-details">
                    <div class="event-detail">
                        <strong>📅 Date & Time</strong>
                        ${formattedDate}
                    </div>
                    <div class="event-detail">
                        <strong>💰 Budget</strong>
                        $${event.price_total.toFixed(2)}
                    </div>
                    <div class="event-detail">
                        <strong>📍 Location</strong>
                        ${event.location || 'Not specified'}
                    </div>
                    <div class="event-detail">
                        <strong>✓ Payment</strong>
                        ${event.payment_confirmed ? '✅ Confirmed' : '⏳ Pending'}
                    </div>
                    ${event.notes ? `
                        <div class="event-detail" style="grid-column: 1 / -1;">
                            <strong>📝 Notes</strong>
                            ${event.notes}
                        </div>
                    ` : ''}
                </div>
                <div class="event-card-actions">
                    ${event.status_code !== 10 ? `
                        <button class="btn-small btn-danger" onclick="cancelEvent(${event.id})">Cancel Event</button>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('') + '</div>';
}

async function handleCreateEvent(event) {
    event.preventDefault();

    const user = JSON.parse(sessionStorage.getItem('user'));
    const title = document.getElementById('eventTitle').value;
    const eventDate = document.getElementById('eventDate').value;
    const location = document.getElementById('eventLocation').value;
    const notes = document.getElementById('eventNotes').value;
    const price = document.getElementById('eventPrice').value || 0;

    if (!eventDate) {
        showMessage('createEventMessage', 'Please select an event date', 'error');
        return;
    }

    // Convert datetime-local to ISO format
    const isoDate = new Date(eventDate).toISOString();

    showLoading('createEventLoading', true);

    try {
        const response = await fetch(`${API_URL}/client/create-event`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                title: title || null,
                event_date: eventDate,
                location: location || null,
                notes: notes || null,
                price_total: parseFloat(price)
            })
        });

        const data = await response.json();

        if (data.success) {
            showMessage('createEventMessage', 'Event created successfully!', 'success');
            document.getElementById('eventTitle').value = '';
            document.getElementById('eventDate').value = '';
            document.getElementById('eventLocation').value = '';
            document.getElementById('eventNotes').value = '';
            document.getElementById('eventPrice').value = '';

            // Reload events
            setTimeout(() => {
                loadClientEvents(user.id);
                document.getElementById('createEventMessage').classList.remove('show');
            }, 1500);
        } else {
            showMessage('createEventMessage', data.message || 'Failed to create event', 'error');
        }
    } catch (error) {
        showMessage('createEventMessage', 'Error: ' + error.message, 'error');
    } finally {
        showLoading('createEventLoading', false);
    }
}

async function cancelEvent(eventId) {
    if (!confirm('Are you sure you want to cancel this event?')) {
        return;
    }

    const user = JSON.parse(sessionStorage.getItem('user'));

    try {
        const response = await fetch(`${API_URL}/client/cancel-event`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                event_id: eventId
            })
        });

        const data = await response.json();

        if (data.success) {
            // Reload events
            loadClientEvents(user.id);
        } else {
            alert('Failed to cancel event: ' + data.message);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function navigateToAdminSystem(system) {
    if (system === 'booking') {
        // Show the admin events dashboard
        const adminLanding = document.getElementById('adminLanding');
        const adminEventsDashboard = document.getElementById('adminEventsDashboard');
        
        adminLanding.classList.remove('active');
        adminEventsDashboard.classList.add('active');
    } else if (system === 'configure') {
        alert('Configure CMS system is coming soon!');
    } else {
        // For now, show a message that other systems are coming soon
        alert(`${system.charAt(0).toUpperCase() + system.slice(1)} system is coming soon!`);
    }
}

function navigateToAdminLanding() {
    // Go back to the admin landing page
    const adminLanding = document.getElementById('adminLanding');
    const adminEventsDashboard = document.getElementById('adminEventsDashboard');
    
    adminEventsDashboard.classList.remove('active');
    adminLanding.classList.add('active');
}

async function loadAdminEvents(userId) {
    try {
        const response = await fetch(`${API_URL}/admin/events`, {
            headers: getAuthHeaders()
        });
        const data = await response.json();

        if (data.success) {
            displayAdminEventsGrid(data.events, data.planners || []);
            updateAdminEventCount(data.events.length);
        } else {
            displayAdminEventsGrid([]);
            updateAdminEventCount(0);
        }
    } catch (error) {
        console.error('Error loading admin events:', error);
        displayAdminEventsGrid([]);
        updateAdminEventCount(0);
    }
}

function updateAdminEventCount(count) {
    document.getElementById('adminLandingEventCount').textContent = count + ' ' + (count === 1 ? 'event' : 'events');
}

function displayAdminEventsGrid(events, planners = []) {
    const container = document.getElementById('adminEventsGridContainer');

    if (events.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px;">
                <div style="font-size: 48px; margin-bottom: 15px;">📭</div>
                <div style="font-size: 18px; font-weight: 600; color: #333; margin-bottom: 10px;">No events</div>
                <div style="font-size: 14px; color: #999;">There are currently no events in the system</div>
            </div>
        `;
        return;
    }

    container.innerHTML = events.map((event, index) => {
        const eventDate = new Date(event.event_date);
        const formattedDate = eventDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        const statusClass = `status-${event.status.toLowerCase().replace(/ /g, '-')}`;
        const assignedPlannerIds = event.assigned_planners ? event.assigned_planners.split(',').map(p => parseInt(p.trim())).filter(p => !isNaN(p)) : [];

        return `
            <div class="admin-event-card" data-event-id="${event.id}">
                <div class="admin-event-card-header">
                    <div class="admin-event-card-title">${event.title || `Event #${event.id}`}</div>
                    <div class="event-status-badge ${statusClass}">${event.status}</div>
                </div>

                <div class="admin-event-card-info">
                    <div class="admin-event-info-item">
                        <div class="admin-event-info-label">Client</div>
                        <div class="admin-event-info-value">${event.client_name || 'Unknown'}</div>
                    </div>
                    <div class="admin-event-info-item">
                        <div class="admin-event-info-label">Email</div>
                        <div class="admin-event-info-value" style="font-size: 12px; word-break: break-all;">${event.client_email || 'N/A'}</div>
                    </div>
                    <div class="admin-event-info-item">
                        <div class="admin-event-info-label">Date & Time</div>
                        <div class="admin-event-info-value">${formattedDate}</div>
                    </div>
                    <div class="admin-event-info-item">
                        <div class="admin-event-info-label">Budget</div>
                        <div class="admin-event-info-value">$${event.price_total ? event.price_total.toFixed(2) : '0.00'}</div>
                    </div>
                    <div class="admin-event-info-item">
                        <div class="admin-event-info-label">Location</div>
                        <div class="admin-event-info-value">${event.location || 'Not specified'}</div>
                    </div>
                    <div class="admin-event-info-item">
                        <div class="admin-event-info-label">Payment</div>
                        <div class="admin-event-info-value">${event.payment_confirmed ? '✅ Confirmed' : '⏳ Pending'}</div>
                    </div>
                </div>

                <div class="admin-event-planner-assignment">
                    <div class="admin-event-planner-label">Assign Planners</div>
                    <div class="admin-event-planner-selector">
                        <div class="multi-select-container" id="plannerSelect-${event.id}">
                            <div class="multi-select-header" onclick="togglePlannerDropdown(${event.id})">
                                <span style="color: #666;">Select planners...</span>
                                <span style="font-size: 12px;">▼</span>
                            </div>
                            <div class="multi-select-items" id="plannerItems-${event.id}">
                                ${planners.map(planner => `
                                    <div class="multi-select-item">
                                        <input type="checkbox" id="planner-${event.id}-${planner.id}" 
                                            value="${planner.id}" 
                                            ${assignedPlannerIds.includes(planner.id) ? 'checked' : ''}
                                            onchange="updateSelectedPlanners(${event.id})">
                                        <label for="planner-${event.id}-${planner.id}" style="cursor: pointer; margin: 0; flex: 1;">${planner.username}</label>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <div class="admin-event-selected-planners" id="selectedPlanners-${event.id}">
                            ${assignedPlannerIds.length === 0 ? '<span style="color: #999; font-size: 13px;">No planners assigned</span>' : ''}
                        </div>
                    </div>
                    <button class="admin-event-save-btn" onclick="savePlannerAssignments(${event.id})">Save Assignments</button>
                </div>

                ${event.notes ? `
                    <div style="border-top: 2px solid #e0e0e0; padding-top: 15px; font-size: 13px; color: #666;">
                        <strong>📝 Notes:</strong><br>${event.notes}
                    </div>
                ` : ''}

                <div style="border-top: 2px solid #e0e0e0; padding-top: 15px;">
                    <button class="btn-small btn-danger" onclick="cancelEventAdmin(${event.id})" style="width: 100%;">Cancel Event</button>
                </div>
            </div>
        `;
    }).join('');

    // Initialize selected planner tags
    events.forEach(event => {
        updateSelectedPlanners(event.id, false);
    });
}

function togglePlannerDropdown(eventId) {
    const dropdown = document.getElementById('plannerItems-' + eventId);
    const header = dropdown.previousElementSibling;
    
    // Close all other dropdowns
    document.querySelectorAll('.multi-select-items.active').forEach(el => {
        if (el.id !== 'plannerItems-' + eventId) {
            el.classList.remove('active');
            el.previousElementSibling.classList.remove('active');
        }
    });

    dropdown.classList.toggle('active');
    header.classList.toggle('active');
}

function updateSelectedPlanners(eventId, renderTags = true) {
    const checkboxes = document.querySelectorAll(`#plannerSelect-${eventId} input[type="checkbox"]:checked`);
    const selectedIds = Array.from(checkboxes).map(cb => cb.value);

    if (renderTags) {
        const container = document.getElementById('selectedPlanners-' + eventId);
        if (selectedIds.length === 0) {
            container.innerHTML = '<span style="color: #999; font-size: 13px;">No planners selected</span>';
        } else {
            container.innerHTML = selectedIds.map(id => {
                const checkbox = document.querySelector(`#planner-${eventId}-${id}`);
                const label = checkbox.nextElementSibling.textContent;
                return `
                    <div class="planner-tag">
                        ${label}
                        <span class="planner-tag-remove" onclick="removePlannerTag(${eventId}, ${id})">✕</span>
                    </div>
                `;
            }).join('');
        }
    }

    // Store selected planners on the event card
    const card = document.querySelector(`[data-event-id="${eventId}"]`);
    if (card) {
        card.dataset.selectedPlanners = selectedIds.join(',');
    }
}

function removePlannerTag(eventId, plannerId) {
    const checkbox = document.querySelector(`#planner-${eventId}-${plannerId}`);
    if (checkbox) {
        checkbox.checked = false;
        updateSelectedPlanners(eventId);
    }
}

async function savePlannerAssignments(eventId) {
    const button = event.target;
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Saving...';

    const card = document.querySelector(`[data-event-id="${eventId}"]`);
    const selectedPlannersStr = card.dataset.selectedPlanners || '';
    const selectedPlannerIds = selectedPlannersStr ? selectedPlannersStr.split(',') : [];

    const user = JSON.parse(sessionStorage.getItem('currentAdminUser'));

    try {
        const response = await fetch(`${API_URL}/admin/assign-planners`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                event_id: eventId,
                planner_ids: selectedPlannerIds
            })
        });

        const data = await response.json();

        if (data.success) {
            button.textContent = '✓ Saved!';
            setTimeout(() => {
                button.textContent = originalText;
                button.disabled = false;
            }, 2000);
        } else {
            alert('Error: ' + (data.message || 'Failed to save assignments'));
            button.textContent = originalText;
            button.disabled = false;
        }
    } catch (error) {
        console.error('Error saving assignments:', error);
        alert('Error saving assignments: ' + error.message);
        button.textContent = originalText;
        button.disabled = false;
    }
}

async function cancelEventAdmin(eventId) {
    if (!confirm('Are you sure you want to cancel this event?')) {
        return;
    }

    const user = JSON.parse(sessionStorage.getItem('currentAdminUser'));
    if (!user) {
        alert('User not found');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/admin/cancel-event`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                event_id: eventId
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(`✓ Event "${data.event.title}" cancelled successfully!`);
            // Reload events to refresh the grid
            loadAdminEvents(user.id);
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (error) {
        console.error('Error cancelling event:', error);
        alert('Failed to cancel event: ' + error.message);
    }
}

function logout() {
    console.log('Logout function called');
    
    // Clear session storage
    sessionStorage.removeItem('user');
    sessionStorage.removeItem('currentPlannerUser');
    sessionStorage.removeItem('currentAdminUser');
    console.log('Session storage cleared');

    // Reset forms - find actual form elements within containers
    const loginFormContainer = document.getElementById('loginForm');
    const registerFormContainer = document.getElementById('registerForm');
    
    if (loginFormContainer) {
        const loginForm = loginFormContainer.querySelector('form');
        if (loginForm) loginForm.reset();
    }
    
    if (registerFormContainer) {
        const registerForm = registerFormContainer.querySelector('form');
        if (registerForm) registerForm.reset();
    }
    console.log('Forms reset');

    // Show login form
    document.getElementById('loginForm').classList.add('active');
    document.getElementById('welcomePage').classList.remove('active');
    document.getElementById('clientDashboard').classList.remove('active');
    document.getElementById('plannerDashboard').classList.remove('active');
    document.getElementById('plannerLanding').classList.remove('active');
    document.getElementById('adminLanding').classList.remove('active');
    document.getElementById('adminEventsDashboard').classList.remove('active');
    document.body.classList.add('login-view');
    console.log('Login view activated');

    clearMessages();
    console.log('Messages cleared - logout complete');
}

// Check if user is already logged in on page load
window.addEventListener('DOMContentLoaded', () => {
    const user = sessionStorage.getItem('user');
    if (user) {
        showWelcomePage(JSON.parse(user));
    } else {
        document.body.classList.add('login-view');
    }
});
