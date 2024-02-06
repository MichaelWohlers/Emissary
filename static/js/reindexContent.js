// Global Variables
var map;
var markerLayerGroup;
var intervalId; // Global scope declaration
var markersClusterGroup;

// Initialization Functions
function initializeMap() {
    map = L.map('map').setView([38.497, -90.394], 8);
    markerLayerGroup = L.layerGroup().addTo(map);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap / OveratureMaps'
    }).addTo(map);
    markersClusterGroup = L.markerClusterGroup().addTo(map);

    var drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    setupDrawControl(drawnItems);
    setupGeocoder(drawnItems);
    addGearMenuControl(drawnItems);
    
}

function setupGeocoder(drawnItems) {
    var geocoder = L.Control.geocoder({
        defaultMarkGeocode: false
    }).on('markgeocode', function(e) {
        var center = e.geocode.center;
        var bounds = L.latLngBounds([
            [center.lat - 0.05, center.lng - 0.05],
            [center.lat + 0.05, center.lng + 0.05]
        ]);

        drawnItems.clearLayers();
        var layer = L.rectangle(bounds, {color: 'blue'}).addTo(drawnItems);
        updateBboxText(layer);
        map.fitBounds(bounds);
    }).addTo(map);
}

function setupDrawControl(drawnItems) {
    var drawControl = new L.Control.Draw({
        draw: {
            polygon: false,
            marker: false,
            circle: false,
            circlemarker: false,
            polyline: false,
            rectangle: {
                shapeOptions: {
                    color: 'blue'
                }
            }
        },
        edit: {
            featureGroup: drawnItems
        }
    });
    map.addControl(drawControl);

    map.on('draw:created', function(event) { onDrawCreated(event, drawnItems); });
    map.on('draw:edited', function(event) { onDrawEdited(event); });
}

// Event Handlers
function onDrawCreated(event, drawnItems) {
    drawnItems.clearLayers();
    var layer = event.layer;
    drawnItems.addLayer(layer);
    updateBboxText(layer);
}

function onDrawEdited(event) {
    var layers = event.layers;
    layers.eachLayer(function(layer) {
        if (layer instanceof L.Rectangle) {
            updateBboxText(layer);
        }
    });
}

