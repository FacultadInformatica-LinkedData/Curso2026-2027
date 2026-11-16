
import PropTypes from "prop-types";

export default function FacilityHeader({ facility }) {
  return (
    <section className="detail-header">
      <span className="facility-type">
        {facility.facility_type === "library" ? "Library" : "Museum"}
      </span>

      <h1>{facility.name}</h1>

      <p>
        {facility.district.name} · {facility.neighborhood.name}
      </p>
    </section>
  );
}

FacilityHeader.propTypes = {
  facility: PropTypes.object.isRequired,
};
