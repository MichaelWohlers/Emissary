#routes.py
from flask import render_template, request, jsonify, url_for, session, redirect, flash, send_from_directory, make_response
from models import Place, EmailTemplate, clientUser
#from shared import db
from flask import current_app  # Import at the top of your file
import subprocess
import smtplib
import os
from werkzeug.security import check_password_hash, generate_password_hash
import json
import logging
from dotenv import load_dotenv
from queryBuilders import construct_query, fetch_userClient_query, add_userClient, delete_userClient, update_userClient, save_contact, fetch_contacts, delete_contacts
from tasks import execute_query_and_fetch_data, execute_query_and_fetch_clientUser, execute_query_and_fetch_clientUsers
import subprocess
import redis
import threading
from app import socketio
import heroku3
from io import BytesIO
import boto3
import pandas as pd

load_dotenv()


# Configure Python's logging
logging.basicConfig(level=logging.DEBUG)

PROGRESS_FILE_PATH = 'business_scraper/progress.txt'
aws_access_key_id = os.environ.get('YOUR_ACCESS_KEY')
aws_secret_access_key = os.environ.get('YOUR_SECRET_KEY')
aws_default_region = os.environ.get('AWS_DEFAULT_REGION')
place_location = os.environ.get('PLACE_FOLDER')
records_location=os.environ.get('RECORDS_FOLDER')
os.environ['AWS_ACCESS_KEY_ID'] = os.getenv('YOUR_ACCESS_KEY')
os.environ['AWS_SECRET_ACCESS_KEY'] = os.getenv('YOUR_SECRET_KEY')

# Load the merged GeoJSON data
with open('files/updated_usaCounties.geojson', 'r') as file:
    county_data = json.load(file)

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

# Usage
state = SingletonState()

def is_logged_in():
    return 'user_id' in session



