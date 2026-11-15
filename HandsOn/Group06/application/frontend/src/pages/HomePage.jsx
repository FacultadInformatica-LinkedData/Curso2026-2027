
import { useEffect, useState } from "react";

import Header from "../components/layout/Header";

import FacilityList from "../components/facilities/FacilityList";

import FacilityMap from "../components/map/FacilityMap";

import FacilityFilters from "../components/filters/FacilityFilters";

import { getFacilities } from "../services/facilityService";

import "./HomePage.css";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [facilities, setFacilities] = useState([]);
  const [allFacilities, setAllFacilities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [locationError, setLocationError] = useState(null);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [hoveredFacilityId, setHoveredFacilityId] = useState(null);

  const activeFacilityId = hoveredFacilityId;

  const [filters, setFilters] = useState({
    facility_types: [],
    accessibility_status: [],
    accessibility_features: [],
    district: "",
    neighborhood: "",
    latitude: null,
    longitude: null,
    radius: 1,
  });
  
  function handleToggleLocation() {
    // Si ya está activada, desactivarla.
    if (filters.latitude != null && filters.longitude != null) {
      setFilters((previousFilters) => ({
        ...previousFilters,
        latitude: null,
        longitude: null,
      }));

      setUserLocation(null);
      setLocationError(null);
      return;
    }

    // Si está desactivada, solicitar la ubicación.
    setLocationError(null);

    if (!navigator.geolocation) {
      setLocationError("Tu navegador no admite la geolocalización.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;

        setFilters((previousFilters) => ({
          ...previousFilters,
          latitude,
          longitude,
        }));

        setUserLocation({ latitude, longitude });
      },
      () => {
        setLocationError("No se ha podido obtener tu ubicación.");
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 0,
      }
    );
  }

  async function handleSearch(event) {
    event.preventDefault();

    setFiltersOpen(false); // Cerrar ventana filtros

    setLoading(true);
    setError(null);

    try {
      const data = await getFacilities({
        query,
        ...filters,
      });

      setFacilities(data);
    } catch (err) {
      setError("No se pudieron obtener las instalaciones: " + err);
    } finally {
      setLoading(false);
    }
  }

  function handleFilterChange(filterName, newValue) {
    setFilters((previousFilters) => ({
      ...previousFilters,
      [filterName]: newValue,
    }));
  }

  // Ejecuta este código al iniciar la página
  useEffect(() => {
    async function loadFacilities() {
      setLoading(true);
      setError(null);

      try {
        const data = await getFacilities();
        setFacilities(data);
        setAllFacilities(data)
      } catch (err) {
        setError("No se pudieron obtener las instalaciones: " + err);
      } finally {
        setLoading(false);
      }
    }

    loadFacilities();
  }, []);

  const districts = [
    ...new Map(
      allFacilities.map((facility) => [
        facility.district.uri,
        facility.district,
      ])
    ).values(),
  ].sort((a, b) => a.name.localeCompare(b.name, "es"));

  const neighborhoods = [
    ...new Map(
      allFacilities.map((facility) => [
        facility.neighborhood.uri,
        facility.neighborhood,
      ])
    ).values(),
  ].sort((a, b) => a.name.localeCompare(b.name, "es"));

  return (
    <div className="app-layout">
      <Header />

      <main className="home-page">
        <section className="hero">
          <form className="search-container" onSubmit={handleSearch}>
            <input
              type="text"
              placeholder="Buscar bibliotecas y museos..."
              aria-label="Buscar bibliotecas y museos"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <button type="submit" disabled={loading}>
              {loading ? "Buscando..." : "Buscar"}
            </button>
          </form>

          <FacilityFilters
            filters={filters}
            onFilterChange={handleFilterChange}
            districts={districts}
            neighborhoods={neighborhoods}
            userLocation={userLocation}
            locationError={locationError}
            handleToggleLocation={handleToggleLocation}
            isOpen={filtersOpen}
            onToggle={() => setFiltersOpen((previous) => !previous)}
          />
        </section>

        <section className="results-section">
          {error && <p>{error}</p>}

          {!loading && !error && (
                <>
                  <div className="content-layout">
                    <div className="results-container">
                      <FacilityList
                        facilities={facilities}
                        activeFacilityId={activeFacilityId}
                        onHoverFacility={setHoveredFacilityId}
                      />
                    </div>

                    <div className="map-container">
                      <FacilityMap
                        facilities={facilities}
                        userLocation={userLocation}
                        activeFacilityId={activeFacilityId}
                      />
                    </div>
                  </div>
                </>
          )}
        </section>
      </main>
    </div>
  );
}
