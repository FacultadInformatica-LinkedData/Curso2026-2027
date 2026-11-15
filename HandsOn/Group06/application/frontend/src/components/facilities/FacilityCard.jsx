
import PropTypes from "prop-types";
import "./FacilityCard.css";

import { Link } from "react-router-dom";

export default function FacilityCard({ facility }) {
  const facilityId = facility.id.split("/").slice(-2).join("/");

  return (
    <Link 
      to={`/facilities/${facilityId}`}
      className="facility-card-link"
    >
      <article className="facility-card">
        <span className="facility-type">
          {facility.facility_type === "library" ? "Biblioteca" : "Museo"}
        </span>

        
          <h2>{facility.name}</h2>

        <p>Distrito: {facility.district.name}</p>

        <p>Barrio: {facility.neighborhood.name}</p>
      </article>
    </Link>
  );
}

FacilityCard.propTypes = {
  facility: PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    facility_type: PropTypes.oneOf(["library", "museum"]).isRequired,
    district: PropTypes.shape({
      name: PropTypes.string.isRequired,
    }).isRequired,
    neighborhood: PropTypes.shape({
      name: PropTypes.string.isRequired,
    }).isRequired
  }).isRequired,
};
