
import PropTypes from "prop-types";
import InfoItem from "./InfoItem";

export default function FacilityLocation({ facility }) {
  return (
    <section className="detail-section">
      <h2>Localización</h2>

      <div className="detail-grid detail-grid-two-columns">
        <InfoItem label="Dirección" value={facility.address.street} />
        <InfoItem label="Distrito" value={facility.address.district.name} />
        <InfoItem label="Código postal" value={facility.address.postal_code} />
        <InfoItem label="Barrio" value={facility.address.neighborhood.name} />
      </div>
    </section>
  );
}

FacilityLocation.propTypes = {
  facility: PropTypes.object.isRequired,
};
