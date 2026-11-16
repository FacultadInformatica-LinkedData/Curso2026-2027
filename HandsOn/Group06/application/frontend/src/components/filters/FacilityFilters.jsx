
import PropTypes from "prop-types";

import "./FacilityFilters.css";

export default function FacilityFilters({
  filters,
  onFilterChange,
  districts,
  neighborhoods,
  userLocation,
  locationError,
  handleToggleLocation,
  isOpen,
  onToggle,
}) {

  function handleFeatureChange(event) {
    const { value, checked } = event.target;

    const currentFeatures = filters.accessibility_features;

    const updatedFeatures = checked
      ? [...currentFeatures, value]
      : currentFeatures.filter((feature) => feature !== value);

    onFilterChange("accessibility_features", updatedFeatures);
  }

  function handleStatusChange(event) {
    const value = event.target.value;

    onFilterChange(
      "accessibility_status",
      value ? value.split(",") : []
    );

    if (!value) {
      onFilterChange("accessibility_features", []);
    }
  }

  return (
    <section className="facility-filters">
      <button
        type="button"
        className="filters-toggle"
        onClick={onToggle}
        aria-expanded={isOpen}
      >
        <span>Filtros</span>
        <span>{isOpen ? "▲" : "▼"}</span>
      </button>

      {isOpen && (
        <div className="filters-content">
          {/* Búsqueda por cercanía */}
          <div className="filter-group">
            <p>Instalaciones cercanas</p>

            <button
              type="button"
              className={`location-toggle ${
                filters.latitude != null && filters.longitude != null
                  ? "active"
                  : ""
              }`}
              onClick={handleToggleLocation}
              aria-pressed={
                filters.latitude != null && filters.longitude != null
              }
            >
              <span className="toggle-indicator"></span>
              Usar mi ubicación
            </button>

            {userLocation && (
              <p>Ubicación activada.</p>
            )}

            {locationError && (
              <p className="error-message">{locationError}</p>
            )}

            <label htmlFor="radius">Radio de búsqueda</label>

            <select
              id="radius"
              value={filters.radius}
              onChange={(event) =>
                onFilterChange("radius", Number(event.target.value))
              }
            >
              <option value={0.5}>500 metros</option>
              <option value={1}>1 km</option>
              <option value={2}>2 km</option>
              <option value={5}>5 km</option>
            </select>
          </div>

          {/* Filtro por distrito */}
          <div className="filter-group">
            <label htmlFor="district">
              Distrito
            </label>

            <select
              id="district"
              value={filters.district}
              onChange={(event) =>
                onFilterChange("district", event.target.value)
              }
            >
              <option value="">Todos los distritos</option>

              {districts.map((district) => (
                <option key={district.uri} value={district.uri}>
                  {district.name}
                </option>
              ))}
            </select>
          </div>

          {/* Filtro por barrio */}
          <div className="filter-group">
            <label htmlFor="neighborhood">
              Barrio
            </label>

            <select
              id="neighborhood"
              value={filters.neighborhood}
              onChange={(event) =>
                onFilterChange("neighborhood", event.target.value)
              }
            >
              <option value="">Todos los barrios</option>

              {neighborhoods.map((neighborhood) => (
                <option key={neighborhood.uri} value={neighborhood.uri}>
                  {neighborhood.name}
                </option>
              ))}
            </select>
          </div>

          {/* Tipo de instalación */}
          <div className="filter-group">
            <label htmlFor="facility-type">
              Tipo de instalación
            </label>

            <select
              id="facility-type"
              value={filters.facility_types[0] ?? ""}
              onChange={(event) =>
                onFilterChange(
                  "facility_types",
                  event.target.value ? [event.target.value] : []
                )
              }
            >
              <option value="">Todas</option>
              <option value="library">Bibliotecas</option>
              <option value="museum">Museos</option>
            </select>
          </div>

          {/* Estado de accesibilidad */}
          <div className="filter-group">
            <label htmlFor="accessibility-status">
              Estado de accesibilidad
            </label>

            <select
              id="accessibility-status"
              value={filters.accessibility_status.join(",")}
              onChange={handleStatusChange}
            >
              <option value="">Cualquier estado</option>
              <option value="accessible">Accesible</option>
              <option value="partial">Parcialmente accesible</option>
              <option value="accessible,partial"> Accesible y parcialmente accesible</option>
            </select>
          </div>

          {/* Características de accesibilidad */}
          {filters.accessibility_status.length > 0 && (
            <div className="filter-group">
              <p>Características de accesibilidad</p>

              <label>
                <input
                  type="checkbox"
                  value="sign_language"
                  checked={filters.accessibility_features.includes("sign_language")}
                  onChange={handleFeatureChange}
                />
                Señalización en lengua de signos
              </label>

              <label>
                <input
                  type="checkbox"
                  value="tactile_paving"
                  checked={filters.accessibility_features.includes("tactile_paving")}
                  onChange={handleFeatureChange}
                />
                Pavimento podotáctil
              </label>

              <label>
                <input
                  type="checkbox"
                  value="magnetic_induction_loop"
                  checked={filters.accessibility_features.includes(
                    "magnetic_induction_loop"
                  )}
                  onChange={handleFeatureChange}
                />
                Bucle de inducción magnética
              </label>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

FacilityFilters.propTypes = {
  filters: PropTypes.shape({
    facility_types: PropTypes.arrayOf(
      PropTypes.oneOf(["library", "museum"])
    ).isRequired,

    accessibility_status: PropTypes.arrayOf(
      PropTypes.oneOf(["accessible", "partial"])
    ).isRequired,

    accessibility_features: PropTypes.arrayOf(
      PropTypes.oneOf([
        "sign_language",
        "tactile_paving",
        "magnetic_induction_loop",
      ])
    ).isRequired,

    district: PropTypes.string.isRequired,
    neighborhood: PropTypes.string.isRequired,

      latitude: PropTypes.number,
    longitude: PropTypes.number,
    radius: PropTypes.oneOf([0.5, 1, 2, 5]).isRequired
  }).isRequired,

  districts: PropTypes.arrayOf(
    PropTypes.shape({
      uri: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
    })
  ).isRequired,

  neighborhoods: PropTypes.arrayOf(
    PropTypes.shape({
      uri: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
    })
  ).isRequired,

  userLocation: PropTypes.shape({
    latitude: PropTypes.oneOfType([PropTypes.number, PropTypes.oneOf([null])]),
    longitude: PropTypes.oneOfType([PropTypes.number, PropTypes.oneOf([null])])
  }),

  locationError: PropTypes.string,

  handleToggleLocation: PropTypes.func.isRequired,

  onFilterChange: PropTypes.func.isRequired,

  isOpen: PropTypes.bool.isRequired,
  onToggle: PropTypes.func.isRequired,
};