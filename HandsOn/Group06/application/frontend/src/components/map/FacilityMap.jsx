
import { useEffect } from "react";

import PropTypes from "prop-types";

import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
} from "react-leaflet";

import L from "leaflet";

import "./FacilityMap.css";

// Configuración del icono de los marcadores.
const libraryIcon = L.divIcon({
  className: "custom-marker",
  html: '<div class="marker-pin library-marker"></div>',
  iconSize: [20, 20],
  iconAnchor: [10, 10],
  popupAnchor: [0, -10],
});

const selectedLibraryIcon = L.divIcon({
  className: "custom-marker",
  html: '<div class="marker-pin library-marker selected-marker"></div>',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
  popupAnchor: [0, -14],
});

const museumIcon = L.divIcon({
  className: "custom-marker",
  html: '<div class="marker-pin museum-marker"></div>',
  iconSize: [20, 20],
  iconAnchor: [10, 10],
  popupAnchor: [0, -10],
});

const selectedMuseumIcon = L.divIcon({
  className: "custom-marker",
  html: '<div class="marker-pin museum-marker selected-marker"></div>',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
  popupAnchor: [0, -14],
});

const userIcon = L.divIcon({
  className: "custom-marker",
  html: '<div class="marker-pin user-marker"></div>',
  iconSize: [24, 24],
  iconAnchor: [12, 12],
  popupAnchor: [0, -12],
});

// Coordenadas del centro de Madrid.
const MADRID_CENTER = [40.4168, -3.7038];

function MapBounds({ facilities, userLocation }) {
  const map = useMap();

  useEffect(() => {
    const bounds = facilities.map((facility) => [
      facility.location.latitude,
      facility.location.longitude,
    ]);

    // Añadir la ubicación del usuario si existe.
    if (userLocation) {
      bounds.push([
        userLocation.latitude,
        userLocation.longitude,
      ]);
    }

    if (bounds.length > 1) {
      map.fitBounds(bounds, {
        padding: [30, 30],
        maxZoom: 15,
      });
    } else if (bounds.length === 1) {
      map.setView(bounds[0], 15);
    }
  }, [facilities, userLocation, map]);

  return null;
}

function MapLegend() {
  const map = useMap();

  useEffect(() => {
    const legend = L.control({
      position: "bottomright",
    });

    legend.onAdd = () => {
      const div = L.DomUtil.create("div", "map-legend");

      div.innerHTML = `
        <strong>Instalaciones</strong>
        <div class="legend-item">
          <span class="legend-color library-marker"></span>
          <span>Bibliotecas</span>
        </div>
        <div class="legend-item">
          <span class="legend-color museum-marker"></span>
          <span>Museos</span>
        </div>
        <div class="legend-item">
          <span class="legend-color user-marker"></span>
          <span>Tu ubicación</span>
        </div>
      `;

      L.DomEvent.disableClickPropagation(div);

      return div;
    };

    legend.addTo(map);

    return () => {
      legend.remove();
    };
  }, [map]);

  return null;
}

export default function FacilityMap({
  facilities,
  userLocation,
  activeFacilityId
}) {
  // Nos quedamos únicamente con instalaciones
  // que tienen coordenadas válidas.
  const locatedFacilities = facilities.filter((facility) => {
    const latitude = facility.location?.latitude;
    const longitude = facility.location?.longitude;

    return (
      Number.isFinite(latitude) &&
      Number.isFinite(longitude) &&
      latitude >= -90 &&
      latitude <= 90 &&
      longitude >= -180 &&
      longitude <= 180
    );
  });

  return (
    <MapContainer
      center={MADRID_CENTER}
      zoom={12}
      scrollWheelZoom={true}
      className="facility-map"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <MapBounds
        facilities={locatedFacilities}
        userLocation={userLocation}
      />

      <MapLegend />

      {userLocation && (
        <Marker
          position={[
            userLocation.latitude,
            userLocation.longitude,
          ]}
          icon={userIcon}
        >
          <Popup>
            <strong>Tu ubicación</strong>
          </Popup>
        </Marker>
      )}

      {locatedFacilities.map((facility) => {
        const isActive = facility.id === activeFacilityId;

        const icon =
          facility.facility_type === "library"
            ? isActive ? selectedLibraryIcon : libraryIcon
            : isActive ? selectedMuseumIcon : museumIcon;

        return (
          <Marker
            key={facility.id}
            position={[
              facility.location.latitude,
              facility.location.longitude,
            ]}
            icon={icon}
          >
            <Popup>
              <strong>{facility.name}</strong>
            </Popup>
          </Marker>
        );
      })}
    </MapContainer>
  );
}

MapBounds.propTypes = {
  facilities: PropTypes.arrayOf(
    PropTypes.shape({
      location: PropTypes.shape({
        latitude: PropTypes.number.isRequired,
        longitude: PropTypes.number.isRequired,
      }).isRequired,
    })
  ).isRequired,
};

FacilityMap.propTypes = {
  facilities: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      location: PropTypes.shape({
        latitude: PropTypes.number,
        longitude: PropTypes.number,
      }),
    })
  ).isRequired,

  userLocation: PropTypes.shape({
    latitude: PropTypes.number.isRequired,
    longitude: PropTypes.number.isRequired,
  }),

  activeFacilityId: PropTypes.string,
};

MapBounds.propTypes = {
  facilities: PropTypes.array.isRequired,
  userLocation: PropTypes.shape({
    latitude: PropTypes.number.isRequired,
    longitude: PropTypes.number.isRequired,
  }),
};