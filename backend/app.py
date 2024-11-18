from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS
import logging
from werkzeug.security import generate_password_hash, check_password_hash

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Set up CORS
CORS(app, supports_credentials=True)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:yourpassword@localhost/happy_tails'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

# Initialize extensions
db = SQLAlchemy(app)

# Model definitions
class Pet(db.Model):
    __tablename__ = 'pet'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=False)
    health_status = db.Column(db.String(100), nullable=False)
    vaccination_status = db.Column(db.String(100), nullable=False)
    adoption_status = db.Column(db.String(20), default='Available')

class Adopter(db.Model):
    __tablename__ = 'adopter'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.String(100), nullable=False)
    preferences = db.Column(db.String(200), nullable=True)

class AdoptionApplication(db.Model):
    __tablename__ = 'adoption_application'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    adopter_id = db.Column(db.Integer, db.ForeignKey('adopter.id'), nullable=False)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')

class Volunteer(db.Model):
    __tablename__ = 'volunteer'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.String(100), nullable=False)
    skills = db.Column(db.String(200), nullable=True)
    availability = db.Column(db.String(100), nullable=True)

class VolunteerSchedule(db.Model):
    __tablename__ = 'volunteer_schedule'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    volunteer_id = db.Column(db.Integer, db.ForeignKey('volunteer.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(50), nullable=False)
    task = db.Column(db.String(200), nullable=False)

# API Endpoints
@app.route('/pets', methods=['GET', 'POST'])
def handle_pets():
    if request.method == 'POST':
        data = request.json
        new_pet = Pet(
            name=data['name'],
            species=data['species'],
            breed=data.get('breed'),
            age=data['age'],
            health_status=data['health_status'],
            vaccination_status=data['vaccination_status']
        )
        db.session.add(new_pet)
        db.session.commit()
        return jsonify({"message": "Pet added successfully"}), 201
    else:
        pets = Pet.query.all()
        return jsonify([pet.to_dict() for pet in pets]), 200

@app.route('/adopters', methods=['GET', 'POST'])
def handle_adopters():
    if request.method == 'POST':
        data = request.json
        new_adopter = Adopter(
            name=data['name'],
            contact_info=data['contact_info'],
            preferences=data.get('preferences')
        )
        db.session.add(new_adopter)
        db.session.commit()
        return jsonify({"message": "Adopter added successfully"}), 201
    else:
        adopters = Adopter.query.all()
        return jsonify([adopter.to_dict() for adopter in adopters]), 200

# Additional endpoints for AdoptionApplication, Volunteer, and VolunteerSchedule would follow a similar pattern

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)