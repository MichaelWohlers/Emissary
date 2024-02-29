// Global Variables
var map;
var markerLayerGroup;
var intervalId; // Global scope declaration
var markersClusterGroup;
var heatmapLayer;
var currentHeatmapType = 3; // 3: off, 0: perCapitaIncome, 1: population, 2: prosperity index
var countyLayer; // Declare countyLayer globally

function prepareHeatmapData(data, currentHeatmapType) {
    var heatmapData = [];
    data.features.forEach(function(feature) {
        if (feature.geometry && feature.geometry.type === "MultiPolygon") {
            // Directly calculate the centroid for MultiPolygon
            var centroids = [];
            feature.geometry.coordinates.forEach(polygon => {
                var centroidLng = 0, centroidLat = 0, totalPoints = 0;
                polygon[0].forEach(coord => { // Assuming polygon[0] is the outer ring
                    centroidLng += coord[0];
                    centroidLat += coord[1];
                    totalPoints++;
                });
                centroids.push([centroidLng / totalPoints, centroidLat / totalPoints]);
            });

            // Average the centroids if there are multiple
            var avgCentroid = centroids.reduce((acc, cur) => {
                return [acc[0] + cur[0] / centroids.length, acc[1] + cur[1] / centroids.length];
            }, [0, 0]);

            var lat = avgCentroid[1];
            var lng = avgCentroid[0];
            var intensity = determineIntensity(feature, currentHeatmapType);

            heatmapData.push([lat, lng, intensity]);
        }
    });
    return heatmapData;
}

function determineIntensity(feature, currentHeatmapType) {
    if (currentHeatmapType === 3) {
        return null;
    }
    var population = parseInt(feature.properties.population, 10);
    var perCapitaIncome = parseFloat(feature.properties.perCapitaIncome);
    var area = parseFloat(feature.properties.area);

    switch (currentHeatmapType) {
        case 0: // perCapitaIncome
            return perCapitaIncome || null;
        case 1: // population
            return population || null;
        case 2: // prosperity index
            // Ensuring we have all the needed data to calculate the prosperity index
            if (population && perCapitaIncome && area) {
                // Calculate prosperity index as (population * perCapitaIncome) / area
                return (population * perCapitaIncome) / area;
            }
            return null;
        default:
            return null;
    }
}





// Assuming calculateCentroid is correctly defined elsewhere in your code

function toggleHeatmap() {
    // Increment currentHeatmapType to cycle through the states.
    currentHeatmapType = (currentHeatmapType + 1) % 4; // Cycle through -1 to 2
    console.log("toggleHeatmap called. Current state:", currentHeatmapType);

    // Remove existing heatmap layer if it exists.
    if (heatmapLayer) {
        map.removeLayer(heatmapLayer);
        heatmapLayer = null; // Ensure the reference is cleared.
    }

    // If currentHeatmapType is -1 (off), reinitialize the heatmap layer without data.
    if (currentHeatmapType === 3) {
        // Reinitialize the heatmapLayer with an empty dataset or hide it.
        heatmapLayer = L.heatLayer([], {
            radius: 25,
            blur: 15,
            // Ensure the gradient is such that it would not display any data.
            gradient: {0.0: 'rgba(0,0,0,0)'}
        }).addTo(map);
        return;
    }

    // Proceed to load and display the heatmap for the currentHeatmapType if not -1.
    fetch('/county-data')
        .then(response => response.json())
        .then(data => {
            var heatmapData = prepareHeatmapData(data, currentHeatmapType);

            // Define custom gradient here as before.
            var customGradient = {
                0.0: 'rgba(0,0,0,0)', // Fully transparent for the base state
                0.2: 'blue', // Cooler colors for lower values
                0.4: 'lime', // Intermediate values
                0.6: 'yellow', // Warmer colors for higher values
                1.0: 'red' // Hot colors for the highest values
            };

            // Create and add the heatmap layer if we're not in the "off" state (-1).
            heatmapLayer = L.heatLayer(heatmapData, {
                radius: 25,
                blur: 15,
                gradient: customGradient
            }).addTo(map);
        })
        .catch(error => console.error('Error loading county data for heatmap:', error));
}







//var newGeoJsonLayer; // Add this line

