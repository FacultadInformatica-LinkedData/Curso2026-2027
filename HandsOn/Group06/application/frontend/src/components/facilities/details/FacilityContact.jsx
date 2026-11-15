
import PropTypes from "prop-types";
import InfoItem from "./InfoItem";

export default function FacilityContact({ facility }) {
  return (
    <section className="detail-section">
      <h2>Contacto</h2>

      <div className="detail-grid detail-grid-two-columns">
        <InfoItem label="Telefono" value={facility.contact.telephone} />
        <InfoItem label="Email" value={facility.contact.email} />
      </div>
    </section>
  );
}

FacilityContact.propTypes = {
  facility: PropTypes.object.isRequired,
};
