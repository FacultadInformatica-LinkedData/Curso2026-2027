
import PropTypes from "prop-types";

export default function WikidataListItem({ label, values }) {
  return (
    <div className="detail-info-item">
      <span className="detail-label">{label}</span>

      {values?.length > 0 ? (
        <ul>
          {values.map((value, index) => (
            <li key={`${value}-${index}`}>{value}</li>
          ))}
        </ul>
      ) : (
        <span className="detail-value">No hay información</span>
      )}
    </div>
  );
}

WikidataListItem.propTypes = {
  label: PropTypes.string.isRequired,
  values: PropTypes.arrayOf(PropTypes.string),
};
