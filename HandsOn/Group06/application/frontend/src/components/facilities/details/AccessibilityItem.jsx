
import PropTypes from "prop-types";

export default function AccessibilityItem({ label, available }) {
  return (
    <div className="accessibility-item">
      <span>{label}</span>
      <span className={available ? "available" : "unavailable"}>
        {available ? "Si" : "No"}
      </span>
    </div>
  );
}

AccessibilityItem.propTypes = {
  label: PropTypes.string.isRequired,
  available: PropTypes.bool.isRequired,
};
