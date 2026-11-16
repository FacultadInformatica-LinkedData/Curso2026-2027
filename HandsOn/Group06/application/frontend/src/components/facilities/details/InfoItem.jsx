
import PropTypes from "prop-types";

export default function InfoItem({ label, value }) {
  const displayValue =
    value === null || value === undefined || value === ""
      ? "No hay información"
      : value;

  return (
    <div className="detail-info-item">
      <span className="detail-label">{label}</span>
      <span className="detail-value">{displayValue}</span>
    </div>
  );
}

InfoItem.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.number,
    PropTypes.bool,
  ]),
};
