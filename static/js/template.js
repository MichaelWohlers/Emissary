document.addEventListener('DOMContentLoaded', function() {
    loadSavedTemplates();
});

function loadSavedTemplates() {
    fetch('/get-saved-templates')
    .then(response => response.json())
    .then(templates => {
        const templateSelect = document.getElementById('savedTemplateSelect');
        templates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.name;
            templateSelect.appendChild(option);
        });
    })
    .catch(error => console.error('Error:', error));
}

document.getElementById('saveTemplateButton').addEventListener('click', function() {
    const templateNameInput = document.getElementById('templateNameInput');
    const subjectInput = document.getElementById('templateSubjectInput');
    const bodyTextarea = document.getElementById('templateBodyTextarea');

    const templateData = { 
        name: templateNameInput.value, 
        subject: subjectInput.value, 
        body: bodyTextarea.value 
    };

    fetch('/save-template', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(templateData),
    })
    .then(response => response.json())
    .then(data => {
        // Handle response, e.g., show a success message
        alert('Template saved successfully');

        // Clear the input fields
        templateNameInput.value = '';
        subjectInput.value = '';
        bodyTextarea.value = '';
        clearSavedTemplateSelect();
        loadSavedTemplates();

    })
    .catch(error => console.error('Error:', error));
});


document.getElementById('savedTemplateSelect').addEventListener('change', function() {
    const templateId = this.value;
    fetch(`/get-template/${templateId}`)
    .then(response => response.json())
    .then(template => {
        document.getElementById('templateNameInput').value = template.name;
        document.getElementById('templateSubjectInput').value = template.subject;
        document.getElementById('templateBodyTextarea').value = template.body;
        })
        .catch(error => console.error('Error:', error));
        });

function clearSavedTemplateSelect() {
    const selectElement = document.getElementById('savedTemplateSelect');
    // Remove all options except the first placeholder option
    selectElement.innerHTML = '<option value="">Choose a template...</option>';
}

document.getElementById('deleteTemplateButton').addEventListener('click', function() {
    const selectedTemplateId = document.getElementById('savedTemplateSelect').value;
    if (selectedTemplateId) {
        fetch(`/delete-template/${selectedTemplateId}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            alert(data.message);  // Or use a more styled message
            clearTemplateFields();
            clearSavedTemplateSelect();
            loadSavedTemplates();  // Refresh the templates dropdown
        })
        .catch(error => console.error('Error:', error));
    } else {
        alert('No template selected');  // Or handle this scenario as needed
    }
});

function clearTemplateFields() {
    document.getElementById('templateNameInput').value = '';
    document.getElementById('templateSubjectInput').value = '';
    document.getElementById('templateBodyTextarea').value = '';
    document.getElementById('savedTemplateSelect').value = '';
}
