#routes.py
from flask import render_template, request, jsonify, url_for, session, redirect, flash
import requests
#from config import GOOGLE_MAPS_API_KEY
from models import Place, EmailTemplate, clientUser
from shared import db
from flask import current_app  # Import at the top of your file
import subprocess
import smtplib
import os
from werkzeug.security import check_password_hash, generate_password_hash



PROGRESS_FILE_PATH = 'business_scraper/progress.txt'

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

            new_user = clientUser(first_name=first_name, last_name=last_name, email=email, permission_level='standard')
            new_user.set_password(password)  # Set the password using the set_password method
            db.session.add(new_user)
            db.session.commit()

            flash('Account created successfully!')
            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])

    def login():
        if request.method == 'POST':
            email = request.form['exampleInputEmail']
            password = request.form['exampleInputPassword']
            user = clientUser.query.filter_by(email=email).first()

            # Check if user exists and password is correct
            if user and user.check_password(password):
                # Check if user status is 'Active'
                if user.status == 'Active':
                    session['user_id'] = user.id
                    return redirect(url_for('home'))
                else:
                    flash('Your account is not active. Please contact the administrator.')
            else:
                flash('Invalid email or password')
        
        return render_template('login.html')

    
    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        return redirect(url_for('login'))
    

    @app.route('/')
    def home():
        if not is_logged_in():
            return redirect(url_for('login'))
        google_maps_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        return render_template('index.html', google_maps_api_key=google_maps_api_key)
    
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

        
    @app.route('/add-place', methods=['POST'])
    def add_place():
        if not is_logged_in():
            return redirect(url_for('login'))
        try:
            data = request.get_json()
            new_place = Place(
                name=data.get('name'),
                coordinates=data.get('coordinates'),
                website=data.get('website', ''),
                formatted_address=data.get('formatted_address', ''),
                category=data.get('category', 'Default Category'),
                status=data.get('status', 'Pending Approval')
            )
            db.session.add(new_place)
            db.session.commit()
            return jsonify({"message": "Place added successfully"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/update-place/<int:place_id>', methods=['PUT'])
    def update_place(place_id):
        if not is_logged_in():
            return redirect(url_for('login'))
        data = request.get_json()
        place = Place.query.get(place_id)
        if not place:
            return jsonify({'error': 'Place not found'}), 404
        # Update place data
        place.category = data.get('category', place.category)
        place.status = data.get('status', place.status)
        db.session.commit()
        return jsonify({'message': 'Place updated successfully'}), 200


    @app.route('/save-places', methods=['POST'])
    def save_places():
        if not is_logged_in():
            return redirect(url_for('login'))
        data = request.get_json()
        for place in data:
            print("Place being saved:", place)  # Print the place data

            # Extract formatted_address along with other fields
            formatted_address = place.get('formatted_address', '')

            # Check if the place has a website value
            if 'website' in place and place['website'] not in [None, '', 'No website']:
                existing_place = Place.query.filter_by(name=place['name']).first()
                if not existing_place:
                    # Create a new place with the formatted_address
                    new_place = Place(name=place['name'], coordinates=place['coordinates'], website=place['website'],
                                    formatted_address=formatted_address)
                    db.session.add(new_place)
                else:
                    # Update the existing place if the name already exists
                    existing_place.coordinates = place['coordinates']
                    existing_place.website = place['website']
                    existing_place.formatted_address = formatted_address  # Update formatted_address
            else:
                # Logic for handling cases where there is no website
                pass

        db.session.commit()
        return 'Data processed successfully', 200


    
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




    @app.route('/addressbook')
    def address_book():
        if not is_logged_in():
            return redirect(url_for('login'))
        return render_template('addressbook.html')

    @app.route('/delete-place/<int:place_id>', methods=['DELETE'])
    def delete_place(place_id):
        if not is_logged_in():
            return redirect(url_for('login'))
        try:
            place = Place.query.get_or_404(place_id)

            # Check if the place has an associated contact
            if place.contact:
                # Delete the contact associated with this place
                db.session.delete(place.contact)

            # After handling the contact, delete the place
            db.session.delete(place)
            db.session.commit()

            return jsonify({'message': 'Place deleted successfully'}), 200
        except Exception as e:
            db.session.rollback()  # Roll back in case of error
            current_app.logger.error(f"Error deleting place: {e}")  # Log the error for debugging
            return jsonify({'error': 'Internal Server Error'}), 500

    @app.route('/run-scraper', methods=['POST'])
    def run_scraper():
        if not is_logged_in():
            return redirect(url_for('login'))
        try:
            # Trigger the Scrapy spider using subprocess
            # Ensure the spider is configured to fetch URLs from the database and save data back to it
            subprocess.run(['scrapy', 'crawl', 'business_info'], cwd='business_scraper')

            # Optional: Implement any post-scraping logic if necessary
            # after_scraping()

            return jsonify({'message': 'Scraping in progress...'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/delete-places', methods=['POST'])
    def delete_places():
        if not is_logged_in():
            return redirect(url_for('login'))
        try:
            place_ids = request.get_json()
            Place.query.filter(Place.id.in_(place_ids)).delete(synchronize_session=False)
            db.session.commit()
            return jsonify({'message': 'Places deleted successfully'}), 200
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

    @app.route('/save-template', methods=['POST'])
    def save_template():
        if not is_logged_in():
            return redirect(url_for('login'))
        data = request.json
        new_template = EmailTemplate(template_name=data['name'], subject_content=data['subject'], body_content=data['body'])
        db.session.add(new_template)
        db.session.commit()
        return jsonify({'message': 'Template saved successfully', 'id': new_template.id})

    @app.route('/get-template/<int:template_id>', methods=['GET'])
    def get_template(template_id):
        if not is_logged_in():
            return redirect(url_for('login'))
        template = EmailTemplate.query.get(template_id)
        if template:
            return jsonify({'name': template.template_name, 'subject': template.subject_content, 'body': template.body_content})
        return jsonify({'error': 'Template not found'}), 404
    
    @app.route('/delete-template/<int:template_id>', methods=['DELETE'])
    def delete_template(template_id):
        if not is_logged_in():
            return redirect(url_for('login'))
        template = EmailTemplate.query.get(template_id)
        if template:
            db.session.delete(template)
            db.session.commit()
            return jsonify({'message': 'Template deleted successfully'})
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

        user = clientUser.query.get(session['user_id'])
        if user.permission_level != 'Admin':
            flash('You do not have permission to access the Admin page.', 'danger')
            return redirect(url_for('home'))


        users = clientUser.query.all()
        return render_template('admin.html', users=users)
    
    @app.route('/update-user/<int:user_id>', methods=['POST'])
    def update_user(user_id):
        if 'user_id' not in session:
            flash('Please log in to access the Admin page.', 'danger')
            return redirect(url_for('login'))

        logged_in_user = clientUser.query.get(session['user_id'])
        if logged_in_user.permission_level != 'Admin':
            flash('You do not have permission to access the Admin page.', 'danger')
            return redirect(url_for('home'))
        
        user_to_update = clientUser.query.get(user_id)
        if user_to_update:
            user_to_update.email = request.form.get('email')
            user_to_update.permission_level = request.form.get('permission_level')
            user_to_update.status = request.form.get('status')

            try:
                db.session.commit()
                flash("User updated successfully.", "success")
            except Exception as e:
                db.session.rollback()  # Rollback in case of error
                flash(str(e), "danger")  # Show error message
        else:
            flash("User not found.", "warning")

        return redirect(url_for('admin'))



# Additional routes...