
import PropTypes from "prop-types";
import FacilityCard from "./FacilityCard";
import "./FacilityList.css";

export default function FacilityList({
  facilities,
  activeFacilityId,
  onHoverFacility,
}) {
  return (
    <section className="facility-list">
      {facilities.length === 0 ? (
        <p>No se han encontrado instalaciones.</p>
      ) : (
        facilities.map((facility) => (
          <FacilityCard
            key={facility.id}
            facility={facility}
            isActive={facility.id === activeFacilityId}
            onMouseEnter={() => onHoverFacility(facility.id)}
            onMouseLeave={() => onHoverFacility(null)}
          />
        ))
      )}
    </section>
  );
}

FacilityList.propTypes = {
  facilities: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      facility_type: PropTypes.oneOf(["library", "museum"]).isRequired,
    })
  ).isRequired,
  activeFacilityId: PropTypes.string,
  onHoverFacility: PropTypes.func.isRequired,
};
