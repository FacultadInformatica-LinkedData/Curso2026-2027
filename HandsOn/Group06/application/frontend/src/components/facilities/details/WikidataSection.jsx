import PropTypes from "prop-types";
import InfoItem from "./InfoItem";
import WikidataListItem from "./WikidataListItem";

export default function WikidataSection({ information }) {
  if (!information) {
    return (
      <section className="detail-section">
        <h2>Información adicional</h2>
        <p>No linked Wikidata information available.</p>
      </section>
    );
  }

  const description = information.description
    ? information.description.charAt(0).toUpperCase() +
      information.description.slice(1)
    : null;

  const inception = information.inception?.split("-")[0];

  return (
    <section className="detail-section">
      <h2>Información adicional</h2>

      {information.image && (
        <div className="wikidata-images">
          <img
            src={information.image}
            alt={information.name || "Facility"}
            loading="lazy"
          />
        </div>
      )}

      {information.interior_image && (
        <div className="wikidata-images">
          <img
            src={information.interior_image}
            alt={`Interior de ${information.name || "la instalación"}`}
            loading="lazy"
          />
        </div>
      )}

      <div className="detail-grid">
        {description && (
          <InfoItem label="Descripción" value={description} />
        )}

        {inception && (
          <InfoItem label="Año de fundación" value={inception} />
        )}

        {information.founders?.length > 0 && (
          <WikidataListItem
            label="Fundadores"
            values={information.founders}
          />
        )}

        {information.architect?.length > 0 && (
          <WikidataListItem
            label="Arquitectos"
            values={information.architect}
          />
        )}
      </div>
    </section>
  );
}

WikidataSection.propTypes = {
  information: PropTypes.shape({
    wikidata_id: PropTypes.string,
    name: PropTypes.string,
    description: PropTypes.string,
    image: PropTypes.string,
    logo: PropTypes.string,
    interior_image: PropTypes.string,
    founders: PropTypes.arrayOf(PropTypes.string),
    inception: PropTypes.string,
    architect: PropTypes.arrayOf(PropTypes.string),
    country: PropTypes.arrayOf(PropTypes.string),
    located_in: PropTypes.arrayOf(PropTypes.string),
    architectural_style: PropTypes.arrayOf(PropTypes.string),
    coordinates: PropTypes.arrayOf(PropTypes.string),
    wikidata_uri: PropTypes.string,
  }),
};