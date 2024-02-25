document.addEventListener('DOMContentLoaded', function () {
    fetchAndDisplayPlaces(); // Fetch and display places data on page load
    // Initialize the DataTable with specific options and store the reference
    var table = $('#placesTable').DataTable({
        "pagingType": "full_numbers",
        "lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]]
    });


// Custom search function
$.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
    for (let column in filters) {
        let columnIndex = table.column(column + ':name').index();
        let filterValues = filters[column];

        if (filterValues.length > 0 && !filterValues.includes(data[columnIndex])) {
            return false; // Exclude row
        }
    }
    return true; // Include row
});

    // Trigger the filter on each column
    $("#placesTable thead tr:eq(1) th input").on('keyup change', function () {
        table.draw();
    });
    

    // Event listener for scrape contacts button
    var scrapeButton = document.getElementById('scrape-contacts-btn');
    var progressPopup = document.getElementById('progressPopup');
    var closeButton = document.getElementsByClassName('close-btn')[0];
    scrapeButton.addEventListener('click', function() {
        progressPopup.style.display = 'block'; // Show the popup
        updateProgress();
        fetch('/run-scraper', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
        })
        .then(response => response.json())
        .then(data => {
            console.log('Scraping started:', data.message);
        })
        .catch(error => console.error('Error:', error));
    });
    
    closeButton.addEventListener('click', function() {
        progressPopup.style.display = 'none'; // Hide the popup
    });
    

    
    
    function updateProgress() {
        var timestamp = new Date().getTime();
        fetch('/scraping-status?_=' + timestamp)
            .then(response => response.json())
            .then(data => {
                var progressBar = document.getElementById('progressBar');
    
                if (data.progress > 0) {
                    progressBar.style.width = data.progress + '%'; // Update the width of the progress bar
                    progressBar.innerText = data.progress + '%'; // Update the text inside the progress bar
                    progressBar.style.display = 'block'; // Show the progress bar
                } else {
                    progressBar.style.display = 'none'; // Hide the progress bar if progress is 0 or less
                }
    
                if (data.progress < 100) {
                    setTimeout(updateProgress, 1000); // Schedule next update
                }
            })
            .catch(error => {
                console.error('Error fetching progress:', error);
                var progressBar = document.getElementById('progressBar');
                progressBar.style.display = 'none'; // Hide in case of error
            });
    }
    
    updateProgress(); // Call the function to start the progress update loop
    
    
});

// Function to fetch and display places in the table
function fetchAndDisplayPlaces() {
    fetch('/get-places')
        .then(response => response.json())
        .then(data => {
            console.log("Data received:", data); // Log the data for inspection
            var table = $('#placesTable').DataTable();
            table.clear(); // Clear the existing data

            let totalPlaces = 0;
            let totalEmails = 0;
            let totalPhoneNumbers = 0;
            let totalApproved = 0;

            data.forEach(place => {
                totalPlaces++;
                if (place.contact_email !== 'none') totalEmails++;
                if (place.contact_phone_number !== 'none') totalPhoneNumbers++;
                if (place.status === 'Approved') totalApproved++;

                var name = place.name || '';
                var email = place.contact_email || '';
                var phoneNumber = place.contact_phone_number || '';
                var website = place.website ? `<a href="${place.website}" target="_blank">Visit</a>` : '';
                var address = place.formatted_address || '';
                var category = createDropdown('category', place.id, ['Retail', 'Wholesale', 'Individual', 'Supplier', 'Other'], place.category);
                var status = createDropdown('status', place.id, ['Disabled', 'Pending Approval', 'Approved', 'Pending Reply', 'Confirmed Lead'], place.status);
                var actions = `<button onclick="updatePlace(${place.id}, 'status', 'Approved')">Approve</button>
                               <button onclick="deletePlace(${place.id})">Delete</button>`;

                table.row.add([name, email, phoneNumber, website, address, category, status, actions]);
            });

            table.draw(); // Redraw the table with new data

            // Update table statistics
            const statsDisplay = document.getElementById('tableStats');
            statsDisplay.innerHTML = `Total Places: ${totalPlaces} | Total Emails: ${totalEmails} | Total Phone Numbers: ${totalPhoneNumbers} | Total Approved: ${totalApproved}`;
        })
        .catch(error => console.error('Error fetching data:', error));
}


function createDropdown(field, id, options, selectedValue) {
    let dropdown = `<select onchange="updatePlace(${id}, '${field}', this.value)">`;
    options.forEach(option => {
        dropdown += `<option value="${option}" ${option === selectedValue ? 'selected' : ''}>${option}</option>`;
    });
    dropdown += '</select>';
    return dropdown;
}

function updatePlace(placeId, field, value) {
    fetch(`/update-place/${placeId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ [field]: value })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log(`Update sent for place ID ${placeId}: ${field} changed to ${value}`);
        console.log(data.message);
        
        // Refresh the table to reflect the changes
        fetchAndDisplayPlaces();
    })
    .catch(error => {
        console.error('Error updating place:', error);
    });
}

function deletePlace(placeId) {
    fetch(`/delete-place/${placeId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        if (response.status === 204) {
            console.log(`Place with ID ${placeId} deleted successfully.`);
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data && data.message) {
            console.log(data.message);
            // Refresh the table after successful deletion
            fetchAndDisplayPlaces();
        }
    })
    .catch(error => console.error('Error deleting place:', error));
}

document.getElementById('scrape-contacts-btn').addEventListener('click', function() {
    fetch('/run-scraper', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log('Scraping started:', data.message);
        // You can update the UI here to notify the user that scraping has started
    })
    .catch(error => console.error('Error:', error));
});
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        var column = this.getAttribute('data-column');
        // Position the popup near the button
        // (You'll need to calculate the position based on the button's position)
        var popup = document.getElementById('filter-popup');
        popup.style.display = 'block';
        // Save the current column in the popup for reference
        popup.setAttribute('data-current-column', column);
        // Populate current filters for this column
        populateCurrentFilters(column);
    });
});
var filters = {
    'name': [],
    // ... other columns
};

function addFilter(column, filter) {
    if (!filters[column].includes(filter)) {
        filters[column].push(filter);
    }
    refreshDataTable(); // Refresh the DataTable with new filters
    updateFilterButtonAppearance(); // Update the appearance of filter buttons
}

function deleteFilter(column, filter) {
    var index = filters[column].indexOf(filter);
    if (index > -1) {
        filters[column].splice(index, 1);
    }
    refreshDataTable(); // Refresh the DataTable with new filters
    updateFilterButtonAppearance(); // Update the appearance of filter buttons
}



document.getElementById('filterButton').addEventListener('click', function() {
    var filterArea = document.getElementById('filterArea');
    if (filterArea.style.display === 'none') {
        filterArea.style.display = 'block'; // Show the filter area
    } else {
        filterArea.style.display = 'none'; // Hide the filter area
    }
});