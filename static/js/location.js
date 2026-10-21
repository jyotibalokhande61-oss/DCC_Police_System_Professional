(() => {
  const button = document.getElementById("locate-btn");
  const status = document.getElementById("location-status");
  const latInput = document.getElementById("latitude");
  const lonInput = document.getElementById("longitude");
  const mapElement = document.getElementById("map");
  if (!button || !status || !latInput || !lonInput) return;

  let map = null;
  let marker = null;

  if (mapElement && window.L) {
    map = L.map("map").setView([20.5937, 78.9629], 4);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);
    map.on("click", (event) => setLocation(event.latlng.lat, event.latlng.lng, "Map pin selected."));
  } else if (mapElement) {
    mapElement.innerHTML = '<div class="map-fallback">Map tiles could not load. You can still use the location button or enter a location description.</div>';
  }

  function setLocation(lat, lon, message) {
    latInput.value = Number(lat).toFixed(6);
    lonInput.value = Number(lon).toFixed(6);
    status.textContent = message;
    status.classList.add("location-success");
    if (map) {
      const point = [Number(lat), Number(lon)];
      map.setView(point, 15);
      if (marker) marker.setLatLng(point);
      else marker = L.marker(point, {draggable: true}).addTo(map);
      marker.bindPopup("Selected report location").openPopup();
      marker.on("dragend", (event) => {
        const p = event.target.getLatLng();
        latInput.value = p.lat.toFixed(6);
        lonInput.value = p.lng.toFixed(6);
        status.textContent = "Map pin adjusted. Coordinates will be attached if you submit.";
      });
    }
  }

  button.addEventListener("click", () => {
    if (!navigator.geolocation) {
      status.textContent = "This browser does not support location. Enter the location description manually.";
      return;
    }
    button.disabled = true;
    status.textContent = "Requesting permission and checking device location…";
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation(position.coords.latitude, position.coords.longitude, "Location selected. It will be attached only if you submit this complaint.");
        button.disabled = false;
      },
      (error) => {
        const messages = {
          1: "Permission denied. You can enter the location description manually.",
          2: "Location unavailable. Try again or enter the location manually.",
          3: "Location request timed out. Please try again."
        };
        status.textContent = messages[error.code] || "Unable to get location. You can enter it manually.";
        button.disabled = false;
      },
      {enableHighAccuracy: true, timeout: 12000, maximumAge: 60000}
    );
  });
})();