// Data Display Functions
function displayDataOnMap(geojsonData) {
    if (!map) {
        console.error('Map not initialized');
        return;
    }

    var newGeoJsonLayer = L.geoJSON(geojsonData, {
        pointToLayer: function(feature, latlng) {
            return L.marker(latlng);
        },
        onEachFeature: onEachFeature
    });

    newGeoJsonLayer.eachLayer(function(layer) {
        markersClusterGroup.addLayer(layer);
    });

    if (!map.hasLayer(markersClusterGroup)) {
        markersClusterGroup.addTo(map);
    }
}
function addGearMenuControl(drawnItems) {
    L.Control.GearMenu = L.Control.extend({
        onAdd: function(map) {
            var container = L.DomUtil.create('div', 'leaflet-control-gear flex-container');
            L.DomEvent.disableClickPropagation(container);

            // Gear Icon as a Button
            var gearButton = L.DomUtil.create('button', 'gear-icon', container);
            gearButton.innerHTML = '&#9881;'; // Gear Icon&#9881; '&#x2699;'
            gearButton.onclick = toggleMenuVisibility;

            // Function to toggle menu visibility and map zoom
            function toggleMenuVisibility() {
                var menu = container.querySelector('.gear-menu');
                var isHidden = menu.classList.contains('hidden');
                
                // Toggle menu visibility
                menu.classList.toggle('hidden');
                gearButton.classList.toggle('active');

                // Toggle map scroll zoom
                if (!isHidden) {
                    map.scrollWheelZoom.enable();
                } else {
                    map.scrollWheelZoom.disable();
                }
            }

           
        

            // Menu Container (Initially Hidden)
            var menu = L.DomUtil.create('div', 'gear-menu hidden', container);
            menu.innerHTML = `<div class="bg-white py-2 collapse-inner rounded"><div class="center-container">
            <h6 class="collapse-header">Search Filters:</h6>
        </div>
            <form id="queryForm">
                <div class="dropdown">
                    <div class="center-container">
                        <button class="collapse-item btn btn-secondary dropdown-toggle" style="padding: 7px 30px;" id="categoryDropdown" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                            Select Categories
                        </button>
                        <div id="categoryList" class="dropdown-menu" aria-labelledby="categoryDropdown" style="max-height: 300px; overflow-y: auto; max-width: 350px; overflow-x: auto;">
                            <!-- Search Bar for Categories -->
                            <div class="form-group">
                                <input type="text" class="form-control-sm" id="searchInput" placeholder="Search Categories">
                            </div>
                            <!-- Container for dynamically populated keywords -->
                            <div id="categoryItems">
                                <!-- Keywords will be populated dynamically with checkboxes here -->
                            </div>
                        </div>
                    </div>    
                </div>
            
                <div class="dropdown mt-3  ">
                    <div class="center-container mb-3">
                        <button class="collapse-item btn btn-secondary dropdown-toggle"style="padding: 7px 30px;" type="button" id="keywordDropdown" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                            Select Keywords
                        </button>
                        <div id="keywordList" class="dropdown-menu" aria-labelledby="keywordDropdown" style="max-height: 300px; overflow-y: auto; max-width: 350px; overflow-x: auto;">
                            <!-- Search Bar for Keywords -->
                            <div class="form-group">
                                <input type="text" class="form-control-sm" id="searchKeyword" placeholder="Search Keyword">
                            </div>
                            <!-- Container for dynamically populated keywords -->
                            <div id="keywordItems">
                                <!-- Keywords will be populated dynamically with checkboxes here -->
                            </div>
                        </div> 
                    </div>
                    <div style="border-bottom: 1px solid #ccc; margin: 5px 0;"></div>
                    <div class="center-container">

                        <h6 class="collapse-header">Do not Include:</h6>

                        <div class="form-group mb-2">
                            <input type="text" class="collapse-item form-control-sm" id="exclusionWords" placeholder="JCPenny,Walmart,etc.">
                        </div>
                    </div>
                    <div style="border-bottom: 1px solid #ccc; margin: 5px 0;"></div>
                    <div class="center-container">
                        <button type="submit" id='fetchDataButton' class="collapse-item-button btn btn-primary-sm"data-toggle="collapse" data-target="#formCollapse">Fetch Places</button>
                    </div>
            </form>
            </div>
`;
            

            return container;
        }
    });

    map.addControl(new L.Control.GearMenu({ position: 'topright' }));
}
function toggleMapView(drawnItems){L.Control.ToggleView = L.Control.extend({
    onAdd: function(map) {
        // Create a div to hold the control
        var container = L.DomUtil.create('div', 'leaflet-control-toggle-view leaflet-bar');

        // Prevent map panning/zooming when interacting with the control
        L.DomEvent.disableClickPropagation(container);

        // Add your custom HTML for the toggle switch
        container.innerHTML = `
            <div class="form-group" style="margin-bottom: 1px;">
                <label for="mapTableToggle">Toggle Map/Table View:</label>
                <label class="switch">
                    <input type="checkbox" id="mapTableToggle" class="rounded-circle border-0">
                    <span class="slider round"></span>
                </label>
            </div>
        `;

        // Add any event listeners if necessary
        var checkbox = container.querySelector('#mapTableToggle');
        checkbox.addEventListener('change', function() {
            // Logic to toggle between map and table view
            // Example: map.setView(...), toggle visibility of map/table elements
        });

        return container;
    }
});

// Add the new control to the map
map.addControl(new L.Control.ToggleView({ position: 'topright' })); // You can choose the position
}






