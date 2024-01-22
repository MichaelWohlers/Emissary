window.onload = function() {
    fetchStatusOptions();
    loadSavedTemplates()
};

function fetchStatusOptions() {
    fetch('/email_feature', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(statusValues => {
        populateStatusDropdown(statusValues);
    })
    .catch(error => console.error('Error:', error));
}

function populateStatusDropdown(statusValues) {
    const dropdown = document.getElementById('statusSelect');
    // Clear existing options
    dropdown.innerHTML = '<option value="">Select a Status</option>'; // Default blank option

    // Populate dropdown with fetched status values
    statusValues.forEach(status => {
        const option = document.createElement('option');
        option.value = status;
        option.textContent = status;
        dropdown.appendChild(option);
    });
}

document.getElementById('statusSelect').addEventListener('change', function() {
    const selectedStatus = this.value;
    fetch('/email_feature', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 'status': selectedStatus }),
    })
    .then(response => response.json())
    .then(emailAddresses => {
        updateEmailList(emailAddresses);
    })
    .catch(error => console.error('Error:', error));
});

function updateEmailList(emailAddresses) {
    // Get the textarea where emails should be inserted
    const emailTextarea = document.getElementById('emailList');

    // Check for 'sales@' emails and add 'purchasing@' emails, case-insensitive
    const additionalEmails = emailAddresses.reduce((acc, email) => {
        if (email.toLowerCase().includes('sales@')) {
            const domain = email.split('@')[1];
            acc.push(`purchasing@${domain}`);
        }
        return acc;
    }, []);

    // Combine original and additional emails
    const combinedEmails = emailAddresses.concat(additionalEmails);

    // Set the combined emails as the value of the textarea
    emailTextarea.value = combinedEmails.join(', ');
}




function loadSavedTemplates() {
    fetch('/get-saved-templates')
    .then(response => response.json())
    .then(templates => {
        const templateSelect = document.getElementById('templateSelect');
        templates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.name;
            templateSelect.appendChild(option);
        });
    })
    .catch(error => console.error('Error:', error));
}

document.getElementById('templateSelect').addEventListener('change', function() {
    const templateId = this.value;
    fetch(`/get-template/${templateId}`)
    .then(response => response.json())
    .then(template => {
        document.getElementById('subjectInput').value = template.subject;
        document.getElementById('bodyTextarea').value = template.body;
        })
        .catch(error => console.error('Error:', error));
        });

document.getElementById('sendEmailButton').addEventListener('click', function() {
    // Retrieve email addresses from the textarea
    const emailListText = document.getElementById('emailList').value;
    const emailAddresses = emailListText.split(/[\s,;]+/); // Split by space, comma, or semicolon

    // Filter out empty strings or invalid email addresses if necessary
    const validEmailAddresses = emailAddresses.filter(email => email.includes('@'));

    if (validEmailAddresses.length === 0) {
        alert('No valid email addresses entered.');
        return;
    }

    const confirmation = window.confirm(`Are you sure you want to send ${validEmailAddresses.length} emails?`);
    if (confirmation) {
        const subject = document.getElementById('subjectInput').value;
        const body = document.getElementById('bodyTextarea').value;

        fetch('/send-emails', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ emailAddresses: validEmailAddresses, subject, body }),
        })
        .then(response => response.json())
        .then(data => {
            alert('Emails sent successfully.');
        })
        .catch(error => console.error('Error:', error));
    }
});
