const API_URL = "http://127.0.0.1:8000/api";

/**
 * Obtiene las instalaciones aplicando los filtros indicados.
 */
export async function getFacilities(filters = {}) {
    const params = new URLSearchParams();

    if (filters.query) {
        params.set("query", filters.query);
    }

    if (filters.facility_types) {
        filters.facility_types.forEach((type) => {
            params.append("facility_types", type);
        });
    }

    if (filters.district) {
        params.set("district", filters.district);
    }

    if (filters.neighborhood) {
        params.set("neighborhood", filters.neighborhood);
    }

    if (filters.accessibility_status) {
        filters.accessibility_status.forEach((status) => {
            params.append("accessibility_status", status);
        });
    }

    if (filters.accessibility_features) {
        filters.accessibility_features.forEach((feature) => {
            params.append("accessibility_features", feature);
        });
    }

    if (filters.latitude != null && filters.longitude != null) {
        params.set("latitude", String(filters.latitude));
        params.set("longitude", String(filters.longitude));
        params.set("radius", String(filters.radius ?? 1));
    }

    const response = await fetch(
        `${API_URL}/facilities?${params.toString()}`
    );

    if (!response.ok) {
        throw new Error("No se han podido obtener las instalaciones.");
    }

    return response.json();
}

/**
 * Obtiene los detalles de una instalación.
 */
export async function getFacilityDetail(facilityId) {
    const response = await fetch(
        `${API_URL}/facilities/${facilityId}`
    );

    if (!response.ok) {
        if (response.status === 404) {
            throw new Error("No se ha encontrado la instalación.");
        }

        throw new Error("No se han podido obtener los detalles.");
    }

    return response.json();
}
