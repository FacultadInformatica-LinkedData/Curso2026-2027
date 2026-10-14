"""Prepare the Madrid open-data CSV files for the RML mapping.

The source files are semicolon-delimited and encoded as Windows-1252.  This
script writes small, UTF-8, comma-delimited projections with trimmed values so
that the mapping remains portable across RML processors.
"""

from __future__ import annotations

import csv
import html
import re
from pathlib import Path


GROUP_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = GROUP_DIR / "csv"
OUTPUT_DIR = SOURCE_DIR / "clean"

FACILITY_FIELDS = [
    "id",
    "name",
    "description",
    "opening_hours",
    "transport",
    "content_url",
    "street_address",
    "address_label",
    "postal_code",
    "district_code",
    "district_name",
    "neighborhood_code",
    "neighborhood_name",
    "latitude",
    "longitude",
    "telephone",
    "fax",
    "email",
    "facility_type",
]


def clean_text(value: str | None) -> str:
    """Decode HTML entities, normalize whitespace, and trim a CSV value."""
    if not value:
        return ""
    return re.sub(r"\s+", " ", html.unescape(value).replace("\xa0", " ")).strip()


def read_source(filename: str) -> list[dict[str, str]]:
    with (SOURCE_DIR / filename).open(encoding="cp1252", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=";"))


def transform_row(source: dict[str, str]) -> dict[str, str]:
    name = clean_text(source.get("NOMBRE"))
    street_parts = [
        clean_text(source.get("CLASE-VIAL")),
        clean_text(source.get("NOMBRE-VIA")),
    ]
    street = " ".join(part for part in street_parts if part)
    number = clean_text(source.get("NUM"))
    if number:
        street = f"{street}, {number}" if street else number

    district_code = clean_text(source.get("COD-DISTRITO"))
    district_name = clean_text(source.get("DISTRITO"))
    if district_name.upper() == "DISTRITO" or not district_code:
        district_code = ""
        district_name = ""

    neighborhood_code = clean_text(source.get("COD-BARRIO"))
    neighborhood_name = clean_text(source.get("BARRIO"))
    if not district_code or not neighborhood_code:
        neighborhood_code = ""
        neighborhood_name = ""

    facility_type = clean_text(source.get("TIPO")).rstrip("/").rsplit("/", 1)[-1]

    return {
        "id": clean_text(source.get("PK")),
        "name": name,
        "description": clean_text(source.get("DESCRIPCION-ENTIDAD"))
        or clean_text(source.get("DESCRIPCION")),
        "opening_hours": clean_text(source.get("HORARIO")),
        "transport": clean_text(source.get("TRANSPORTE")),
        "content_url": clean_text(source.get("CONTENT-URL")),
        "street_address": street,
        "address_label": f"Dirección de {name}" if name else "",
        "postal_code": clean_text(source.get("CODIGO-POSTAL")),
        "district_code": district_code,
        "district_name": district_name,
        "neighborhood_code": neighborhood_code,
        "neighborhood_name": neighborhood_name,
        "latitude": clean_text(source.get("LATITUD")),
        "longitude": clean_text(source.get("LONGITUD")),
        "telephone": clean_text(source.get("TELEFONO")),
        "fax": clean_text(source.get("FAX")),
        "email": clean_text(source.get("EMAIL")),
        "facility_type": facility_type,
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    libraries = [transform_row(row) for row in read_source("libraries.csv")]
    museums = [transform_row(row) for row in read_source("museums.csv")]
    all_rows = libraries + museums

    districts = {
        (row["district_code"], row["district_name"])
        for row in all_rows
        if row["district_code"] and row["district_name"]
    }
    neighborhoods = {
        (
            row["district_code"],
            row["neighborhood_code"],
            row["neighborhood_name"],
        )
        for row in all_rows
        if row["district_code"]
        and row["neighborhood_code"]
        and row["neighborhood_name"]
    }

    write_csv(OUTPUT_DIR / "libraries.csv", FACILITY_FIELDS, libraries)
    write_csv(OUTPUT_DIR / "museums.csv", FACILITY_FIELDS, museums)
    write_csv(
        OUTPUT_DIR / "districts.csv",
        ["district_code", "district_name"],
        [
            {"district_code": code, "district_name": name}
            for code, name in sorted(districts, key=lambda item: int(item[0]))
        ],
    )
    write_csv(
        OUTPUT_DIR / "neighborhoods.csv",
        ["district_code", "neighborhood_code", "neighborhood_name"],
        [
            {
                "district_code": district_code,
                "neighborhood_code": neighborhood_code,
                "neighborhood_name": name,
            }
            for district_code, neighborhood_code, name in sorted(
                neighborhoods, key=lambda item: (int(item[0]), int(item[1]))
            )
        ],
    )

    print(
        f"Prepared {len(libraries)} libraries, {len(museums)} museums, "
        f"{len(districts)} districts and {len(neighborhoods)} neighborhoods."
    )


if __name__ == "__main__":
    main()
