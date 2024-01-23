LOAD httpfs;
LOAD spatial;
COPY (
    SELECT
       id,
       updatetime,
       version,
       CAST(names AS JSON) AS names,
       CAST(categories AS JSON) AS categories,
       CAST(websites AS JSON) AS websites,
       CAST(socials AS JSON) AS socials,
       CAST(phones AS JSON) AS phones,
       CAST(addresses AS JSON) AS addresses,
       ST_GeomFromWKB(geometry)
    FROM
       read_parquet('s3://overturemaps-us-west-2/release/2024-01-17-alpha.0/theme=places/type=*/*', hive_partitioning=1)
    WHERE
       (
           JSON_EXTRACT_STRING(categories, 'main') = 'women''s clothing store' OR 
           JSON_EXTRACT_STRING(categories, 'alternate') LIKE '%boutique%'
       )
       AND NOT (
           JSON_EXTRACT_STRING(names, 'common') LIKE '%JCPenny%' OR
           JSON_EXTRACT_STRING(names, 'common') LIKE '%Redbox%'
       )
       AND bbox.minx > -95.5854100258
       AND bbox.maxx < -88.87063784
       AND bbox.miny > 36.0851894959
       AND bbox.maxy < 39.7219776747
    ) TO 'MO.shp'
 WITH (FORMAT GDAL, DRIVER 'ESRI Shapefile');

bbox.minx > -88.0224609
bbox.maxx < -87.2534180
bbox.miny > 41.6400784
bbox.maxy < 42.0492926