# Analysis

- The openrefine directory is missing.

# Ontology

- Check that all property names start with a lower-case letter (lowerCamelCase).
- Distinguish between object properties (where the value is another individual/resource) and datatype properties (where the value is a typed literal).
- The use of subproperties is not correct.
- The domain and/or range is missing for some properties.

# RDF Graph

- URIs for individuals should be human-readable and meaningful; an auto-incremented integer does not satisfy this criterion.
- Values defined as literals should be instances.
- Character encoding issues are not resolved.
- Some individuals are missing human-readable labels (rdfs:label).