function onEachFeature(feature, layer) {
        if (feature.properties) {
        var popupContent = '<div style="font-family: Arial, sans-serif; color: #333;">' +
                           '<h3 style="color: #007bff; margin-bottom: 5px;">' + (feature.properties.names?.common[0]?.value || 'N/A') + '</h2>' +
                           '<p><strong>Category:</strong> ' + (feature.properties.categories?.main || 'N/A') + '</p>';

        if (Array.isArray(feature.properties.socials) && feature.properties.socials.length > 0) {
            popupContent += '<p><strong>Social Media:</strong> <a href="' + feature.properties.socials[0] + '" target="_blank" style="color: #007bff;">Visit</a></p>';
        } else {
            popupContent += '<p><strong>Social Media:</strong> N/A</p>';
        }

        if (Array.isArray(feature.properties.phones) && feature.properties.phones.length > 0) {
            popupContent += '<p><strong>Phone Number:</strong> ' + feature.properties.phones[0] + '</p>';
        } else {
            popupContent += '<p><strong>Phone Number:</strong> N/A</p>';
        }

        if (feature.properties.addresses && feature.properties.addresses.length > 0) {
            var address = feature.properties.addresses[0];
            var addressString = [address.freeform, address.locality, address.region].filter(Boolean).join(', ');
            popupContent += '<p><strong>Address:</strong> ' + addressString + '</p>';
        } else {
            popupContent += '<p><strong>Address:</strong> N/A</p>';
        }

        if (Array.isArray(feature.properties.websites) && feature.properties.websites.length > 0) {
            popupContent += '<p><strong>Website:</strong> <a href="' + feature.properties.websites[0] + '" target="_blank" style="color: #007bff;">Visit</a></p>';
        } else {
            popupContent += '<p><strong>Website:</strong> N/A</p>';
        }

        popupContent += '</div>';
        layer.bindPopup(popupContent);
    }

}  



// Function to update table data
function displayDataOnTable(data) {
    var table = $('#dataTable').DataTable();

    data.features.forEach(feature => {
        const addressInfo = feature.properties.addresses ? feature.properties.addresses[0] : {};
        const address = [
            addressInfo.freeform,
            addressInfo.locality,
            addressInfo.region,
            addressInfo.postcode
        ].filter(part => part).join(', ');

        table.row.add([
            '<input type="checkbox" name="id[]" value="' + feature.properties.id + '">',
            feature.properties.names.common[0].value,
            feature.properties.categories.main,
            feature.properties.websites ? `<a href="${feature.properties.websites[0]}">${feature.properties.websites[0]}</a>` : 'N/A',
            feature.properties.socials ? feature.properties.socials.map(social => `<a href="${social}">${new URL(social).hostname}</a>`).join(', ') : 'N/A',
            feature.properties.phones ? feature.properties.phones[0] : 'N/A',
            address || 'N/A',
            '<button class="btn btn-primary btn-sm">Action</button>'
        ]);
    });

    table.draw(); // Redraw the DataTable
}

// Utility Functions

// Function to start the interval for fetchTempData
function startFetchingTempData() {
    intervalId = setInterval(fetchTempData, 3000); // Fetch every 5 seconds
    console.log('interval set')
    
}
function updateBboxText(layer) {
    var bounds = layer.getBounds();
    var sw = bounds.getSouthWest();
    var ne = bounds.getNorthEast();

    var bboxText = `${sw.lng.toFixed(7)},${sw.lat.toFixed(7)},${ne.lng.toFixed(7)},${ne.lat.toFixed(7)}`;
    var bboxTextElement = document.getElementById('bboxTextElement');
    if (!bboxTextElement) {
        console.error('bboxTextElement not found');
        return;
    }
    bboxTextElement.value = bboxText;
}

function fetchData(queryData) {
    $('#dataTable').DataTable().clear();
    $('#dataTable').DataTable().draw();
    markerLayerGroup.clearLayers();
    markersClusterGroup.clearLayers();



    // Display the loading icon
    document.getElementById('loadingIcon').style.display = 'block';

    // Record the start time
    const startTime = Date.now();

    fetch('/fetch-geojson', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(queryData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Calculate and log the elapsed time
        const endTime = Date.now();
        const elapsedTime = endTime - startTime;
        console.log(`Request completed in ${elapsedTime} ms`);

    })
    .catch(error => {
        // Hide the loading icon and log error and elapsed time
        const endTime = Date.now();
        const elapsedTime = endTime - startTime;
        console.error(`Error: ${error}. Request failed in ${elapsedTime} ms`);

    });
}

function fetchTempData() {
    // Record the start time
    const startTime = Date.now();
    fetch('/fetch-temp-geojson', {
        method: 'GET'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errData => {
                throw new Error(`HTTP error! Status: ${response.status}, Message: ${errData.message}`);
            });
        }
        return response.json();
    })
    .then(data => {
        

        displayDataOnTable(data); // Populate the table with data

        displayDataOnMap(data); // Handle the data
    })
    .catch(error => {
        const endTime = Date.now();

        const elapsedTime = endTime - startTime;
        // log error, and stop interval
        console.error(`Error: ${error}. Request failed in ${elapsedTime} ms`);


        if (error.message.includes('404')) { // Assuming 404 means file not found
            clearInterval(intervalId);
            const endTime = Date.now();

            const elapsedTime = endTime - startTime;
            document.getElementById('loadingIcon').style.display = 'none';

            console.log('No more data to fetch, stopping interval. Total Time = ',{elapsedTime});
        }
    });
}

