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
class SingletonState:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SingletonState, cls).__new__(cls)
            # Initialize your variables here
            cls._instance.last_read_position = 0
            cls._instance.base_position = 149
            cls._instance.is_new_read = True
        return cls._instance

def assemble_and_publish_geojson(file_path, redis_client):
    global exit_loop  # Ensure exit_loop is recognized within this function
    state = SingletonState()  # Get the singleton instance

    geojson_header = ('{"type": "FeatureCollection","features": [')
    

    while not os.path.exists(file_path):
        time.sleep(2)  # Wait for the file to be created by the DuckDB query

    while not exit_loop:  # Use the global exit_loop flag to control loop exit
        try:
            new_data = ''
            with open(file_path, 'r') as file:
                file.seek(state.last_read_position)
                new_data = file.read()
                state.last_read_position = file.tell()
                if state.last_read_position > state.base_position:
                    state.last_read_position += 1
                    state.base_position = state.last_read_position
                
            if new_data:
                completed_json = (geojson_header + new_data) if state.is_new_read else new_data
                state.is_new_read = False
                
                if not completed_json.endswith(']}'):
                    completed_json += ']}'
                
                print(completed_json)
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

def checkFile():
    # Specify the expected path of your output.geojson file
    output_file_path = 'output.geojson'  # Adjust this path as necessary

    # Check if the file exists
    if os.path.exists(output_file_path):
        print(f"File {output_file_path} exists.")
    else:
        print(f"File {output_file_path} does not exist.")

    # List all files in the directory where output.geojson is supposed to be
    directory = os.path.dirname(output_file_path)
    print(f"Listing contents of directory: {directory or '.'}")
    for filename in os.listdir(directory or '.'):
        print(filename)

if __name__ == "__main__":
    query_key='query_for_offload'
    print('hello from offLoad.py')
    print(exit_loop)
    query = json.loads(r.get(query_key))
    # Start file monitoring in a separate thread
    thread = threading.Thread(target=assemble_and_publish_geojson, args=('output.geojson', r,))
    print('starting thread')

    thread.start()
    print('executing query')

    # Execute query and wait for completion
    execute_query_and_fetch_data(query)
    time.sleep(2)
    print(exit_loop)

    
    checkFile()

   
    

