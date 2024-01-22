let map, circle;
let searchCache = {};
let allResults = new Map(); // To store unique results
let currentRadius = 5000; // Default radius in meters
const MAX_SUBAREA_RADIUS = 20 * 1609.34; // 20 miles in meters
let currentInfowindow = null; // Global variable to track the current info window
let allCircles = [];  // Array to store all circles (subareas)



function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 8,
        center: { lat: 38.5915857, lng: -90.3383463 },
        streetViewControl: false, // Hide Street View control
        fullscreenControl: false, // Hide Full Screen control
        mapTypeControl: false,     // Hide Map/Satellite toggle buttons
        });

    circle = new google.maps.Circle({
        map: map,
        center: map.getCenter(),
        radius: currentRadius,
        fillColor: '#FF0000',
        fillOpacity: 0.35,
        strokeColor: '#FF0000',
        strokeOpacity: 0.8,
        strokeWeight: 2
        
    });

    document.getElementById('distanceSlider').addEventListener('input', function() {
        currentRadius = parseInt(this.value) * 1609.34; // Convert miles to meters
        circle.setRadius(currentRadius);
        updateSearchSettingsCard(currentRadius);
    });
    const testCenters = [{ lat: -34.397, lng: 150.644 }, /* more centers */];
}

function createKeyFromCoordinates(lat, lng) {
    return `${lat.toFixed(5)}_${lng.toFixed(5)}`;
}

function searchSubArea(center, keyword) {
    var service = new google.maps.places.PlacesService(map);
    service.nearbySearch({
        location: center,
        radius: currentRadius,
        keyword: keyword
    }, function(results, status) {
        if (status === google.maps.places.PlacesServiceStatus.OK) {
            console.log("API Results:", results);

            results.forEach(place => {
                const key = createKeyFromCoordinates(place.geometry.location.lat(), place.geometry.location.lng());
                if (!allResults.has(key)) {
                    allResults.set(key, {});
                    fetchPlaceDetails(place.place_id); // Fetch details and then create markers
                }
            });
        } else {
            console.error('Places Service failed due to: ' + status);
        }
    });
}



document.getElementById('searchButton').addEventListener('click', function() {
    clearMap(); // Clear existing markers and circles
    // Collect selected common keywords
    var selectedKeywords = Array.from(document.getElementById('exampleFormControlSelect2').selectedOptions)
                                .map(option => option.value);

    // Collect custom keywords and split them by commas
    var customKeywords = document.getElementById('exampleFormControlTextarea1').value.split(',');

    // Combine both lists of keywords, trimming any whitespace
    var allKeywords = selectedKeywords.concat(customKeywords).map(keyword => keyword.trim());

    // Get the current center for subarea calculation and validate it
    let center = map.getCenter();
    console.log("Center:", center); // Log the center object

    if (!center || typeof center.lat !== 'function' || typeof center.lng !== 'function') {
        console.error('Invalid center:', center);
        return; // Stop execution if center is invalid
    }

    let bounds = getBounds(center, currentRadius);
    if (!bounds) {
        console.error('Bounds calculation failed.');
        return; // Stop execution if bounds are null
    }

    // Pass the original center to calculateSubAreaCenters
    let subAreaCenters = calculateSubAreaCenters(bounds, MAX_SUBAREA_RADIUS, center);

    // Draw and search each subarea
    drawSubAreas(map, subAreaCenters, MAX_SUBAREA_RADIUS);
    subAreaCenters.forEach(subCenter => {
        allKeywords.forEach(keyword => {
            if (keyword !== '') {
                searchSubArea(subCenter, keyword, MAX_SUBAREA_RADIUS);
            }
        });
    });
});


document.getElementById('saveResultsButton').addEventListener('click', function() {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/save-places", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            console.log('Results saved successfully');
            console.log('Simplified data', simplifiedData);
            console.log('AllResults', Array.from(allResults.values()));
        }
    };

    // Simplify data before sending
    const simplifiedData = Array.from(allResults.values()).map(placeData => {
        if (placeData.details && placeData.details.geometry && placeData.details.geometry.location) {
            // Extract latitude and longitude
            const lat = placeData.details.geometry.location.lat();
            const lng = placeData.details.geometry.location.lng();

            // Prepare the data object with formatted_address
            return {
                name: placeData.details.name, // Adjust according to the actual property path
                coordinates: lat + ', ' + lng,
                website: placeData.details.website, // Adjust according to the actual property path
                formatted_address: placeData.details.formatted_address // Adding formatted_address
            };
        } else {
            // Return null or default object if details do not exist
            return null;
        }
    }).filter(item => item !== null); // Filter out null values

    xhr.send(JSON.stringify(simplifiedData));
});