function fetchSavedData() {
    // Display the loading icon
    document.getElementById('loadingIcon').style.display = 'block';

    // Record the start time
    const startTime = Date.now();

    fetch('geojson/output.geojson', {
        method: 'GET'
        
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        displayDataOnTable(data); // Populate the table with data
        // Calculate and log the elapsed time
        const endTime = Date.now();
        const elapsedTime = endTime - startTime;
        console.log(`Request completed in ${elapsedTime} ms`);

        document.getElementById('loadingIcon').style.display = 'none';
        displayDataOnMap(data); // Handle the data
    })
    .catch(error => {
        // Hide the loading icon and log error and elapsed time
        const endTime = Date.now();
        const elapsedTime = endTime - startTime;
        console.error(`Error: ${error}. Request failed in ${elapsedTime} ms`);

        document.getElementById('loadingIcon').style.display = 'none';
    });
}

function fetchAndDisplayCategories() {
    console.log('fetching Categories')
    fetch('/get_categories')
    .then(response => response.json())
    .then(data => {
        var categoryItems = document.getElementById('categoryItems');
        categoryItems.innerHTML = ''; // Clear existing categories

        data.categories.sort().forEach(category => {
            var label = document.createElement('label');
            label.style.whiteSpace = 'nowrap';
            label.style.display = 'block';

            var checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = 'categories[]';
            checkbox.value = category;
            checkbox.classList.add('ml-2');

            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(category.replace(/_/g, ' ').toUpperCase()));
            categoryItems.appendChild(label);
        });

        categoryList.addEventListener('change', fetchAndDisplayKeywords);
    })
    .catch(error => console.error('Error fetching categories:', error));
}

function fetchAndDisplayKeywords() {
    var selectedCategories = Array.from(document.querySelectorAll('#categoryList input[type="checkbox"]:checked'))
                                  .map(checkbox => checkbox.value);

    fetch('/get_keywords', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ categories: selectedCategories })
    })
    .then(response => response.json())
    .then(data => {
        var keywordItems = document.getElementById('keywordItems');
        keywordItems.innerHTML = ''; // Clear existing keywords

        data.keywords.sort().forEach(keyword => {
            var label = document.createElement('label');
            label.classList.add('checkbox-item');
            label.style.whiteSpace = 'nowrap';
            label.style.display = 'block';

            var checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = 'keywords[]';
            checkbox.value = keyword;
            checkbox.classList.add('ml-2');

            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(keyword.replace(/_/g, ' ').toUpperCase()));
            keywordItems.appendChild(label);
        });
    })
    .catch(error => console.error('Error fetching keywords:', error));
}

// UI Interaction Functions
function filterCategories() {
    var searchInput = document.getElementById('searchInput').value.toLowerCase();
    var labels = document.querySelectorAll('#categoryList label');

    labels.forEach(function(label) {
        var text = label.textContent.toLowerCase();
        if (text.includes(searchInput)) {
            label.style.display = "block";
            label.style.whiteSpace = 'nowrap';

        } else {
            label.style.display = "none";
        }
    });
}

function filterKeywords() {
    var searchInput = document.getElementById('searchKeyword').value.toLowerCase();
    var labels = document.querySelectorAll('#keywordItems label');

    labels.forEach(function(label) {
        var text = label.textContent.toLowerCase();
        if (text.includes(searchInput)) {
            label.style.display = "block";
            label.style.whiteSpace = 'nowrap';

        } else {
            label.style.display = "none";
        }
    });
}

