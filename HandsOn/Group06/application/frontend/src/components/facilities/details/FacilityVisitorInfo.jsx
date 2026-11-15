
import PropTypes from "prop-types";
import InfoItem from "./InfoItem";

export default function FacilityVisitorInfo({ facility }) {
  return (
    <section className="detail-section">
      <h2>Información para visitas</h2>

      <div className="detail-grid">
        <InfoItem
          label="Horario"
          value={facility.opening_hours?.replace(/\.\s*/g, ".\n\n")}
        />
        <InfoItem 
          label="Transporte" 
          value={facility.transport?.replace(/\.\s*/g, ".\n\n")} 
        />
      </div>
    </section>
  );
}

FacilityVisitorInfo.propTypes = {
  facility: PropTypes.object.isRequired,
};
