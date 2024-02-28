import pandas as pd

# Replace 'input_file.parquet' with the path to your actual Parquet file
parquet_file = 'files/usaCounties.parquet'

# Replace 'output_file.csv' with the desired output CSV file path
csv_file = 'files/usaCounties_file.csv'

# Read the Parquet file
df = pd.read_parquet(parquet_file)

# Save the dataframe to a CSV file
df.to_csv(csv_file, index=False)

print(f"Successfully converted {parquet_file} to {csv_file}")


"""LOAD httpfs;
LOAD spatial;

CREATE TABLE admin_boundaries_filtered AS
SELECT
    id,
    adminlevel,
    bbox,
    ST_GeomFromWKB(geometry) AS geometry
FROM read_parquet('files/theme=admins/type=administrativeBoundary/*', filename=true, hive_partitioning=1)
WHERE adminlevel = 4;
COPY admin_boundaries_filtered TO 'files/admin_boundaries_filtered.parquet';
"""


"""
LOAD spatial;
COPY (
    SELECT
        id,
        adminlevel,
        ST_GeomFromWKB(geometry) AS geometry
    FROM read_parquet('files/admin_boundaries_filtered.parquet', filename=true, hive_partitioning=1)
) TO 'admins_sample.geojsonseq'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');
"""

"""
LOAD httpfs;
LOAD spatial;

CREATE VIEW admins_view AS (
    SELECT
        *
    FROM
        read_parquet('files/theme=admins/type=*/*', filename=true, hive_partitioning=1)
);
COPY (
    SELECT
            admins.id,
            admins.subType,
            admins.isoCountryCodeAlpha2,
            JSON(admins.names) AS names,
            JSON(admins.sources) AS sources,
            areas.areaId,
            ST_GeomFromWKB(areas.areaGeometry) as geometry
    FROM admins_view AS admins
    INNER JOIN (
        SELECT
            id as areaId,
            localitytype,
            geometry AS areaGeometry
        FROM admins_view
    ) AS areas ON areas.localitytype == admins.id
    WHERE admins.adminLevel = 2
    LIMIT 10
) TO 'admins2_sample.geojsonseq'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');

"""

"""
LOAD httpfs;
LOAD spatial;

COPY (
SELECT
    id,
    adminlevel,
    ST_GeomFromWKB(geometry) AS geometry
FROM read_parquet('files/theme=admins/type=administrativeBoundary/*', filename=true, hive_partitioning=1)
WHERE adminlevel = 1
AND bbox.minx > -125.0
AND bbox.maxx < -66.9
AND bbox.miny > 24.0
AND bbox.maxy < 49.4

) TO 'admins1US_sample.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');
"""