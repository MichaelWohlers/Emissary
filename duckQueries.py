from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import duckdb
from models import dbPlace
import logging
import json
from flask import jsonify
import json

def parse_ndjson_to_dict(file_path):
    data_dict = {}
    with open(file_path, 'r') as file:
        for line in file:
            try:
                json_object = json.loads(line)
                data_dict[json_object['id']] = json_object
            except json.JSONDecodeError:
                print(f"Error decoding JSON from line: {line}")
    return data_dict
ndjson_file_path = 'files/clientUser.json'


def execute_query_and_fetch_data(query):
        try:
            # Connect to DuckDB
            conn = duckdb.connect()
            logging.debug("Connected to DuckDB")

            # Execute the query and fetch results
            result = conn.execute(query).fetchall()
            logging.debug(f"Query executed: {query}")

            # Close the connection
            conn.close()
            logging.debug("Connection closed")

            # Read the content of output.geojson
            with open('files/output.geojson', 'r') as file:
                query_data = json.load(file)
                return query_data

        except Exception as e:
            logging.error(f"Error executing query: {e}")
            return None
        
def execute_query_and_fetch_clientUsers(query):
        try:
            # Connect to DuckDB
            conn = duckdb.connect()
            logging.debug("Connected to DuckDB")

            # Execute the query and fetch results
            result = conn.execute(query).fetchall()
            logging.debug(f"Query executed: {query}")
            

            # Close the connection
            conn.close()
            logging.debug("Connection closed")

            # parse nldjson to json
            parsed_data = parse_ndjson_to_dict(ndjson_file_path)
            print(parsed_data)
            return parsed_data

        except Exception as e:
            logging.error(f"Error executing query: {e}")
            return None

def execute_query_and_fetch_clientUser(query):
        try:
            # Connect to DuckDB
            conn = duckdb.connect()
            logging.debug("Connected to DuckDB")

            # Execute the query and fetch results
            result = conn.execute(query).fetchall()
            logging.debug(f"Query executed: {query}")
            

            # Close the connection
            conn.close()
            logging.debug("Connection closed")

            # Read the content of output.geojson
            with open('files/clientUser.json', 'r') as file:
                query_data = json.load(file)
                return query_data

        except Exception as e:
            logging.error(f"Error executing query: {e}")
            return None

