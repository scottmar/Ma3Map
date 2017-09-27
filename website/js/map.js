	//Create a blank map
	var map = L.map("map",{
		center:[-1.299737, 36.824208],
		zoom: 12,
		scrollWheelZoom: false,
	});


	//<!-- set up some blank layers -->
	var trafficLayer = new L.geoJson();
	var accidentLayer = new L.geoJson();
	var rainLayer = new L.geoJson();
	var otherLayer = new L.geoJson();
	
	trafficLayer.addTo(map);
	accidentLayer.addTo(map);
	rainLayer.addTo(map);
	otherLayer.addTo(map);

	//<!--add slippy map as a base-->
	L.tileLayer('http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
		maxZoom: 19,
		attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>, Tiles courtesy of <a href="http://hot.openstreetmap.org/" target="_blank">Humanitarian OpenStreetMap Team</a>'
	}).addTo(map);

	//<!-- Build the layer selector -->
	var layerControl = {
		"<img src = 'img/traffic.png' height=24>Traffic": trafficLayer,
		"<img src = 'img/accident.png' height=24>Accidents": accidentLayer,
		"<img src = 'img/rain.png' height=24>Rain": rainLayer,
		"<img src = 'img/marker-black.png' height=24>Unmatched": otherLayer
	};
	
	L.control.layers(null, layerControl).addTo(map);
	
	//<!--add JSON data to each layer-->
	$.getJSON("js/tweets.geojson",function(data){
    	L.geoJson(data, {
			onEachFeature: function (feature, layer) {
				layer.bindPopup(feature.properties.text);
			},
			filter: function(feature, layer) {
				return feature.properties.category !== ('traffic'||'accident'||'rain');
			},
			pointToLayer: function (feature, latlng) {
				return L.marker(latlng,{icon: plainIcon});
			}
		}).addTo(otherLayer);
		
		L.geoJson(data, {
			onEachFeature: function (feature, layer) {
            	layer.bindPopup(feature.properties.text);
			},
			filter: function(feature, layer) {
				return feature.properties.category === 'traffic';
			},
			pointToLayer: function (feature, latlng) {
				return L.marker(latlng,{icon: trafficIcon});
			}
        }).addTo(trafficLayer);
		
		L.geoJson(data, {
			onEachFeature: function (feature, layer) {
            	layer.bindPopup(feature.properties.text);
			},
			filter: function(feature, layer) {
				return feature.properties.category === 'accident';
			},
			pointToLayer: function (feature, latlng) {
				return L.marker(latlng,{icon: accidentIcon});
			}
        }).addTo(accidentLayer);
		
		L.geoJson(data, {
			onEachFeature: function (feature, layer) {
				layer.bindPopup(feature.properties.text);
			},
			filter: function(feature, layer) {
				return feature.properties.category === 'rain';
			},
			pointToLayer: function (feature, latlng) {
				return L.marker(latlng,{icon: rainIcon});
			}
		}).addTo(rainLayer);
		

	});
	
	
	//<!-- Add custom markers -->
	var customIcon = L.Icon.extend({
		options:{
			//iconSize: [36,36],
			iconAnchor: [18,18],
			popupAnchor: [0,0]
		}
	});
	
	var customPin = L.Icon.extend({
		options:{
			iconSize: [36,36],
			iconAnchor: [18,36],
			popupAnchor: [0,-18]
		}
	})
	
	var trafficIcon = new customIcon({iconUrl:'img/traffic.png'});
	var accidentIcon = new customIcon({iconUrl:'img/accident.png'});
	var rainIcon = new customIcon({iconUrl:'img/rain.png'});
	var plainIcon = new customPin({iconUrl:'img/marker-black.png'});

	
	//<!-- Add custom locator -->
	map.locate({setView: true, maxZoom: 16});

	function onLocationFound(e) {
		var radius = e.accuracy / 2;
		L.marker(e.latlng).addTo(map)
			.bindPopup("You are here").openPopup();
		L.circle(e.latlng, radius).addTo(map);
	}

	map.on('locationfound', onLocationFound);

	function onLocationError(e) {
		alert(e.message);
	}

	map.on('locationerror', onLocationError);




