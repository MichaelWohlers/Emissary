#models.py
from shared import db
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy.orm import joinedload

class Place(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    coordinates = db.Column(db.String(255), nullable=False)
    website = db.Column(db.String(255))
    formatted_address = db.Column(db.String(255))
    category = db.Column(db.String(255))
    status = db.Column(db.String(255), default='Pending Approval')

    # Ensure only one contact per place with uselist=False
    contact = db.relationship('Contact', backref='place', uselist=False, lazy='joined')

    def __repr__(self):
        return f'<Place {self.name}>'

    def to_dict(self):
        # Check if contact exists and adjust the dictionary accordingly
        contact_data = self.contact.to_dict() if self.contact else {'email': 'none', 'phone_number': 'none'}
        return {
            "id": self.id,
            "name": self.name,
            "website": self.website,
            "formatted_address": self.formatted_address,
            "category": self.category,
            "status": self.status,
            "contact_email": contact_data['email'],
            "contact_phone_number": contact_data['phone_number']
        }

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    contact_name = db.Column(db.String(255), nullable=True)
    contact_title = db.Column(db.String(255), nullable=True)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=False, unique=True)

    def __repr__(self):
        return f'<Contact {self.email}>'
        
    def to_dict(self):
        return {
            "email": self.email or 'none',
            "phone_number": self.phone_number or 'none',
            "contact_name": self.contact_name or 'none',
            "contact_title": self.contact_title or 'none'
        }


class EmailTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_name = db.Column(db.String(255), nullable=False)
    subject_content = db.Column(db.Text, nullable=False)
    body_content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<EmailTemplate {self.template_name}>'
    def to_dict(self):
        return {
            'id': self.id,
            'template_name': self.template_name,
            'subject_content': self.subject_content,
            'body_content': self.body_content
        }

class BlockedSite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(255), nullable=False)
    site_website = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<BlockedSite {self.site_name}>'
    def to_dict(self):
        return {
            'id': self.id,
            'site_name': self.site_name,
            'site_website': self.site_website
        }

class SavedKeyword(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<SavedKeyword {self.keyword}>'
    def to_dict(self):
        return {
            'id': self.id,
            'keyword': self.keyword
        }

class clientUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)
    permission_level = db.Column(db.String(50), nullable=False, default='standard')
    status = db.Column(db.String(50), nullable=False, default='Pending Approval')
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        return f'<clientUser {self.email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'permission_level': self.permission_level,
            'status': self.status
        }
    
#create class dataset including named sets of keywords and exclusion words with relation to data
#create class data including geojson data saved marker coordinates, relation to datasets many to many
#create class exclusion keywords related to datasets many to mana