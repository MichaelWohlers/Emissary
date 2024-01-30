from dotenv import load_dotenv
import os
import pandas as pd
import duckdb

load_dotenv()
aws_access_key_id = os.environ.get('YOUR_ACCESS_KEY')
aws_secret_access_key = os.environ.get('YOUR_SECRET_KEY')
aws_default_region = os.environ.get('AWS_DEFAULT_REGION')
place_location = os.environ.get('PLACE_SERVER')
records_location=os.environ.get('RECORDS_FOLDER')

def construct_query(keywords, exclusion_words, bbox):
        # Split keywords and exclusion words into arrays
        keyword_list = keywords.split(',')
        exclusion_list = exclusion_words.split(',')
        # Set AWS credentials (replace with your credentials)
        

        # Function to format keywords, handling single quotes
        def format_keyword(kw):
            return kw.replace("'", "").strip()

        # Construct WHERE clause for keywords
        keyword_conditions = ' OR '.join([
            f"JSON_EXTRACT_STRING(categories, 'main') = '{format_keyword(kw)}'" 
            for kw in keyword_list if kw.strip()
        ])

        # Construct WHERE clause for exclusion words
        exclusion_conditions = ' OR '.join([
            f"JSON_EXTRACT_STRING(names, 'common') LIKE '%{format_keyword(ew)}%'" 
            for ew in exclusion_list if ew.strip()
        ])

        # Validate the bbox parameter
        #if not isinstance(bbox, tuple) or len(bbox) != 4:
        #    raise ValueError("bbox must be a tuple with exactly 4 elements (minx, maxx, miny, maxy)")

        # Accessing elements of bbox safely
        #minx, maxx, miny, maxy = bbox
        query = f"""
            INSTALL httpfs;
            INSTALL spatial;
            LOAD httpfs;
            LOAD spatial;
            SET s3_region = '{aws_default_region}';
            SET s3_access_key_id = '{aws_access_key_id}';
            SET s3_secret_access_key = '{aws_secret_access_key}';
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
                    read_parquet('{place_location}', hive_partitioning=1)
                WHERE
                    ({keyword_conditions})
                    AND NOT ({exclusion_conditions})
                    AND bbox.minx > {bbox[0]}
                    AND bbox.maxx < {bbox[2]}
                    AND bbox.miny > {bbox[1]}
                    AND bbox.maxy < {bbox[3]}
            ) TO 'files/output.geojson'
        WITH (FORMAT GDAL, DRIVER 'GeoJSON', SRS 'EPSG:4326');
        """
        return query

def fetch_userClient_query(key,value):
    method=key
    data=value
    query = f"""
        INSTALL httpfs;
        LOAD httpfs;
        SET s3_region = '{aws_default_region}';
        SET s3_access_key_id = '{aws_access_key_id}';
        SET s3_secret_access_key = '{aws_secret_access_key}';
        COPY (
            SELECT
                id,
                email,
                hashed_password,
                permission_level,
                user_status,
                first_name,
                last_name
            FROM
            read_parquet('{records_location}clientuser.parquet')
            WHERE
                {method} = '{data}'
        ) TO 'files/clientUser.json'
    ;
    """
    return query

def hash_email(email):
    return hash(email)

def add_userClient(user):
    id=hash_email(user['email'])
    conn = duckdb.connect()

    # Read the existing data
    existing_data = conn.execute(f"""
        INSTALL httpfs;
        LOAD httpfs;
        SET s3_region = '{aws_default_region}';
        SET s3_access_key_id = '{aws_access_key_id}';
        SET s3_secret_access_key = '{aws_secret_access_key}';
        SELECT * FROM 
        read_parquet('s3://emissarybucket/records/emissary.parquet/clientuser.parquet')""").fetchdf()

    # Create a new DataFrame for the record to be added
    new_record = pd.DataFrame({
        'id': [id],
        'email': [user['email']],
        'hashed_password': [user['hashed_password']],
        'permission_level': [user['permission_level']],
        'user_status': [user['user_status']],
        'first_name': [user['first_name']],
        'last_name': [user['last_name']]
    })

    # Append the new record to the existing data
    updated_data = pd.concat([existing_data, new_record], ignore_index=True)
    
    # Write the updated data to a S3
    conn.execute(f"""
        INSTALL httpfs;
        LOAD httpfs;
        SET s3_region = '{aws_default_region}';
        SET s3_access_key_id = '{aws_access_key_id}';
        SET s3_secret_access_key = '{aws_secret_access_key}';
        CREATE TABLE userClient AS SELECT * FROM updated_data; 
        COPY userClient TO 's3://emissarybucket/records/emissary.parquet/clientuser.parquet';
        """)

    conn.close()

def delete_userClient(id):
    print('Attempting to delete user with ID:', id)
    
    try:
        # Validate that id is an integer
        user_id = int(id)

        conn = duckdb.connect()

        # Execute SQL statements
        conn.execute("INSTALL httpfs")
        conn.execute("LOAD httpfs")
        conn.execute(f"SET s3_region = '{aws_default_region}'")
        conn.execute(f"SET s3_access_key_id = '{aws_access_key_id}'")
        conn.execute(f"SET s3_secret_access_key = '{aws_secret_access_key}'")

        # Read and create a temporary table
        conn.execute("CREATE TEMPORARY TABLE tempUserClient AS SELECT * FROM read_parquet('s3://emissarybucket/records/emissary.parquet/clientuser.parquet')")

        # Safely format the DELETE query with the validated user_id
        delete_query = f"DELETE FROM tempUserClient WHERE id = {user_id}"
        conn.execute(delete_query)

        # Save changes back
        conn.execute("COPY tempUserClient TO 's3://emissarybucket/records/emissary.parquet/clientuser.parquet' (FORMAT 'parquet')")

        conn.close()
        print('User deletion completed')
    except ValueError:
        print("Invalid ID format")
        # Handle invalid ID format error
    except Exception as e:
        print("An error occurred during deletion:", e)
        # Handle other exceptions


def update_userClient(user_id, column, value):
    print(user_id)
    print(column)
    print(value)
    try:
        # Validate user_id is an integer
        user_id = int(user_id)

        # Whitelist of allowed columns to prevent injection
        allowed_columns = ['user_status', 'another_column']
        if column not in allowed_columns:
            raise ValueError("Invalid column name")

        # Sanitize value if necessary (e.g., if it's a string, escape quotes)
        # value = sanitize_value(value) # Implement this function based on your requirements

        conn = duckdb.connect()

        # Execute your statements
        conn.execute("INSTALL httpfs")
        conn.execute("LOAD httpfs")
        conn.execute(f"SET s3_region = '{aws_default_region}'")
        conn.execute(f"SET s3_access_key_id = '{aws_access_key_id}'")
        conn.execute(f"SET s3_secret_access_key = '{aws_secret_access_key}'")

        conn.execute(f"CREATE TABLE userClient AS SELECT * FROM read_parquet('s3://emissarybucket/records/emissary.parquet/clientuser.parquet')")

        update_query = f"UPDATE userClient SET {column} = '{value}' WHERE id = {user_id}"
        conn.execute(update_query)

        conn.execute("COPY userClient TO 's3://emissarybucket/records/emissary.parquet/clientuser.parquet'")

        conn.close()
    except Exception as e:
        print("An error occurred:", e)
        # Handle the error appropriately