document.getElementById('locationSubmit').addEventListener('click', function(event) {
    event.preventDefault();
    geocodeLocation();
});

// Adding keypress event listener to 'locationInput' field
document.getElementById('locationInput').addEventListener('keypress', function(event) {
    // Check if the key pressed is the Enter key
    if (event.key === "Enter") {
        event.preventDefault(); // Prevent the default action for Enter key
        geocodeLocation();
    }
});

document.getElementById('distanceSlider').addEventListener('input', function() {
    var distanceValue = this.value; // Get the current value of the slider
    updateCircleRadius(distanceValue); // Update the circle radius
});

function geocodeLocation() {
    var location = document.getElementById('locationInput').value;
    var geocoder = new google.maps.Geocoder();

    geocoder.geocode({ 'address': location }, function(results, status) {
        if (status === 'OK') {
            var newCenter = results[0].geometry.location;
            map.setCenter(newCenter);
            circle.setCenter(newCenter);
            updateCircleRadius(document.getElementById('distanceSlider').value);
        } else {
            alert('Geocode was not successful for the following reason: ' + status);
        }
    });
}

function updateCircleRadius(distance) {
    circle.setRadius(parseInt(distance) * 1609.34);
}

function fetchPlaces(map, center, radius, keyword, cacheKey) {
    var service = new google.maps.places.PlacesService(map);
    service.nearbySearch({
        location: center,
        radius: currentRadius,
        keyword: keyword
    }, function(results, status) {
        if (status === google.maps.places.PlacesServiceStatus.OK) {
            searchCache[cacheKey] = results;
            processResults(results, status);
        } else {
            console.error('Places Service failed due to: ' + status);
        }
    });
}


function processResults(results, status) {
    if (status === google.maps.places.PlacesServiceStatus.OK) {
        document.getElementById('searchResultsCount').textContent = results.length;
        results.forEach(result => {
            // Only fetch details for operational businesses
            if (result.business_status === "OPERATIONAL") {
                fetchPlaceDetails(result.place_id);
            }
        });
    } else {
        document.getElementById('searchResultsCount').textContent = '0';
    }
}



function fetchPlaceDetails(placeId) {
    var service = new google.maps.places.PlacesService(map);
    service.getDetails({ placeId: placeId }, function(place, status) {
        if (status === google.maps.places.PlacesServiceStatus.OK) {
            console.log("Detailed Place Data:", place);
            
            if (place.website && place.business_status === "OPERATIONAL") {
                updateResultsWithDetails(place);
            }
        } else {
            console.error('Failed to fetch place details:', status);
        }
    });
}

function updateResultsWithDetails(place) {
    const key = createKeyFromCoordinates(place.geometry.location.lat(), place.geometry.location.lng());

    if (allResults.has(key)) {
        let placeData = allResults.get(key);

        // Check if a marker already exists for this place
        if (!placeData.marker) {
            var marker = new google.maps.Marker({
                map: map,
                position: place.geometry.location,
                title: place.name
            });

            var infowindow = new google.maps.InfoWindow({
                content: `<div><strong>${place.name}</strong><br>` + 
                         `<a href="${place.website}" target="_blank">${place.website}</a></div>`
            });

            marker.addListener('click', function() {
                if (currentInfowindow && currentInfowindow !== infowindow) {
                    currentInfowindow.close();
                }
                infowindow.open(map, this);
                currentInfowindow = infowindow;
            });

            placeData.marker = marker;
        }

        placeData.details = place;
    }
}







function getPlaceDetails(placeId, infowindow) {
    var service = new google.maps.places.PlacesService(map);
    service.getDetails({ placeId: placeId }, function(place, status) {
        if (status === google.maps.places.PlacesServiceStatus.OK) {
            var contentString = `<div><strong>${place.name}</strong><br>` +
                                `<a href="${place.website}" target="_blank">${place.website}</a></div>`;
            infowindow.setContent(contentString);
        }
    });
}

