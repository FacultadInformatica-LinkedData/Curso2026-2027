
import PropTypes from "prop-types";

export default function FacilityExternalInfo({ facility }) {
  return (
    <section className="detail-section">
      <h2>Información externa</h2>

      <div className="detail-grid">
        <div className="detail-info-item">
          <span className="detail-label">Página oficial</span>

          {facility.publisher_url ? (
            <a
              href={facility.publisher_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Visitar la página
            </a>
          ) : (
            <span>No hay información</span>
          )}
        </div>
      </div>
    </section>
  );
}

FacilityExternalInfo.propTypes = {
  facility: PropTypes.object.isRequired,
};