// Function to start the tour
function startIntroTour() {
    // Create an Intro.js instance
    var intro = introJs();

    // Set options and steps programmatically
    intro.setOptions({
        steps: [
            {
                // Step 1: Draw Rectangle Button
                element: document.querySelector('.leaflet-draw-draw-rectangle'),
                intro: "Click here to draw the search area on the map.",
                position: 'right'
            },
            {
                // Step 3: Search Field
                element: document.querySelector('.leaflet-control-geocoder-icon'),
                intro: "[Optional]Use this search field to find specific locations on the map instead of drawing the search area.",
                position: 'bottom'
            },
            {
                // Step 2: Gear Icon for opening the filter menu
                element: document.querySelector('.gear-icon'),
                intro: "After defining a search area, click the gear icon to setup the search filters.",
                position: 'top'
            },
            
            {
                // Step 4: results switch
                element: document.querySelector('.slider'),
                intro: "View results on the map or in a searchable table. You can save results by selecting them in the table and clicking the add to contacts button.",
                position: 'bottom'
            },
            {
                // Step 5: Tools menu
                element: document.getElementById('toolsDropdown'),
                intro: "View saved contacts in address book, or use the other tools as they are added here.",
                position: 'bottom'
            }
        ],
        showBullets: false, // Optionally, disable navigation bullets
        showProgress: true, // Optionally, show progress through the tour
        exitOnOverlayClick: true, // Allow users to exit the tour by clicking the overlay
        scrollToElement: true // Scroll to the highlighted element
    });

    // Start the tour
    intro.start();
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
    // Add a custom control for toggling the heatmap
    var heatmapToggleControl = L.control({position: 'topright'});
    heatmapToggleControl.onAdd = function (map) {
        var div = L.DomUtil.create('div', 'control-custom');
        div.innerHTML = '<button id="heatmapToggle">Toggle Heatmap</button>';
        L.DomEvent.on(div, 'click', function (e) {
            L.DomEvent.stopPropagation(e);
            toggleHeatmap(); // Function to toggle heatmap views
        });
        return div;
    };
    heatmapToggleControl.addTo(map);
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
function displayDataOnMap(geojsonData, interactionHandler) {
        if (!map) {
        console.error('Map not initialized');
        return;
    }

    var newGeoJsonLayer = L.geoJSON(geojsonData, {
        pointToLayer: function(feature, latlng) {
            return L.marker(latlng);
        },
        onEachFeature: interactionHandler || onEachFeature
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
                        <span>Average Request Time = 3 min.</span>
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
            address || 'N/A'
        ]);
    });

    table.draw(); // Redraw the DataTable
}

// Utility Functions


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


function fetchAndDisplayCountyData() {
    fetch('/county-data')
        .then(response => response.json())
        .then(data => {
            countyLayer = L.geoJSON(data, {
                style: function(feature) {
                    // Check for missing data as before
                    var hasMissingData = !feature.properties.population || !feature.properties.perCapitaIncome || !feature.properties.area;

                    // Initial style makes counties blend in or be invisible
                    return {
                        weight: 0,
                        color: '#666', // Outline color remains for missing data indication
                        fillColor: hasMissingData ? '#ccc' : '#3388ff', // Use grey for missing data, blue otherwise
                        fillOpacity: 0 // Change here: counties are not highlighted by default
                    };
                },
                onEachFeature: setupCountyInteraction
            }).addTo(map);
        })
        .catch(error => console.error('Error fetching county data:', error));
}



function setupCountyInteraction(feature, layer) {
    var missingDataMessage = "Data not available";
    var popupContent = "<div>Name: " + feature.properties.name + "</div>" +
                       "<div>Population: " + (feature.properties.population || missingDataMessage) + "</div>" +
                       "<div>Area: " + (feature.properties.area || missingDataMessage) + "</div>" +
                       "<div>Per Capita Income: " + (feature.properties.perCapitaIncome || missingDataMessage) + "</div>";
    
    layer.bindPopup(popupContent);

    layer.on({
        mouseover: function(e) {
            var layer = e.target;
            layer.setStyle({
                weight: 0,
                color: '#666', // Keep the outline color on mouseover
                fillColor: '#3388ff', // Highlight color on mouseover
                fillOpacity: 0.7 // Highlight on mouseover
            });
        },
        mouseout: function(e) {
            // Reset to the initial style on mouseout; it automatically considers the missing data styling
            countyLayer.resetStyle(e.target);
        }
    });
}