function performPlaceSearch(keywords) {
    let center = map.getCenter();
    let radius = currentRadius; // Radius in meters from the distanceSlider

    // Ensure there is a center and radius defined
    if (!center || radius <= 0) {
        console.log("Search center or radius is not set");
        return;
    }

    // Calculate bounds
    let bounds = getBounds(center, radius);

    // Generate sub-area centers
    let subAreaCenters = calculateSubAreaCenters(bounds.northeast, bounds.southwest, radius, center);

    // Perform search for each sub-area
    subAreaCenters.forEach(subCenter => {
        keywords.forEach(keyword => {
            if (keyword !== '') {
                searchSubArea(subCenter, keyword);
            }
        });
    });
}

function updateSearchSettingsCard(radius) {
    document.getElementById('currentRadiusDisplay').textContent = `${(radius / 1609.34).toFixed(0)}`;
}

function calculateSubAreaCenters(bounds, subAreaRadius, originalCenter) {
    let centers = [];

    // Keep the original step size
    let radiusInDegreesLat = (subAreaRadius / 111320) * 1.4;
    let avgLat = (bounds.northeast.lat + bounds.southwest.lat) / 2;
    let radiusInDegreesLng = (subAreaRadius / (111320 * Math.cos(avgLat * (Math.PI / 180)))) * 1.4;

    console.log("Calculating subarea centers with bounds:", bounds, "and subAreaRadius:", subAreaRadius);

    for (let lat = bounds.southwest.lat; lat <= bounds.northeast.lat; lat += radiusInDegreesLat) {
        for (let lng = bounds.southwest.lng; lng <= bounds.northeast.lng; lng += radiusInDegreesLng) {
            let point = new google.maps.LatLng(lat, lng);
            let distanceToCenter = google.maps.geometry.spherical.computeDistanceBetween(point, originalCenter);


            // Include point if within the circular search area
            if (distanceToCenter <= currentRadius) {
                centers.push(point);
            } else {
            }
        }
    }

    return centers;
}







function calculateLngStep(radius, latitude) {
    // Calculate degrees per longitude based on the radius and latitude
    let metersPerLngDegree = 111320 * Math.cos(latitude * (Math.PI / 180));
    return radius / metersPerLngDegree;
}
function getBounds(center, radius) {
    let north = google.maps.geometry.spherical.computeOffset(center, radius, 0).lat();
    let south = google.maps.geometry.spherical.computeOffset(center, radius, 180).lat();
    let east = google.maps.geometry.spherical.computeOffset(center, radius, 90).lng();
    let west = google.maps.geometry.spherical.computeOffset(center, radius, 270).lng();

    return {
        northeast: { lat: north, lng: east },
        southwest: { lat: south, lng: west }
    };
}


function performLargeAreaSearch() {
    let center = map.getCenter();
    let radius = currentRadius; // Radius in meters from the distanceSlider

    // Calculate bounds
    let bounds = getBounds(center, radius);

    // Generate sub-area centers
    let subAreaCenters = calculateSubAreaCenters(bounds.northeast, bounds.southwest, radius, center);

    // Perform search for each sub-area
    subAreaCenters.forEach(center => searchSubArea(center));
}
function calculateLatStep(radius) {
    // Approximate degrees per latitude based on the radius
    return (radius / 111320); // 111,320 meters is approx. distance of 1 degree of latitude
}

function drawSubAreas(map, centers, radius) {
    // Clear existing circles before drawing new ones
    allCircles.forEach(circle => circle.setMap(null));
    allCircles = [];

    console.log("Map instance in drawSubAreas:", map); 
    console.log("Drawing circles on map with centers:", centers, "with radius:", radius);

    centers.forEach(center => {
        let cityCircle = new google.maps.Circle({
            strokeColor: "#FFFF00",
            strokeOpacity: 0.8,
            strokeWeight: 2,
            fillColor: "#FFFF00",
            fillOpacity: 0.5,
            map: map,
            center: center,
            radius: radius
        });

        allCircles.push(cityCircle);
    });
}


function clearMap() {
    allResults.forEach(placeData => {
        if (placeData.marker) {
            placeData.marker.setMap(null);
        }
    });
    allResults.clear();

    allCircles.forEach(circle => circle.setMap(null));
    allCircles = [];
}


google.maps.event.addDomListener(window, 'load', initMap);