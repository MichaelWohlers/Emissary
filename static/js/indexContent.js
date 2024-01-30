var map; // Declare map globally
var markerLayerGroup; // Declare the layer group globally
var markers;
// Map initialization
function initializeMap() {
    map = L.map('map').setView([38.497, -90.394], 8);
    markerLayerGroup = L.layerGroup().addTo(map);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap/OvertureMaps'
    }).addTo(map);

    var drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

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

    map.on('draw:created', function (event) {
        drawnItems.clearLayers(); // Clear any existing layers
        var layer = event.layer;
        drawnItems.addLayer(layer); // Add the new layer
        updateBboxText(layer); // Update bbox text
    });

    map.on('draw:edited', function (event) {
        var layers = event.layers;
        layers.eachLayer(function (layer) {
            if (layer instanceof L.Rectangle) {
                updateBboxText(layer);
            }
        });
    });

    var geocoder = L.Control.geocoder({
        defaultMarkGeocode: false
    }).on('markgeocode', function(e) {
        var center = e.geocode.center;
        var bounds = L.latLngBounds([
            [center.lat - 0.05, center.lng - 0.05],
            [center.lat + 0.05, center.lng + 0.05]
        ]);

        drawnItems.clearLayers(); // Clear existing layers
        var layer = L.rectangle(bounds, {color: 'blue'}).addTo(drawnItems);
        updateBboxText(layer);
        map.fitBounds(bounds);
    }).addTo(map);

    function updateBboxText(layer) {
        var bounds = layer.getBounds();
        var sw = bounds.getSouthWest();
        var ne = bounds.getNorthEast();
    
        // Format as "minx,miny,maxx,maxy"
        var bboxText = `${sw.lng.toFixed(7)},${sw.lat.toFixed(7)},${ne.lng.toFixed(7)},${ne.lat.toFixed(7)}`;
    
        var bboxTextElement = document.getElementById('bboxTextElement');
        
        if (!bboxTextElement) {
            console.error('bboxTextElement not found');
            return;
        }
    
        bboxTextElement.value = bboxText;
    }
}
function displayDataOnMap(geojsonData) {
    if (!map) {
        console.error('Map not initialized');
        return;
    }
    markerLayerGroup.clearLayers();
    var markers = L.markerClusterGroup();


    L.geoJSON(geojsonData, {
        pointToLayer: function(feature, latlng) {
            return L.marker(latlng);
        },
        onEachFeature: function(feature, layer) {
            if (feature.properties) {
                var popupContent = '<div style="font-family: Arial, sans-serif; color: #333;">' +
                                   '<h2 style="color: #007bff; margin-bottom: 5px;">' + (feature.properties.names?.common[0]?.value || 'N/A') + '</h2>' +
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
                    var addressString = [address.freeform, address.locality, address.region, address.postcode].filter(Boolean).join(', ');
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
    }).addTo(markers);
    markers.addTo(markerLayerGroup);
}


        





document.addEventListener('DOMContentLoaded', function () {
    initializeMap();
    setTimeout(function() {
        map.invalidateSize();
    }, 1); // A brief timeout can ensure the DOM elements are fully rendered
    $(document).ready(function() {
        var table = $('#dataTable').DataTable({
            "responsive": true,
            "paging": true,
            "searching": true,
            "order": [[1, "asc"]], // Order by second column initially
            "columnDefs": [
                { "orderable": false, "targets": [0, 7] } // Disable ordering for column 1 & 8
            ]
        });
    
        // Handle click on "Select all" control
        $('#select-all').on('click', function(){
            var rows = table.rows({ 'search': 'applied' }).nodes();
            $('input[type="checkbox"]', rows).prop('checked', this.checked);
        });
    
        // Handle click on checkbox to set state of "Select all" control
        $('#dataTable tbody').on('change', 'input[type="checkbox"]', function(){
            if(!this.checked){
                var el = $('#select-all').get(0);
                if(el && el.checked && ('indeterminate' in el)){
                    el.indeterminate = true;
                }
            }
        });
    
    function fetchData(queryData) {
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

    
        // Example: Call displayDataOnTable with sample data
        // displayDataOnTable(yourData); // Uncomment and replace 'yourData' with your actual data variable
    });
    

    // Fetch categories from the Flask server
    fetch('/get_categories')
    .then(response => response.json())
    .then(data => {
        var categoryList = document.getElementById('categoryList');

        // Sort categories alphabetically
        var sortedCategories = data.categories.sort();

        sortedCategories.forEach(function(category) {
            var label = document.createElement('label');
            var checkbox = document.createElement('input');
            label.style.whiteSpace = 'nowrap'; // Apply white-space: nowrap; using style
            label.style.display = 'block'; // Apply white-space: nowrap; using style

            checkbox.type = 'checkbox';
            checkbox.name = 'categories[]'; // Use an array name for multiple selections
            checkbox.value = category;
            checkbox.classList.add('ml-2'); // Add margin class to checkbox

            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(category.replace(/_/g, ' ').toUpperCase()));
            categoryList.appendChild(label);
        });

        // Attach an event listener to the categoryList for changes
        categoryList.addEventListener('change', function(event) {
            fetchKeywords(); // Fetch keywords when categories change
        });
    })
    .catch(error => console.error('Error fetching categories:', error));
    // Add search functionality
    document.getElementById('searchInput').addEventListener('input', filterCategories);

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

    // Function to fetch keywords
    function fetchKeywords() {
        // Get selected categories
        var selectedCategories = Array.from(categoryList.querySelectorAll('input[type="checkbox"]:checked'))
            .map(checkbox => checkbox.value)
            .sort(); // Sort categories alphabetically

        // Fetch keywords based on selected categories
        fetch('/get_keywords', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ categories: selectedCategories })
        })
        .then(response => response.json())
        .then(data => {
            var keywordItems = document.getElementById('keywordItems');
            keywordItems.innerHTML = ''; // Clear existing keywords

            // Sort keywords alphabetically
            var sortedKeywords = data.keywords.sort();

            sortedKeywords.forEach(function(keyword) {
                var label = document.createElement('label');
                label.classList.add('checkbox-item'); // Class for spacing
                label.style.whiteSpace = 'nowrap';
                label.style.display = 'block';

                var checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.name = 'keywords[]';
                checkbox.value = keyword;
                checkbox.classList.add('ml-2'); // Add margin class to checkbox
                
                label.appendChild(checkbox);
                label.appendChild(document.createTextNode(keyword.replace(/_/g, ' ').toUpperCase()));
                keywordItems.appendChild(label); // Append to keywordItems instead of keywordList
                    });
            
        })
        .catch(error => console.error('Error fetching keywords:', error));
        
    }

    // Handle checkbox selection change for keywords
    var keywordItems = document.getElementById('keywordItems');
    keywordItems.addEventListener('change', function(event) {
        var selectedKeywords = Array.from(keywordItems.querySelectorAll('input[type="checkbox"]:checked'))
            .map(checkbox => checkbox.value)
            .sort(); // Sort selected keywords alphabetically
        console.log('Selected Keywords:', selectedKeywords);
    });

    // Add search functionality for keywords
    document.getElementById('searchKeyword').addEventListener('input', filterKeywords);

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

    document.getElementById('queryForm').addEventListener('submit', function(e) {
        e.preventDefault();
        $(document).ready(function() {
            var table = $('#dataTable').DataTable({
                "responsive": true,
                "paging": true,
                "searching": true,
                "order": [[1, "asc"]], // Order by second column initially
                "columnDefs": [
                    { "orderable": false, "targets": [0, 7] } // Disable ordering for column 1 & 8
                ]
            });
        
            // Handle click on "Select all" control
            $('#select-all').on('click', function(){
                var rows = table.rows({ 'search': 'applied' }).nodes();
                $('input[type="checkbox"]', rows).prop('checked', this.checked);
            });
        
            // Handle click on checkbox to set state of "Select all" control
            $('#dataTable tbody').on('change', 'input[type="checkbox"]', function(){
                if(!this.checked){
                    var el = $('#select-all').get(0);
                    if(el && el.checked && ('indeterminate' in el)){
                        el.indeterminate = true;
                    }
                }
            });
        
            // Function to update table data
            function displayDataOnTable(data) {
                table.clear(); // Clear existing data in DataTable
        
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
        

        // Get user inputs
        // Get selected keywords as an array of checkbox values
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
        console.log('Starting to fetch saved data after 5 seconds...');
        
            // Start the first fetch after 5 seconds
            setTimeout(function() {
                var intervalId = setInterval(fetchTempData, 5000); // Fetch every 5 seconds
        
                function fetchTempData() {
                    // Display the loading icon
        
                    // Record the start time
                    const startTime = Date.now();
                    fetch('/fetch-temp-geojson', {
                        method: 'GET'
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! Status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        const endTime = Date.now();

                        const elapsedTime = endTime - startTime;

                        displayDataOnTable(data); // Populate the table with data

                        displayDataOnMap(data); // Handle the data
                    })
                    .catch(error => {
                        const endTime = Date.now();

                        const elapsedTime = endTime - startTime;
                        // Hide the loading icon, log error, and stop interval
                        console.error(`Error: ${error}. Request failed in ${elapsedTime} ms`);
        
        
                        if (error.message.includes('404')) { // Assuming 404 means file not found
                            clearInterval(intervalId);
                            console.log('No more data to fetch, stopping interval.');
                        }
                    });
                }
            }, 5000); // 5-second delay before first fetch
        });
        


        
    document.getElementById('loadplaces').addEventListener('click', function(e) {
        console.log('fetching saved data')
        fetchSavedData();
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
       

        
    });
    document.getElementById('searchInput').addEventListener('input', filterCategories);
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
    document.getElementById('searchKeyword').addEventListener('input', filterKeywords);

    document.getElementById('mapTableToggle').addEventListener('change', function() {
        var map = document.getElementById('map');
        var tableView = document.getElementById('tableView');
    
        if (this.checked) {
            map.style.display = 'none';
            tableView.style.display = 'block';
            // Populate and display the table here
        } else {
            map.style.display = 'block';
            tableView.style.display = 'none';
        }
    });
    
})
