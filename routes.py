#routes.py
from flask import render_template, request, jsonify, url_for, session, redirect, flash, send_from_directory, make_response
from models import Place, EmailTemplate, clientUser
#from shared import db
from flask import current_app  # Import at the top of your file
import subprocess
import smtplib
import os
from werkzeug.security import check_password_hash, generate_password_hash
import duckdb
import json
import logging
from dotenv import load_dotenv
from queryBuilders import construct_query, fetch_userClient_query, add_userClient, delete_userClient, update_userClient
from duckQueries import execute_query_and_fetch_data, execute_query_and_fetch_clientUser, execute_query_and_fetch_clientUsers

load_dotenv()


# Configure Python's logging
logging.basicConfig(level=logging.DEBUG)

PROGRESS_FILE_PATH = 'business_scraper/progress.txt'
aws_access_key_id = os.environ.get('YOUR_ACCESS_KEY')
aws_secret_access_key = os.environ.get('YOUR_SECRET_KEY')
aws_default_region = os.environ.get('AWS_DEFAULT_REGION')
place_location = os.environ.get('PLACE_FOLDER')
records_location=os.environ.get('RECORDS_FOLDER')

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

            if user.user_status!= 'active':
                flash('Your account is not active. Please contact the administrator.')
                return render_template('login.html')

            session['user_id'] = user.id
            session['user_permission'] = user.permission_level

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
        return render_template('index.html', user_name=user_name)
    
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
        return render_template('addressbook.html')

    

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
        

    @app.route('/fetch-geojson', methods=['POST'])
    def fetch_geojson():
        if not is_logged_in():
            return redirect(url_for('login'))

        try:
            # Extract user inputs from the form
            data = request.json
            keywords = data['keywords']
            exclusion_words = data['exclusionWords']
            bbox = tuple(data['bbox'])

            # Validate bbox length
            if len(bbox) != 4:
                app.logger.error(f"Invalid bbox length: {len(bbox)}")
                return jsonify({'error': 'Invalid bounding box dimensions'}), 400

            # Construct DuckDB query
            query = construct_query(keywords, exclusion_words, bbox)

            # Fetch GeoJSON data
            geojson_data = execute_query_and_fetch_data(query)
            if geojson_data is None:
                return jsonify({'error': 'Error fetching data'}), 500

            # Return the GeoJSON data
            return jsonify(geojson_data)

        except Exception as e:
            app.logger.error(f"Error in fetch_geojson: {str(e)}")
            return jsonify({'error': str(e)}), 500
        
    

    

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
            print(complete_data)
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

        # Additional routes....




        """def construct_query(keywords, exclusion_words, bbox):
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
        query = finsert triple quotes here!
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
       insert triple quotes here!
        print(query)
        return query"""