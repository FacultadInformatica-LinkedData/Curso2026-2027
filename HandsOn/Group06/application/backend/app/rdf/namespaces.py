
from rdflib import Namespace
from rdflib.namespace import OWL

# Ontología de la aplicación
MC = Namespace("http://w3id.org/madrid-culture/ontology/")

# Recursos del dataset
RES = Namespace("http://w3id.org/madrid-culture/resource/")

# Vocabularios externos
SCHEMA = Namespace("http://schema.org/")

# Clases
LIBRARY = MC.Library
MUSEUM = MC.Museum
ACCESSIBILITY = MC.Accessibility
ADDRESS = MC.Address
DISTRICT = MC.District
NEIGHBORHOOD = MC.Neighborhood

# Propiedades de las instalaciones
TRANSPORT = MC.transport
HAS_ACCESSIBILITY = MC.hasAccessibility
HAS_ADDRESS = MC.hasAddress
EMAIL = MC.email
TYPE = MC.type

# Propiedades de las direcciones
STREET_ADDRESS = MC.streetAddress
POSTAL_CODE = MC.postalCode
LOCATED_IN_DISTRICT = MC.locatedInDistrict
LOCATED_IN_NEIGHBORHOOD = MC.locatedInNeighborhood

# Propiedades de accesibilidad
ACCESSIBLE = MC.accessible
PARTIALLY_ACCESSIBLE = MC.partiallyAccessible
NO_INFO_ACCESSIBILITY = MC.noInfoAccessibility
SIGN_LANGUAGE = MC.signLanguage
TACTILE_PAVING = MC.tactilePaving
MAGNETIC_INDUCTION_LOOP = MC.magneticInductionLoop

# Propiedades de Schema.org
NAME = SCHEMA.name
URL = SCHEMA.url
LATITUDE = SCHEMA.latitude
LONGITUDE = SCHEMA.longitude
TELEPHONE = SCHEMA.telephone
OPENING_HOURS = SCHEMA.openingHours

# Relaciones externas
SAME_AS = OWL.sameAs