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

        {information.heritage_designations?.length > 0 && (
          <WikidataListItem
            label="Declaraciones patrimoniales"
            values={information.heritage_designations.map(
              (designation) =>
                designation.charAt(0).toUpperCase() + designation.slice(1)
            )}
          />
        )}

        {information.activity_policies?.length > 0 && (
          <WikidataListItem
            label="Políticas de actividad"
            values={information.activity_policies.map(
              (policy) => policy.charAt(0).toUpperCase() + policy.slice(1)
            )}
          />
        )}

        {information.awards?.length > 0 && (
          <WikidataListItem
            label="Premios y reconocimientos"
            values={information.awards.map(
              (award) => award.charAt(0).toUpperCase() + award.slice(1)
            )}
          />
        )}

        {information.area?.length > 0 && (
          <WikidataListItem
            label="Superficie"
            values={information.area.map(
              (item) =>
                `${item.value.toLocaleString("es-ES")} ${
                  item.unit || ""
                }`.trim()
            )}
          />
        )}

        {information.x_usernames?.length > 0 && (
          <div className="detail-info-item">
            <span className="detail-label">X (Twitter)</span>

            {information.x_usernames.map((username) => (
              <a
                key={username}
                href={`https://x.com/${username.replace(/^@/, "")}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                @{username.replace(/^@/, "")}
              </a>
            ))}
          </div>
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
    heritage_designations: PropTypes.arrayOf(PropTypes.string),
    activity_policies: PropTypes.arrayOf(PropTypes.string),
    awards: PropTypes.arrayOf(PropTypes.string),
    area: PropTypes.arrayOf(
      PropTypes.shape({
        value: PropTypes.number.isRequired,
        unit: PropTypes.string,
      })
    ),
    x_usernames: PropTypes.arrayOf(PropTypes.string),
    country: PropTypes.arrayOf(PropTypes.string),
    located_in: PropTypes.arrayOf(PropTypes.string),
    architectural_style: PropTypes.arrayOf(PropTypes.string),
    coordinates: PropTypes.arrayOf(PropTypes.string),
    wikidata_uri: PropTypes.string,
  }),
};