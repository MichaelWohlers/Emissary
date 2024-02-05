#offLoad.py
import duckdb
import sys
import redis
import os
import time
import json
import threading
from dotenv import load_dotenv
load_dotenv()
 # Initialize Redis connection
redis_url = os.getenv('REDISCLOUD_URL')
r = redis.from_url(redis_url)

exit_loop = False

def assemble_and_publish_geojson(file_path, redis_client):
    global exit_loop  # Ensure exit_loop is recognized within this function
    
    geojson_header = '{ "type": "FeatureCollection", "features": ['
    is_new_read = True
    last_read_position = 0
    base_position = 149

    while not os.path.exists(file_path):
        time.sleep(2)  # Wait for the file to be created by the DuckDB query

    while not exit_loop:  # Use the global exit_loop flag to control loop exit
        try:
            new_data = ''
            with open(file_path, 'r') as file:
                file.seek(last_read_position)
                new_data = file.read()
                last_read_position = file.tell()
                if last_read_position > base_position:
                    last_read_position += 1
                    base_position = last_read_position
                
            if new_data:
                completed_json = (geojson_header + new_data) if is_new_read else new_data
                is_new_read = False
                
                if not completed_json.endswith(']}'):
                    completed_json += ']}'
                
                redis_client.publish('geojson_channel', completed_json)
            
            time.sleep(2)  # Check file again after a delay

        except Exception as e:
            print(f"Error assembling or publishing GeoJSON: {str(e)}")
            break

def execute_query_and_fetch_data(query):
    global exit_loop  # Declare as global to modify it
    
   
    
    # Start monitoring the output file in a separate thread or before executing the query
    # Consider threading or adjusting the flow to ensure this happens concurrently with query execution

    # Connect to DuckDB and execute the query
    conn = duckdb.connect()
    conn.execute(query)  # Assuming this writes to 'output.geojson'
    conn.close()

    exit_loop = True  # Signal to exit the monitoring loop after the query completes

if __name__ == "__main__":
    query_key='query_for_offload'
    print('hello from offLoad.py')
    query = json.loads(r.get(query_key))
    # Start file monitoring in a separate thread
    thread = threading.Thread(target=assemble_and_publish_geojson, args=('output.geojson', r,))
    thread.start()

    # Execute query and wait for completion
    execute_query_and_fetch_data(query)
    
    # Ensure the monitoring thread completes
    thread.join()
    