$(document).ready(function() {
    initializeMap();
    fetchAndDisplayCategories();
    //startFetchingTempData();

    // Connect to the Socket.IO server.
    // The connection URL has to be updated with your actual server URL
    var socket = io.connect('https://iemissary-e39e92466db2.herokuapp.com/'); // Use 'wss://your-server-url' for secure connections

    socket.on('connect', function() {
        console.log('WebSocket Connected');
        // Request to start fetching data, if needed
    });

    socket.on('geojson_data', function(message) {
        console.log('Received GeoJSON data:', message);
    
        // Extract the ArrayBuffer from the message object
        const arrayBuffer = message.data;
        console.log('ArrayBuffer:', arrayBuffer);
    
        if (arrayBuffer instanceof ArrayBuffer) {
            // Convert ArrayBuffer to String
            const decoder = new TextDecoder('utf-8');
            const geoJsonString = decoder.decode(arrayBuffer); // Pass the raw ArrayBuffer here
            console.log('GeoJSON String:', geoJsonString);
    
            // Parse String as JSON
            try {
                const geoJsonObject = JSON.parse(geoJsonString);
                console.log('GeoJSON Object:', geoJsonObject);
    
                // Proceed with handling the GeoJSON object
                // For example, you can call your display functions here
                displayDataOnTable(geoJsonObject); // Populate the table with data
                displayDataOnMap(geoJsonObject); // Handle the data on the map
            } catch (error) {
                console.error('Error parsing GeoJSON string:', error);
            }
        } else {
            console.error('Received data is not an ArrayBuffer:', arrayBuffer);
        }
    });
    
    

    socket.on('complete', function() {
        console.log('Data fetching complete');
        document.getElementById('loadingIcon').style.display = 'none';
    });




    document.getElementById('searchInput').addEventListener('input', filterCategories);
    document.getElementById('searchKeyword').addEventListener('input', filterKeywords);
    document.getElementById('queryForm').addEventListener('submit', function(e) {
        e.preventDefault(); // Prevent the default form submission
        // Access the gear button and menu
        var gearButton = document.querySelector('.gear-icon');
        var menu = document.querySelector('.gear-menu');

        // Check if elements exist
        if (gearButton && menu) {
            // Toggle a class on the gear button, e.g., 'active'
            gearButton.classList.toggle('active');

            // Toggle a class on the menu, e.g., 'hidden'
            menu.classList.toggle('hidden');
        }
        // Get user inputs
        const keywordCheckboxes = document.querySelectorAll('#keywordItems input[type="checkbox"]:checked');
        const keywordsArray = Array.from(keywordCheckboxes).map(checkbox => checkbox.value);
    
        // Join the keywords into a single string, separated by commas
        const keywords = keywordsArray.join(',');
    
        const exclusionWords = document.getElementById('exclusionWords').value;
        const bboxText = document.getElementById('bboxTextElement').value;
        const bboxValues = bboxText.split(',');
    
        if (bboxValues.length !== 4) {
            console.error('Invalid bbox format. Expected format: minx,miny,maxx,maxy');
            return;
        }
    
        const queryData = {
            keywords: keywords,
            exclusionWords: exclusionWords,
            bbox: bboxValues.map(v => parseFloat(v.trim())) // Convert each value to a float
        };
        markerLayerGroup.clearLayers();
        
        // Fetch GeoJSON data and display on the map
        fetchData(queryData);
        console.log('Fetching data...');
    
        // Set a delay of 10 seconds before fetching temporary data
        //setTimeout(function() {
        //    console.log('Starting to fetch temporary data...');
        //    startFetchingTempData();
       // }, 2000); // 10000 milliseconds = 10 seconds
            
    });
    document.getElementById('mapTableToggle').addEventListener('change', function() {
        var mapView = document.getElementById('map'); // Replace with the actual ID of your map container
        var tableView = document.getElementById('tableContainer'); // Replace with the actual ID of your table container
    
        if (this.checked) {
            mapView.style.display = 'none';
            tableView.style.display = 'block';
        } else {
            mapView.style.display = 'block';
            tableView.style.display = 'none';
        }
    });
    


    if (!$.fn.dataTable.isDataTable('#dataTable')) {
        var table = $('#dataTable').DataTable({
            // DataTable options
        });
    }

    // Event handlers for DataTable
    setupDataTableEventHandlers(table);
    // Start fetching temporary data at regular intervals
});
function setupDataTableEventHandlers(table) {
    // Example: Click event on "Select all" control
    $('#select-all').on('click', function() {
        var rows = table.rows({ 'search': 'applied' }).nodes();
        $('input[type="checkbox"]', rows).prop('checked', this.checked);
    });

    // ... other event handlers ...
}

