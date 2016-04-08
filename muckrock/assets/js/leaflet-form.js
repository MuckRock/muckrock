$(window).on('map:init', function (e) {
    var detail = e.originalEvent ? e.originalEvent.detail : e.detail;
    var map = detail.map;
    // Add geocoder to the map
    var geocoder_settings = {
        'position': 'topright',
        'collapsed': false,
        'placeholder': 'Address'
        // I am getting better results from the default geocoder than
        // I am getting from the Mapzen geocoder. ¯\_(ツ)_/¯
        // 'geocoder': new L.Control.Geocoder.Mapzen('search-npu9HYc')
    };
    var geocoder = L.Control.geocoder(geocoder_settings).addTo(map);
    // Customize geocoder behavior
    geocoder.markGeocode = function(result) {
        // We want to separate the geocoding control from the marker placement
        // control, so do not add any markers to the map from this control.
        map.panTo(result.center).fitBounds(result.bbox);
    };
});

