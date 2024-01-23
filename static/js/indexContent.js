document.addEventListener('DOMContentLoaded', function () {
    var map = L.map('map').setView([38.497, -90.394], 13);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
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

        var bboxText = `bbox.minx > ${sw.lng.toFixed(7)}\n` +
                       `bbox.maxx < ${ne.lng.toFixed(7)}\n` +
                       `bbox.miny > ${sw.lat.toFixed(7)}\n` +
                       `bbox.maxy < ${ne.lat.toFixed(7)}`;

        var bboxTextElement = document.getElementById('bboxTextElement');
        
        if (!bboxTextElement) {
            console.error('bboxTextElement not found');
            return;
        }
    
        bboxTextElement.value = bboxText;
    }
});
