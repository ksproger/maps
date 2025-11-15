const socket = io();
const uid = document.cookie.split('; ').find(row => row.startsWith('uid=')).split('=')[1];

const map = L.map("map").setView([0,0], 2);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(map);

let marker = null;

function sendPosition() {
    navigator.geolocation.getCurrentPosition(pos => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;

        if (!marker) {
            marker = L.marker([lat, lon]).addTo(map).bindPopup("Вы здесь");
            map.setView([lat, lon], 16);
        } else {
            marker.setLatLng([lat, lon]);
        }

        socket.emit("coords", { uid, lat, lon });
    });
}

setInterval(sendPosition, 3000);
sendPosition();
