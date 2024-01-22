document.addEventListener('DOMContentLoaded', function() {
    fetchUsers();

    async function fetchUsers() {
        try {
            const response = await fetch('/api/users');
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const users = await response.json(); // Parse the JSON response
    
            populateUsers(users); // Assuming users is an array of user objects
        } catch (error) {
            console.error('Error fetching users:', error);
        }
    }

    function populateUsers(users) {
        const usersContainer = document.getElementById('usersContainer');
        users.forEach(user => {
            const userDiv = document.createElement('div');
            userDiv.className = 'col-md-4 mb-3';
            userDiv.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" class="form-control userEmail" value="${user.email}">
                        </div>
                        <div class="form-group">
                            <label>Permission Level</label>
                            <select class="form-control userPermission">
                                <option value="User" ${user.permission_level === 'User' ? 'selected' : ''}>User</option>
                                <option value="Admin" ${user.permission_level === 'Admin' ? 'selected' : ''}>Admin</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Status</label>
                            <select class="form-control userStatus">
                                <option value="Active" ${user.status === 'Active' ? 'selected' : ''}>Active</option>
                                <option value="Inactive" ${user.status === 'Inactive' ? 'selected' : ''}>Inactive</option>
                                <option value="Pending Approval" ${user.status === 'Pending Approval' ? 'selected' : ''}>Pending Approval</option>
                            </select>
                        </div>
                        <button onclick="updateUser(${user.id})" class="btn btn-primary">Update</button>
                    </div>
                </div>
            `;
            usersContainer.appendChild(userDiv);
        });
    }

    window.updateUser = async function(userId) {
        const userDiv = document.querySelector(`button[onclick="updateUser(${userId})"]`).closest('.card-body');
        const email = userDiv.querySelector('.userEmail').value;
        const permission = userDiv.querySelector('.userPermission').value;
        const status = userDiv.querySelector('.userStatus').value;

        await fetch(`/api/update-user/${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, permission_level: permission, status })
        });

        // You can add a message to show the update is successful or handle errors
    };
});
