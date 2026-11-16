
import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";

import { getFacilityDetail } from "../services/facilityService";
import Header from "../components/layout/Header";

import FacilityHeader from "../components/facilities/details/FacilityHeader";
import FacilityLocation from "../components/facilities/details/FacilityLocation";
import FacilityVisitorInfo from "../components/facilities/details/FacilityVisitorInfo";
import FacilityContact from "../components/facilities/details/FacilityContact";
import FacilityAccessibility from "../components/facilities/details/FacilityAccessibility";
import WikidataSection from "../components/facilities/details/WikidataSection";
import FacilityExternalInfo from "../components/facilities/details/FacilityExternalInfo";

import "./FacilityDetailPage.css";

export default function FacilityDetailPage() {
  const { type, facilityId } = useParams();

  const [facility, setFacility] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchFacility() {
      try {
        setLoading(true);
        setError(null);

        const data = await getFacilityDetail(
          `${type}/${facilityId}`
        );

        setFacility(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchFacility();
  }, [type, facilityId]);

  if (loading) {
    return (
      <>
        <Header />
        <main className="detail-page">
          <p className="detail-message">Cargando instalación...</p>
        </main>
      </>
    );
  }

  if (error || !facility) {
    return (
      <>
        <Header />
        <main className="detail-page">
          <p className="detail-message">
            {error || "Facility not found."}
          </p>
        </main>
      </>
    );
  }

  return (
    <main className="detail-page">
      <FacilityHeader facility={facility} />
      <div className="detail-columns">
        <div className="facility-information">

          <FacilityLocation facility={facility} />
          <FacilityVisitorInfo facility={facility} />
          <FacilityContact facility={facility} />
          <FacilityAccessibility facility={facility} />
          <FacilityExternalInfo facility={facility} />
        </div>

        <aside className="wikidata-information">
          <WikidataSection
            information={facility.wikidata_information}
          />
        </aside>
      </div>
    </main>
  );
}