$(document).ready(function() {
    initializeMap();
    fetchAndDisplayCountyData();
    fetchAndDisplayCategories();
    document.getElementById('startTourButton').addEventListener('click', function() {
        startIntroTour();
    });


    $('#addToContactsBtn').click(function() {
        var table = $('#dataTable').DataTable();
        
        var selectedData = [];
        
        $('#dataTable input[type="checkbox"]:checked').each(function() {
            var rowData = table.row($(this).closest('tr')).data();
            
            // Generate a unique ID using the current time and a random number
            var uniqueId = Date.now() + Math.floor(Math.random() * 100);
    
            selectedData.push({
                id: uniqueId, // Use the generated unique ID
                name: rowData[1], // Adjust indices based on your table structure
                category: rowData[2],
                website: $(rowData[3]).attr('href'), // Extract the href attribute if it's a link
                socials: rowData[4], // This might need parsing depending on your structure
                phone: rowData[5],
                address: rowData[6]
            });
        });
    
        // Now, send the selectedData array to your server
        $.ajax({
            url: '/save-to-contacts',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(selectedData),
            success: function(response) {
                console.log('Contacts saved:', response);
            },
            error: function(xhr, status, error) {
                console.error('Error saving contacts:', error);
            }
        });
    });
    
    

    // Connect to the Socket.IO server.
    // The connection URL has to be updated with your actual server URL
    var socket;
    if (window.location.hostname === "localhost") {
        socket = io.connect('http://localhost:5000');
    } else {
        socket = io.connect('https://iemissary-e39e92466db2.herokuapp.com/');
    }
    
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

//function fetchTempData() {
    // Record the start time
    //const startTime = Date.now();
  //  fetch('/fetch-temp-geojson', {
    //    method: 'GET'
    //})
    //.then(response => {
      //  if (!response.ok) {
        //    return response.json().then(errData => {
          //      throw new Error(`HTTP error! Status: ${response.status}, Message: ${errData.message}`);
            //});
        //}
        //return response.json();
    //})
    //.then(data => {
        

      //  displayDataOnTable(data); // Populate the table with data

        //displayDataOnMap(data); // Handle the data
    //})
    //.catch(error => {
      //  const endTime = Date.now();

        //const elapsedTime = endTime - startTime;
        // log error, and stop interval
        //console.error(`Error: ${error}. Request failed in ${elapsedTime} ms`);


       // if (error.message.includes('404')) { // Assuming 404 means file not found
         //   clearInterval(intervalId);
           // const endTime = Date.now();

            //const elapsedTime = endTime - startTime;
            //document.getElementById('loadingIcon').style.display = 'none';

            //console.log('No more data to fetch, stopping interval. Total Time = ',{elapsedTime});
        //}
    //});
//}

//function fetchSavedData() {
    // Display the loading icon
  //  document.getElementById('loadingIcon').style.display = 'block';

    // Record the start time
    //const startTime = Date.now();

    //fetch('geojson/output.geojson', {
      //  method: 'GET'
        
   // })
   // .then(response => {
     //   if (!response.ok) {
       //     throw new Error(`HTTP error! Status: ${response.status}`);
        //}
        //return response.json();
    //})
    //.then(data => {
      //  displayDataOnTable(data); // Populate the table with data
        // Calculate and log the elapsed time
        //const endTime = Date.now();
        //const elapsedTime = endTime - startTime;
        //console.log(`Request completed in ${elapsedTime} ms`);

        //document.getElementById('loadingIcon').style.display = 'none';
        //displayDataOnMap(data); // Handle the data
    //})
    //.catch(error => {
        // Hide the loading icon and log error and elapsed time
      //  const endTime = Date.now();
        //const elapsedTime = endTime - startTime;
        //console.error(`Error: ${error}. Request failed in ${elapsedTime} ms`);

        //document.getElementById('loadingIcon').style.display = 'none';
    //});
//}

        // Set a delay of 10 seconds before fetching temporary data
        //setTimeout(function() {
        //    console.log('Starting to fetch temporary data...');
        //    startFetchingTempData();
       // }, 2000); // 10000 milliseconds = 10 seconds

       // Function to start the interval for fetchTempData
//function startFetchingTempData() {
//    intervalId = setInterval(fetchTempData, 3000); // Fetch every 5 seconds
//    console.log('interval set')
    
//}