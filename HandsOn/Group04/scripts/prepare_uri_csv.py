"""Stage OpenRefine outputs with fixed, code-based URI components.

Run from HandsOn/Group04: python scripts/prepare_uri_csv.py
The source CSVs are read only; mappings consume the staged files in csv/uri/.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'csv' / 'uri'
STATIONS = {
    '28079004': 'plaza-de-espana', '28079008': 'escuelas-aguirre',
    '28079011': 'ramon-y-cajal', '28079016': 'arturo-soria',
    '28079017': 'villaverde', '28079018': 'farolillo',
    '28079024': 'casa-de-campo', '28079027': 'barajas-pueblo',
    '28079035': 'plaza-del-carmen', '28079036': 'moratalaz',
    '28079038': 'cuatro-caminos', '28079039': 'barrio-del-pilar',
    '28079040': 'vallecas', '28079047': 'mendez-alvaro',
    '28079048': 'castellana', '28079049': 'parque-del-retiro',
    '28079050': 'plaza-castilla', '28079054': 'ensanche-de-vallecas',
    '28079055': 'urb-embajada', '28079056': 'plaza-eliptica',
    '28079057': 'sanchinarro', '28079058': 'el-pardo',
    '28079059': 'juan-carlos-i', '28079060': 'tres-olivos',
}
POLLUTANTS = {
    '1': 'dioxido-de-azufre', '6': 'monoxido-de-carbono',
    '7': 'monoxido-de-nitrogeno', '8': 'dioxido-de-nitrogeno',
    '9': 'pm2-5', '10': 'pm10', '12': 'oxidos-de-nitrogeno',
    '14': 'ozono', '20': 'tolueno', '30': 'benceno',
    '35': 'etilbenceno',
}
STATION_CLASSES = {'UT': 'UrbanTrafficStation',
                   'UF': 'UrbanBackgroundStation',
                   'S': 'SuburbanStation'}


def stage(source, target, extra, enrich, expected, delimiter=','):
    with (ROOT / 'csv' / source).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream, delimiter=delimiter)
        fields = reader.fieldnames
        assert fields and not set(extra) & set(fields), source
        rows = list(reader)
    assert len(rows) == expected, (source, len(rows))
    OUT.mkdir(exist_ok=True)
    with (OUT / target).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields + extra)
        writer.writeheader()
        for row in rows:
            row.update(enrich(row))
            writer.writerow(row)
    return rows


def main():
    assert len(set(STATIONS.values())) == 24
    assert len(set(POLLUTANTS.values())) == 11
    assert len(set(STATION_CLASSES.values())) == 3

    def station(row):
        return {'STATION_SLUG': STATIONS[row['CODIGO']],
                'STATION_CLASS': STATION_CLASSES[row['COD_TIPO']]}

    station_rows = stage('212629-0-estaciones-control-aire-updated.csv',
                         'stations.csv', ['STATION_SLUG', 'STATION_CLASS'],
                         station, 24)
    stage('212629-0-estaciones-control-aire-with-links.csv',
          'stations-with-links.csv', ['STATION_SLUG', 'STATION_CLASS'],
          station, 24)
    assert {r['CODIGO'] for r in station_rows} == set(STATIONS)
    station_short = {r['CODIGO_CORTO']: r['CODIGO'] for r in station_rows}

    def pollutant(row):
        return {'POLLUTANT_SLUG': POLLUTANTS[row['MAGNITUD']]}

    pollutant_rows = stage('contaminantes.csv', 'pollutants.csv',
                           ['POLLUTANT_SLUG'], pollutant, 11)
    stage('contaminantes-with-links.csv', 'pollutants-with-links.csv',
          ['POLLUTANT_SLUG'], pollutant, 11)
    stage('contaminantes-updated.csv', 'pollutants-updated.csv',
          ['POLLUTANT_SLUG'], pollutant, 11)
    assert {r['MAGNITUD'] for r in pollutant_rows} == set(POLLUTANTS)

    keys = set()
    points = set()

    def observation(row):
        code = row['PROVINCIA'] + row['MUNICIPIO'] + row['COD_ESTACION']
        assert station_short[row['ESTACION']] == code, row
        point = row['PUNTO_MUESTREO']
        prefix = f"{code}_{row['MAGNITUD']}_"
        assert point.startswith(prefix), row
        technique = point[len(prefix):]
        assert technique and '/' not in technique, row
        key = (STATIONS[code], POLLUTANTS[row['MAGNITUD']],
               technique, row['FECHA'], row['HORA'])
        assert key not in keys, key
        keys.add(key)
        points.add(point)
        return {'STATION_SLUG': key[0], 'POLLUTANT_SLUG': key[1],
                'TECHNIQUE': technique}

    stage('calair_tiemporeal-updated.csv', 'observations.csv',
          ['STATION_SLUG', 'POLLUTANT_SLUG', 'TECHNIQUE'], observation, 3024)
    assert len(keys) == 3024
    print(f'Staged 24 stations, 11 pollutants, 3 station categories, '
          f'{len(points)} sampling points and {len(keys)} unique observations.')


if __name__ == '__main__':
    main()
