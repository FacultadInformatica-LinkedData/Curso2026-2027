
import PropTypes from "prop-types";
import AccessibilityItem from "./AccessibilityItem";

export default function FacilityAccessibility({ facility }) {
  const accessibility = facility.accessibility;

  return (
    <section className="detail-section">
      <h2>Accesibilidad</h2>

      
      {accessibility.no_info_accessibility ? (
        <p className="accessibility-note">
          No hay información sobre accesibilidad disponible.
        </p>
      ) : (
        <>
          <div className="accessibility-status">
            {accessibility.accessible ? (
              <span className="available">Accesible</span>
            ) : accessibility.partially_accessible ? (
              <span className="partially-available">
                Parcialmente accesible
              </span>
            ) : (
              <span className="unavailable">No accesible</span>
            )}
          </div>

          <div className="accessibility-list">
            <AccessibilityItem
              label="Lenguaje de signos"
              available={accessibility.sign_language}
            />

            <AccessibilityItem
              label="Pavimento táctil"
              available={accessibility.tactile_paving}
            />

            <AccessibilityItem
              label="Bucle de inducción magnética"
              available={accessibility.magnetic_induction_loop}
            />
          </div>
        </>
      )}

      
    </section>
  );
}

FacilityAccessibility.propTypes = {
  facility: PropTypes.object.isRequired,
};
