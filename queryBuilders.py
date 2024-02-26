from dotenv import load_dotenv
import os
import pandas as pd
import duckdb
from io import BytesIO  

load_dotenv()
aws_access_key_id = os.environ.get('YOUR_ACCESS_KEY')
aws_secret_access_key = os.environ.get('YOUR_SECRET_KEY')
aws_default_region = os.environ.get('AWS_DEFAULT_REGION')
place_location = os.environ.get('PLACE_SERVER')
records_location=os.environ.get('RECORDS_FOLDER')
s3_output=os.environ.get('S3_OUTPUT')

def construct_query(keywords, exclusion_words, bbox):
    # Split keywords and exclusion words into arrays
    keyword_list = keywords.split(',')
    exclusion_list = exclusion_words.split(',') if exclusion_words else []

    # Function to format keywords, handling single quotes
    def format_keyword(kw):
        return kw.replace("'", "").strip()

    # Construct WHERE clause for keywords
    keyword_conditions = ' OR '.join([
        f"JSON_EXTRACT_STRING(categories, 'main') = '{format_keyword(kw)}'" 
        for kw in keyword_list if kw.strip()
    ])

    # Construct WHERE clause for exclusion words, if any
    if exclusion_list:
        exclusion_conditions = ' AND NOT (' + ' OR '.join([
            f"JSON_EXTRACT_STRING(names, 'common') LIKE '%{format_keyword(ew)}%'" 
            for ew in exclusion_list if ew.strip()
        ]) + ')'
    else:
        exclusion_conditions = ''

    # Construct the query
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
                {exclusion_conditions}
                AND bbox.minx > {bbox[0]}
                AND bbox.maxx < {bbox[2]}
                AND bbox.miny > {bbox[1]}
                AND bbox.maxy < {bbox[3]}
        ) TO 'output.geojson'
    WITH (FORMAT GDAL, DRIVER 'GeoJSON', SRS 'EPSG:4326');
    """
    print(query)
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

def save_contactssss(data, user_id):
    conn = duckdb.connect()
    # This line ensures that 'contacts' is a list. If 'data' is a dictionary,
    # it is wrapped in a list. If 'data' is already a list, it is used directly.
    # If 'data' is neither (else case), an empty list is used.
    contacts = [data] if isinstance(data, dict) else data if isinstance(data, list) else []

    # Create a DataFrame for the new contacts
    new_records = pd.DataFrame(contacts)

    # Read the existing data
    existing_data = conn.execute(f"""
        INSTALL httpfs;
        LOAD httpfs;
        SET s3_region = '{aws_default_region}';
        SET s3_access_key_id = '{aws_access_key_id}';
        SET s3_secret_access_key = '{aws_secret_access_key}';
        SELECT * FROM 
        read_parquet('s3://emissarybucket/records/userData/{user_id}/contacts.parquet')""").fetchdf()

    

    # Append the new record to the existing data
    updated_data = pd.concat([existing_data, new_records], ignore_index=True)
    
    # Write the updated data to a S3
    conn.execute(f"""
        INSTALL httpfs;
        LOAD httpfs;
        SET s3_region = '{aws_default_region}';
        SET s3_access_key_id = '{aws_access_key_id}';
        SET s3_secret_access_key = '{aws_secret_access_key}';
        CREATE TABLE contactData AS SELECT * FROM {updated_data}; 
        COPY contactData TO 's3://emissarybucket/records/userData/{user_id}/contacts.parquet';
        """)

    conn.close()

def save_contact(data, user_id):
    try:
        conn = duckdb.connect()
        conn.execute("INSTALL httpfs;")
        conn.execute("LOAD httpfs;")
        conn.execute(f"SET s3_region = '{aws_default_region}';")
        conn.execute(f"SET s3_access_key_id = '{aws_access_key_id}';")
        conn.execute(f"SET s3_secret_access_key = '{aws_secret_access_key}';")

        contacts = [data] if isinstance(data, dict) else data if isinstance(data, list) else []
        new_records = pd.DataFrame(contacts)
        
        # Create a temporary table for the new records
        conn.register('new_records', new_records)
        
        # Assuming the existing data is structured similarly to the new data
        existing_data = conn.execute(f"""
            SELECT * FROM 
            read_parquet('s3://emissarybucket/records/userData/{user_id}/contacts.parquet')
        """).df()

        # Append the new records to the existing data
        updated_data = pd.concat([existing_data, new_records], ignore_index=True)

        # Register the updated DataFrame as a temporary table
        conn.register('updated_data', updated_data)

        # Dynamically insert the user_id into the COPY command string
        copy_command = f"""
            COPY updated_data 
            TO 's3://emissarybucket/records/userData/{user_id}/contacts.parquet' (FORMAT 'parquet');
        """
        conn.execute(copy_command)

        conn.close()
        return True  # Indicate success
    except Exception as e:
        print(f"Error saving contact: {e}")
        return False  # Indicate failure



def fetch_contacts(user_id, key=None, value=None):
    where_clause = ""
    if key and value:  # Ensure both key and value are provided and non-empty
        # Ensure the key is a valid column name to mitigate injection risks
        # This is a basic check; consider more robust validation based on your context
        if key in ['id', 'name', 'category', 'website', 'socials', 'phone', 'address']:
            where_clause = f"WHERE {key} = '{value}'"  # Basic validation applied
        else:
            # Handle invalid key case, e.g., by raising an error or logging a warning
            raise ValueError("Invalid key provided for filtering.")

    query = f"""
        INSTALL httpfs;
        LOAD httpfs;
        SET s3_region = 'your_aws_default_region';
        SET s3_access_key_id = 'your_aws_access_key_id';
        SET s3_secret_access_key = 'your_aws_secret_access_key';
        COPY (
            SELECT
                id,
                name,
                category,
                website,
                socials,
                phone,
                address
            FROM
            read_parquet('s3://emissarybucket/records/userData/{user_id}/contacts.parquet')
            {where_clause}
        ) TO 'files/contacts.json'
    ;
    """
    return query