def configure_routes(app):

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            if password != confirm_password:
                flash('Passwords do not match!')
                return redirect(url_for('register'))

            new_user = clientUser(first_name=first_name, last_name=last_name, email=email, permission_level='standard',user_status='pending approval')
            new_user.set_password(password)  # Set the password using the set_password method
            user=new_user.to_dict()
            add_userClient(user)

            flash('Account created successfully!')
            return redirect(url_for('login'))

        return render_template('register.html')

    

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['exampleInputEmail']
            password = request.form['exampleInputPassword']
            user = fetchClientUser('email',email)
            print(f"Type of user: {type(user)}")  # Debug print

            if user is None:
                flash('Invalid email')
                return render_template('login.html')

            if not user.check_password(password):
                flash('Invalid Password')
                return render_template('login.html')

            if user.user_status == 'pending approval':
                flash('Your account is not active. Please contact the administrator.')
                return render_template('login.html')

            session['user_id'] = user.id
            session['user_permission'] = user.permission_level
            session['user_status'] = user.user_status
            session['user_name'] = user.first_name + " " + user.last_name
            return redirect(url_for('home'))
            
        return render_template('login.html')

    
    def fetchClientUser(key,value):
        try:
            query = fetch_userClient_query(key,value)
            json_data = execute_query_and_fetch_clientUser(query)
            if key==1 and value==1:
                return json_data
            if json_data is None:
                return None  # User not found

            if isinstance(json_data, dict):
                user_data = json_data
            else:
                # Parse the JSON string to a Python dictionary
                user_data = json.loads(json_data)
            
            if not user_data:
                return None  # User not found
            #if switch == 'list':
               # return(user_data)


            user_object = clientUser()
            user_object.id = user_data.get('id')
            user_object.email = user_data.get('email')
            user_object.hashed_password = user_data.get('hashed_password')
            user_object.permission_level = user_data.get('permission_level')
            user_object.user_status = user_data.get('user_status')
            user_object.first_name = user_data.get('first_name')
            user_object.last_name = user_data.get('last_name')

            return user_object

        except Exception as e:
            # Log the error for debugging
            print(f"Error in fetchClientUser: {e}")
            return None
    def fetchClientUsers(key,value):
        query = fetch_userClient_query(key,value)
        data = execute_query_and_fetch_clientUsers(query)
        return data
        
    
    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        return redirect(url_for('login'))
    

    @app.route('/')
    def home():
        if not is_logged_in():
            return redirect(url_for('login'))
        user_name = session.get('user_name', 'Default User')        
        user_status = session.get('user_status', 'active')
        return render_template('index.html', user_name=user_name,user_status=user_status)
    
    @app.route('/email')
    def email():
        if not is_logged_in():
            return redirect(url_for('login'))
        return render_template('email.html')
    @app.route('/template-builder')
    def template():
        if not is_logged_in():
            return redirect(url_for('login'))
        return render_template('template-builder.html')
    
    @app.route('/email_feature', methods=['GET', 'POST'])
    def email_feature():
        if not is_logged_in():
            return redirect(url_for('login'))
        if request.method == 'POST':
            selected_status = request.json.get('status')
            print(f"Selected status: {selected_status}")  # Debug print

            # Query places with the selected status and access their contact emails
            places = Place.query.filter(Place.status == selected_status).all()
            print(f"Found {len(places)} places with status '{selected_status}'")  # Debug print

            email_addresses = [place.contact.email for place in places if place.contact]
            print(f"Email addresses: {email_addresses}")  # Debug print

            return jsonify(email_addresses)

        elif request.method == 'GET':
            # For GET request, return distinct status values as JSON
            status_values = Place.query.with_entities(Place.status).distinct().all()
            status_values = [status[0] for status in status_values]
            print(f"Status values for dropdown: {status_values}")  # Debug print

            return jsonify(status_values)

    
    @app.route('/get-places')
    def get_places():
        if not is_logged_in():
            return redirect(url_for('login'))
        try:
            places = Place.query.all()
            place_list = [place.to_dict() for place in places]

            # Print the data for debugging
            #print("Data being sent to DataTable:", place_list)

            return jsonify(place_list)
        except Exception as e:
            current_app.logger.error(f"Error fetching places: {e}")
            return jsonify([]), 500

    @app.route('/about')
    def about():
        if not is_logged_in():
            return redirect(url_for('login'))
        user_name = session.get('user_name', 'Default User')
        return render_template('about.html')



    @app.route('/addressbook')
    def address_book():
        if not is_logged_in():
            return redirect(url_for('login'))
        user_name = session.get('user_name', 'Default User')        
        user_status = session.get('user_status', 'active')
        return render_template('addressbook.html', user_name=user_name,user_status=user_status)

    

    @app.route('/run-scraper', methods=['POST'])
    def run_scraper():
        if not is_logged_in():
            return redirect(url_for('login'))
        user = clientUser.query.get(session['user_id'])
        if user.permission_level != 'Admin':
            flash('Scraper not in service right now.', 'danger')
            return redirect(url_for('address_book'))
        try:
            # Trigger the Scrapy spider using subprocess
            # Ensure the spider is configured to fetch URLs from the database and save data back to it
            subprocess.run(['scrapy', 'crawl', 'business_info'], cwd='business_scraper')

            # Optional: Implement any post-scraping logic if necessary
            # after_scraping()

            return jsonify({'message': 'Scraping in progress...'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

   
        
    @app.route('/scraping-status')
    def scraping_status():
        if not is_logged_in():
            return redirect(url_for('login'))
        progress = get_scraping_progress()  # Function to get current progress
        return jsonify({'progress': progress})

    def get_scraping_progress():
        try:
            with open(PROGRESS_FILE_PATH, 'r') as file:
                progress = file.read().strip()
                return int(float(progress))  # Convert the progress to a float and then to an integer
        except ValueError as e:
            print(f"Error reading progress file: {e}")
            return 0  # Return 0 if there's an error converting to float
        except Exception as e:
            print(f"Error: {e}")
            return 0  # Return 0 for any other errors

    @app.route('/get-saved-templates', methods=['GET'])
    def get_saved_templates():
        if not is_logged_in():
            return redirect(url_for('login'))
        templates = EmailTemplate.query.all()
        return jsonify([{'id': template.id, 'name': template.template_name} for template in templates])

    
    @app.route('/get-template/<int:template_id>', methods=['GET'])
    def get_template(template_id):
        if not is_logged_in():
            return redirect(url_for('login'))
        template = EmailTemplate.query.get(template_id)
        if template:
            return jsonify({'name': template.template_name, 'subject': template.subject_content, 'body': template.body_content})
        return jsonify({'error': 'Template not found'}), 404
    
    

    @app.route('/send-emails', methods=['POST'])
    def send_emails():
        if not is_logged_in():
            return redirect(url_for('login'))
        data = request.json
        email_addresses = data['emailAddresses']
        subject = data['subject']
        body = data['body']

        try:
            server = smtplib.SMTP('smtp.example.com', 587)  # Replace with your SMTP server details
            server.starttls()
            server.login('your-email@example.com', 'your-password')  # Use your SMTP credentials

            for email in email_addresses:
                message = f"Subject: {subject}\n\n{body}"
                server.sendmail('your-email@example.com', email, message)

            server.quit()
            return jsonify({'status': 'success', 'message': 'Emails sent successfully.'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})

    @app.route('/admin')
    def admin():
        if 'user_id' not in session:
            flash('Please log in to access the Admin page.', 'danger')
            return redirect(url_for('login'))


        user=session['user_permission']
        if user != 'Admin':
            flash('You do not have permission to access the Admin page.', 'danger')
            return redirect(url_for('home'))


        users = fetchClientUsers(1,1,)
        print(users)
        return render_template('admin.html', users=users)
    

    @app.route('/api/delete-user', methods=['POST'])
    def delete_user():
        if session['user_permission'] != 'Admin':
            return jsonify({'error': 'Unauthorized access'}), 403

        # Change to request.args if user_id is sent as a query parameter
        user_id = request.args.get('user_id', type=int)

        if user_id is None:
            return jsonify({'error': 'User ID is missing'}), 400

        try:
            delete_userClient(user_id)
            return redirect(url_for('admin'))

        except Exception as e:
            print(e)  # Log the error for debugging
            return jsonify({'error': 'User not found or deletion failed'}), 404


    
    @app.route('/api/update-user', methods=['POST'])
    def update_user():
        if session['user_permission'] != 'Admin':
            return jsonify({'error': 'Unauthorized access'}), 403

        user_id = request.form.get('user_id', type=int)
        column = request.form.get('column')
        value = request.form.get('value')

        try:
            update_userClient(user_id, column, value)
            return redirect(url_for('admin'))  # Redirect to /admin route 
        except Exception as e:
            # Log the exception e
            return jsonify({'error': 'An error occurred'}), 404
        
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')
        

    def run_one_off_dyno(query):
        # Your Heroku API key, stored securely as an environment variable
        HEROKU_API_KEY = os.environ['HEROKU_API_KEY']
        r = redis.Redis.from_url(os.getenv('REDISCLOUD_URL'))

        
        # The name of your Heroku app
        app_name = "iemissary"
        
        # Serialize and store the query in Redis
        query_key = "query_for_offload"
        r.set(query_key, json.dumps(query))
        
        # Command 
        dyno_command = f"python offLoad.py"
        
        # Connect to Heroku with your API key
        heroku_conn = heroku3.from_key(HEROKU_API_KEY)
        
        # Fetch the app
        app = heroku_conn.apps()[app_name]
        
        # Run a one-off dyno with the specified command
        # Note: Adjust the size according to your needs or omit for default size
        dyno = app.run_command_detached(dyno_command, size="Performance-L")        #, size="Performance-L"
        print(f"One-off dyno {dyno.id} created: {dyno_command}")


    def listen_for_redis_messages():
        r = redis.Redis.from_url(os.getenv('REDISCLOUD_URL'))
        pubsub = r.pubsub()
        pubsub.subscribe('geojson_channel')
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                # Check for a special "complete" message
                if message['data'] == b'COMPLETE':
                    # Emitting 'complete' event to signal the end of data transmission
                    socketio.emit('complete', {})
                    break  # Optionally break if no more messages are expected
                else:
                    # Emitting regular GeoJSON data to clients
                    socketio.emit('geojson_data', {'data': message['data']})


    @app.route('/fetch-geojson', methods=['POST'])
    def fetch_geojson():
        if not is_logged_in():
            return redirect(url_for('login'))

        try:
            data = request.json
            keywords = data['keywords']
            exclusion_words = data.get('exclusionWords', '')
            bbox = tuple(data['bbox'])

            # Validate bbox length
            if len(bbox) != 4:
                app.logger.error(f"Invalid bbox length: {len(bbox)}")
                return jsonify({'error': 'Invalid bounding box dimensions'}), 400

            # Construct DuckDB query
            query = construct_query(keywords, exclusion_words, bbox)
            
            # Starting the one-off dyno in a separate thread
            threading.Thread(target=run_one_off_dyno, args=(query,)).start()
            
            # Starting the Redis listener in a separate thread
            threading.Thread(target=listen_for_redis_messages).start()

            # Acknowledging the request; data will be streamed via WebSocket
            return jsonify({'status': 'data_processing_started'})

        except Exception as e:
            return jsonify({'error': str(e)}), 500


    @app.route('/check-task/<task_id>', methods=['GET'])
    def check_task(task_id):
        task = execute_query_and_fetch_data.AsyncResult(task_id)
        if task.state == 'PENDING':
            # Task is still running
            return jsonify({'status': 'pending'}), 202
        elif task.state == 'SUCCESS':
            # Task completed successfully
            return jsonify({'status': 'completed', 'result': task.result})
        elif task.state == 'FAILURE':
            # Task failed
            return jsonify({'status': 'failed', 'error': str(task.info)}), 500
        else:
            # Task is in an unknown state
            return jsonify({'status': 'unknown'}), 202

            
    

    

    @app.route('/get_categories', methods=['GET'])
    def get_categories():
        # Load the JSON file
        with open('files/keywordcat.json', 'r') as json_file:
            keywordcat_data = json.load(json_file)

        # Extract the categories
        categories = list(set(keywordcat_data.values()))

        # Return the categories as JSON
        return jsonify(categories=categories)

    # Define a route to fetch keywords based on selected categories
    @app.route('/get_keywords', methods=['POST'])
    def get_keywords():
        # Load the JSON file
        with open('files/keywordcat.json', 'r') as json_file:
            keywordcat_data = json.load(json_file)
        # Get the selected categories from the frontend (sent as JSON)
        selected_categories = request.json.get('categories', [])

        # Filter keywords based on selected categories
        filtered_keywords = [keyword for keyword, category in keywordcat_data.items() if category in selected_categories]

        # Return the filtered keywords as JSON
        return jsonify(keywords=filtered_keywords)

    @app.route('/gif/<filename>')
    def serve_gif(filename):
        return send_from_directory('files', filename)
    @app.route('/geojson/<filename>')
    def serve_geojson(filename):
        print('server request for geojson received')
        return send_from_directory('files', filename)
    
        
    @app.route('/fetch-temp-geojson')
    def fetch_temp_geojson():
        temp_file_path = 'files/output.geojson.tmp'
        main_file_path = 'files/output.geojson'
        state = SingletonState()  # Get the singleton instance

        geojson_header = ('{'+'\n'+'"type": "FeatureCollection",'+'\n' '"features": ['+'\n')
        final_header = ('{ "type": "FeatureCollection", "features": [')

        title = f"last_read_position: {state.last_read_position}, is_new_read: {state.is_new_read}"

        if not os.path.exists(temp_file_path):
            new_data =  ''
            with open(main_file_path, 'r') as file:
                file.seek(state.last_read_position)
                new_data = file.read()
                state.last_read_position = 0
                state.base_position = 149
                state.is_new_read = True  # Reset when the file does not exist

            complete_data = final_header + new_data
            return make_response(jsonify(complete_data), 404)

        try:
            new_data = ''
            with open(temp_file_path, 'r') as file:
                file.seek(state.last_read_position)
                new_data = file.read()
                state.last_read_position = file.tell()
                if state.last_read_position > state.base_position:
                    state.last_read_position += 1
                    state.base_position = state.last_read_position
                
            if state.is_new_read:
                completed_json = new_data
                state.is_new_read = False  
            else:
                completed_json = geojson_header + new_data

            if not completed_json.endswith(']}'):
                completed_json += ']}'
            
            # Open the file in append mode ('a') to add the title and the data
            with open('files/output.txt', 'a') as file:
                # Write the title first
                file.write(title + '\n')
                
                # Write the completed_json data
                data = completed_json
                file.write(data)

            geojson_data = json.loads(data)
            return jsonify(geojson_data)

        except Exception as e:
            return jsonify({"error": "Invalid JSON format or other error: " + str(e)}), 500
        
    @app.route('/save-to-contacts', methods=['POST'])
    def save_to_contacts():
        if not is_logged_in():
            return redirect(url_for('login'))
        
        data = request.get_json()
        if data:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'status': 'error', 'message': 'User ID not found in session'}), 401

            s3_client = boto3.client('s3')
            bucket_name = 'emissarybucket'
            object_key = f'records/userData/{user_id}/contacts.parquet'

            try:
                # Attempt to check if the object exists
                s3_client.head_object(Bucket=bucket_name, Key=object_key)
                file_exists = True
            except s3_client.exceptions.ClientError as e:
                # The object does not exist, file_exists is False
                if e.response['Error']['Code'] == '404':
                    file_exists = False
                else:
                    # Other errors (e.g., permission issues, etc.)
                    raise

            if not file_exists:
                # Create an empty DataFrame with specified columns
                df = pd.DataFrame(columns=['id', 'name', 'category', 'website', 'socials', 'phone', 'address'])

                # Convert DataFrame to a Parquet file in memory
                buffer = BytesIO()
                df.to_parquet(buffer, index=False)

                # Reset buffer position to the beginning
                buffer.seek(0)

                # Upload the Parquet file to S3
                s3_client.upload_fileobj(Fileobj=buffer, Bucket=bucket_name, Key=object_key)
                print(f"New contacts.parquet file created at s3://{bucket_name}/{object_key}")

             # Now, call save_contact with the data and user_id
            success = save_contact(data, user_id)
            if success:
                return jsonify({'status': 'success', 'message': 'Contacts saved successfully'}), 200
            else:
                return jsonify({'status': 'error', 'message': 'Failed to save contacts'}), 500
        else:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400

    @app.route('/load-contacts', methods=['GET'])
    def load_contacts():
        # Assuming you have a function is_logged_in() to check user login status
        if not is_logged_in():
            return redirect(url_for('login'))
        
        user_id = session.get('user_id')
        if user_id is None:
            return jsonify({'error': 'User not logged in'}), 401
        
        # Optional: Retrieve query parameters for filtering
        key = request.args.get('key')
        value = request.args.get('value')
        
        data = fetch_contacts(user_id, key, value)
        return jsonify(data), 200

    @app.route('/delete-contacts', methods=['POST'])
    def route_delete_contacts():
        if 'user_id' not in session:
            # User not logged in or session expired
            return jsonify({'status': 'error', 'message': 'User not authenticated'}), 401

        # Extract user_id from session
        user_id = session['user_id']

        # Get JSON data from request
        data = request.get_json()
        if data is None or 'ids' not in data:
            return jsonify({'status': 'error', 'message': 'Invalid request'}), 400

        # Extract contact IDs to delete
        contact_ids = data['ids']

        # Call the delete_contacts function
        try:
            delete_contacts(contact_ids, user_id)
            return jsonify({'status': 'success', 'message': 'Contacts deleted successfully'}), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
        
    @app.route('/county-data', methods=['GET'])
    def get_county_data():
        return jsonify(county_data)
        
            # Additional routes....
