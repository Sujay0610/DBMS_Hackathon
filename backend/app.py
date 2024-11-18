from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS
import logging
from sqlalchemy import text, func, create_engine, DECIMAL
from datetime import timedelta

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Set up CORS
CORS(app, supports_credentials=True)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:sujay123@localhost/happy_tails'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

# Initialize extensions
db = SQLAlchemy(app)

# Model definitions
class Pet(db.Model):
    __tablename__ = 'pet'
    pet_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(50))
    age = db.Column(db.Integer)
    weight = db.Column(DECIMAL(8, 2))
    health_condition = db.Column(db.String(20))
    vaccination_status = db.Column(db.String(20), default='Not Vaccinated')
    vaccination_due_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Available')
    last_updated = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint('age >= 0', name='check_age_positive'),
        db.CheckConstraint('weight > 0 AND weight <= 2000', name='check_weight_range'),
        db.CheckConstraint("health_condition IN ('Good', 'Fair', 'Poor', 'Underweight')", 
                          name='check_health_condition'),
        db.CheckConstraint("vaccination_status IN ('Vaccinated', 'Not Vaccinated')",
                          name='check_vaccination_status'),
        db.CheckConstraint("status IN ('Available', 'Adopted', 'In Review', 'High Demand', 'Not Available')",
                          name='check_status')
    )

    def to_dict(self):
        return {
            'pet_id': self.pet_id,
            'name': self.name,
            'breed': self.breed,
            'age': self.age,
            'weight': float(self.weight) if self.weight else None,
            'health_condition': self.health_condition,
            'vaccination_status': self.vaccination_status,
            'vaccination_due_date': self.vaccination_due_date.isoformat() if self.vaccination_due_date else None,
            'status': self.status,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class Adopter(db.Model):
    __tablename__ = 'adopter'
    adopter_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.String(100), nullable=False)

    __table_args__ = (
        db.CheckConstraint('LENGTH(full_name) >= 2', name='check_name_length'),
        db.CheckConstraint('LENGTH(contact_info) >= 5', name='check_contact_info_length'),
    )

    def to_dict(self):
        return {
            'adopter_id': self.adopter_id,
            'full_name': self.full_name,
            'contact_info': self.contact_info
        }

class AdoptionApplication(db.Model):
    __tablename__ = 'adoption_application'
    application_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.pet_id'), nullable=False)
    adopter_id = db.Column(db.Integer, db.ForeignKey('adopter.adopter_id'), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    application_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint("status IN ('Pending', 'Approved', 'Rejected')", name='check_application_status'),
    )

    def to_dict(self):
        return {
            'application_id': self.application_id,
            'pet_id': self.pet_id,
            'adopter_id': self.adopter_id,
            'status': self.status,
            'application_date': self.application_date.isoformat()
        }

class AdoptionRecord(db.Model):
    __tablename__ = 'adoption_record'
    adoption_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.pet_id'), nullable=False)
    adopter_id = db.Column(db.Integer, db.ForeignKey('adopter.adopter_id'), nullable=False)
    adoption_date = db.Column(db.Date, nullable=False)

    def to_dict(self):
        return {
            'adoption_id': self.adoption_id,
            'pet_id': self.pet_id,
            'adopter_id': self.adopter_id,
            'adoption_date': self.adoption_date.isoformat()
        }

class Volunteer(db.Model):
    __tablename__ = 'volunteer'
    volunteer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.String(100))
    skills = db.Column(db.String(255))
    availability = db.Column(db.String(20))
    last_assigned_date = db.Column(db.Date, nullable=True)

    __table_args__ = (
        db.CheckConstraint("availability IN ('Weekdays', 'Weekends', 'Flexible')", name='check_volunteer_availability'),
    )

    def to_dict(self):
        return {
            'volunteer_id': self.volunteer_id,
            'full_name': self.full_name,
            'contact_info': self.contact_info,
            'skills': self.skills,
            'availability': self.availability,
            'last_assigned_date': self.last_assigned_date.isoformat() if self.last_assigned_date else None
        }

class VolunteerSchedule(db.Model):
    __tablename__ = 'volunteer_schedule'
    schedule_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    volunteer_id = db.Column(db.Integer, db.ForeignKey('volunteer.volunteer_id'), nullable=False)
    shift_date = db.Column(db.Date, nullable=False)
    task_description = db.Column(db.String(255))

    def to_dict(self):
        return {
            'schedule_id': self.schedule_id,
            'volunteer_id': self.volunteer_id,
            'shift_date': self.shift_date.isoformat(),
            'task_description': self.task_description
        }

class VolunteerAudit(db.Model):
    __tablename__ = 'volunteer_audit'
    audit_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    volunteer_id = db.Column(db.Integer, db.ForeignKey('volunteer.volunteer_id'), nullable=False)
    shift_date = db.Column(db.Date, nullable=False)
    update_timestamp = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def to_dict(self):
        return {
            'audit_id': self.audit_id,
            'volunteer_id': self.volunteer_id,
            'shift_date': self.shift_date.isoformat(),
            'update_timestamp': self.update_timestamp.isoformat()
        }

def create_database():
    try:
        engine = create_engine('mysql+pymysql://root:sujay123@localhost/')
        with engine.connect() as conn:
            conn.execute(text("CREATE DATABASE IF NOT EXISTS happy_tails"))
            logger.info("Database 'happy_tails' created or already exists")
    except Exception as e:
        logger.error(f"Error creating database: {str(e)}")
        raise e

def init_db():
    try:
        # Drop all tables first to avoid conflicts
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise e

def init_functions():
    try:
        with db.engine.connect() as conn:
            # Drop existing function if it exists
            conn.execute(text("DROP FUNCTION IF EXISTS calculate_popularity_score"))
            
            # Create the function
            conn.execute(text("""
                CREATE FUNCTION calculate_popularity_score(
                    p_breed VARCHAR(50),
                    p_age INT,
                    p_pending_applications INT
                )
                RETURNS INT
                DETERMINISTIC
                BEGIN
                    DECLARE score INT DEFAULT 50;
                    IF p_breed IN ('Labrador', 'Beagle', 'German Shepherd') THEN
                        SET score = score + 20;
                    END IF;
                    IF p_age < 3 THEN
                        SET score = score + 10;
                    END IF;
                    SET score = score + (p_pending_applications * 5);
                    RETURN score;
                END
            """))
            logger.info("Functions initialized successfully")
    except Exception as e:
        logger.error(f"Error creating functions: {str(e)}")
        raise e

def init_procedures():
    try:
        with db.engine.connect() as conn:
            # Drop existing procedure if it exists
            conn.execute(text("DROP PROCEDURE IF EXISTS update_vaccination_status"))
            
            # Create the procedure
            conn.execute(text("""
                CREATE PROCEDURE update_vaccination_status()
                BEGIN
                    DECLARE updated_count INT;
                    UPDATE pet
                    SET health_condition = 'Needs Vaccination',
                        last_updated = CURRENT_TIMESTAMP
                    WHERE last_updated < DATE_SUB(CURRENT_DATE, INTERVAL 6 MONTH)
                    AND health_condition != 'Needs Vaccination';
                    SELECT ROW_COUNT() INTO updated_count;
                    SELECT updated_count AS pets_updated;
                END
            """))
            logger.info("Procedures initialized successfully")
    except Exception as e:
        logger.error(f"Error creating procedures: {str(e)}")
        raise e

def init_triggers():
    try:
        with db.engine.connect() as conn:
            # Drop existing trigger if it exists
            conn.execute(text("DROP TRIGGER IF EXISTS update_status_based_on_health"))
            
            # Create the trigger
            conn.execute(text("""
                CREATE TRIGGER update_status_based_on_health
                BEFORE UPDATE ON pet
                FOR EACH ROW
                BEGIN
                    IF NEW.health_condition IN ('Underweight', 'Poor') THEN
                        SET NEW.status = 'Not Available';
                    ELSEIF NEW.health_condition = 'Good' THEN
                        SET NEW.status = 'Available';
                    END IF;
                    SET NEW.last_updated = CURRENT_TIMESTAMP;
                END
            """))
            logger.info("Triggers initialized successfully")
    except Exception as e:
        logger.error(f"Error creating triggers: {str(e)}")
        raise e

def setup_federated_connection():
    try:
        with db.engine.connect() as conn:
            # Enable federated storage engine
            conn.execute(text("SET GLOBAL federated = 1"))
            
            # Create federated server connection
            conn.execute(text("""
                CREATE SERVER IF NOT EXISTS remote_server
                FOREIGN DATA WRAPPER mysql
                OPTIONS (
                    HOST 'remote_host',
                    DATABASE 'happy_tails_remote',
                    USER 'remote_user',
                    PASSWORD 'remote_password'
                )
            """))

            # Create federated pet health table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS pet_health_federated (
                    pet_id INT PRIMARY KEY,
                    health_condition VARCHAR(20),
                    last_updated TIMESTAMP,
                    INDEX (pet_id)
                )
                ENGINE=FEDERATED
                CONNECTION='remote_server/pet_health'
            """))
            logger.info("Federated connection setup successfully")
    except Exception as e:
        logger.error(f"Error setting up federated connection: {str(e)}")
        raise e

def setup_remote_database():
    try:
        # Create remote database engine
        remote_engine = create_engine('mysql+pymysql://root:sujay123@localhost/happy_tails_remote')
        
        # Create remote database
        with create_engine('mysql+pymysql://root:sujay123@localhost/').connect() as conn:
            conn.execute(text("CREATE DATABASE IF NOT EXISTS happy_tails_remote"))
        
        # Create remote table
        with remote_engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS pet_health (
                    pet_id INT PRIMARY KEY,
                    health_condition VARCHAR(20),
                    last_updated TIMESTAMP,
                    INDEX (pet_id)
                )
            """))
        logger.info("Remote database setup successfully")
    except Exception as e:
        logger.error(f"Error setting up remote database: {str(e)}")
        raise e

# API Endpoints
@app.route('/pets', methods=['GET', 'POST'])
def handle_pets():
    if request.method == 'POST':
        try:
            data = request.json
            
            # Validate weight
            weight = float(data['weight'])
            if weight <= 0 or weight > 2000:
                return jsonify({"error": "Weight must be between 0 and 2000 kg"}), 400
                
            # Validate age
            age = int(data['age'])
            if age < 0:
                return jsonify({"error": "Age cannot be negative"}), 400

            new_pet = Pet(
                name=data['name'],
                breed=data.get('breed'),
                age=age,
                weight=weight,
                health_condition=data['health_condition'],
                status=data['status']
            )
            db.session.add(new_pet)
            db.session.commit()
            return jsonify(new_pet.to_dict()), 201
        except ValueError:
            return jsonify({"error": "Invalid number format for age or weight"}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        pets = Pet.query.all()
        return jsonify([pet.to_dict() for pet in pets]), 200

@app.route('/adopters', methods=['GET', 'POST'])
def handle_adopters():
    if request.method == 'POST':
        try:
            data = request.json
            
            # Validate full name length
            if len(data.get('full_name', '')) < 2:
                return jsonify({"error": "Full name must be at least 2 characters long"}), 400
                
            # Validate contact info length
            if len(data.get('contact_info', '')) < 5:
                return jsonify({"error": "Contact info must be at least 5 characters long"}), 400

            new_adopter = Adopter(
                full_name=data['full_name'],
                contact_info=data['contact_info']
            )
            db.session.add(new_adopter)
            db.session.commit()
            
            return jsonify(new_adopter.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding adopter: {str(e)}")
            return jsonify({"error": "Invalid input. Please check the requirements."}), 400
    else:
        adopters = Adopter.query.all()
        return jsonify([adopter.to_dict() for adopter in adopters]), 200

@app.route('/adoption-applications', methods=['GET', 'POST'])
def handle_adoption_applications():
    if request.method == 'POST':
        data = request.json
        new_application = AdoptionApplication(
            pet_id=data['pet_id'],
            adopter_id=data['adopter_id'],
            status=data['status']
        )
        db.session.add(new_application)
        db.session.commit()
        return jsonify({"message": "Adoption application submitted successfully"}), 201
    else:
        applications = AdoptionApplication.query.all()
        return jsonify([application.to_dict() for application in applications]), 200

@app.route('/volunteers', methods=['GET', 'POST'])
def handle_volunteers():
    if request.method == 'POST':
        data = request.json
        new_volunteer = Volunteer(
            full_name=data['full_name'],
            contact_info=data['contact_info'],
            skills=data['skills'],
            availability=data['availability']
        )
        db.session.add(new_volunteer)
        db.session.commit()
        return jsonify({"message": "Volunteer added successfully"}), 201
    else:
        volunteers = Volunteer.query.all()
        return jsonify([volunteer.to_dict() for volunteer in volunteers]), 200

@app.route('/pets/<int:pet_id>/update-health', methods=['PUT'])
def update_pet_health(pet_id):
    try:
        data = request.json
        if not data or 'health_condition' not in data:
            return jsonify({"error": "Health condition is required"}), 400

        valid_conditions = ['Good', 'Fair', 'Poor', 'Needs Vaccination', 'Underweight']
        if data['health_condition'] not in valid_conditions:
            return jsonify({"error": "Invalid health condition"}), 400

        pet = Pet.query.get_or_404(pet_id)
        pet.health_condition = data['health_condition']
        pet.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "message": "Pet health updated successfully",
            "pet": pet.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating pet health: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/pets/update-vaccinations', methods=['POST'])
def update_vaccinations():
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text("CALL update_vaccination_status()"))
            updated_count = result.fetchone()[0]
        return jsonify({"pets_updated": updated_count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/pets/<int:pet_id>/popularity', methods=['GET'])
def get_pet_popularity(pet_id):
    try:
        pet = Pet.query.get_or_404(pet_id)
        pending_applications = AdoptionApplication.query.filter_by(
            pet_id=pet_id, 
            status='Pending'
        ).count()
        
        with db.engine.connect() as conn:
            result = conn.execute(
                text("SELECT calculate_popularity_score(:breed, :age, :apps)"),
                {"breed": pet.breed, "age": pet.age, "apps": pending_applications}
            )
            score = result.scalar()
        
        return jsonify({"popularity_score": score}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/pets/multiple-attempts', methods=['GET'])
def get_multiple_attempts():
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text("""
                WITH RECURSIVE AdoptionAttempts AS (
                    SELECT 
                        pet_id,
                        adoption_date,
                        1 as attempt_count
                    FROM adoption_record
                    
                    UNION ALL
                    
                    SELECT 
                        ar.pet_id,
                        ar.adoption_date,
                        aa.attempt_count + 1
                    FROM adoption_record ar
                    JOIN AdoptionAttempts aa ON ar.pet_id = aa.pet_id
                    WHERE ar.adoption_date > aa.adoption_date
                )
                SELECT 
                    pet_id,
                    MAX(adoption_date) as adoption_date,
                    MAX(attempt_count) as attempt_count
                FROM AdoptionAttempts
                GROUP BY pet_id
                HAVING MAX(attempt_count) > 1
            """))
            attempts = [dict(row) for row in result]
            return jsonify(attempts), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/volunteer-schedules', methods=['GET', 'POST'])
def handle_volunteer_schedules():
    if request.method == 'POST':
        try:
            data = request.json
            
            # Start transaction with READ UNCOMMITTED isolation level
            with db.engine.connect().execution_options(
                isolation_level="READ UNCOMMITTED"
            ) as conn:
                # Check for existing schedule
                result = conn.execute(
                    text("""
                        SELECT COUNT(*) 
                        FROM volunteer_schedule 
                        WHERE volunteer_id = :vid 
                        AND shift_date = :date
                    """),
                    {
                        "vid": data['volunteer_id'],
                        "date": data['shift_date']
                    }
                )
                if result.scalar() > 0:
                    return jsonify({"message": "Volunteer already scheduled for this date"}), 400
                
                # Create new schedule
                new_schedule = VolunteerSchedule(
                    volunteer_id=data['volunteer_id'],
                    shift_date=data['shift_date'],
                    task_description=data['task_description']
                )
                db.session.add(new_schedule)
                db.session.commit()
                
                return jsonify({"message": "Schedule created successfully"}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        schedules = VolunteerSchedule.query.all()
        return jsonify([schedule.to_dict() for schedule in schedules]), 200

@app.route('/pets/<int:pet_id>/update-health-federated', methods=['PUT'])
def update_pet_health_federated(pet_id):
    try:
        data = request.json
        with db.engine.connect() as conn:
            # Update local database
            conn.execute(
                text("""
                    UPDATE pet 
                    SET health_condition = :condition,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE pet_id = :pid
                """),
                {"condition": data['health_condition'], "pid": pet_id}
            )
            
            # Update federated table
            conn.execute(
                text("""
                    UPDATE pet_health_federated 
                    SET health_condition = :condition,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE pet_id = :pid
                """),
                {"condition": data['health_condition'], "pid": pet_id}
            )
            
            return jsonify({"message": "Health updated in both databases"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/volunteer-schedules/check', methods=['GET'])
def check_volunteer_schedule():
    volunteer_id = request.args.get('volunteer_id')
    shift_date = request.args.get('shift_date')
    
    try:
        # Create a new session with READ UNCOMMITTED isolation level
        with db.engine.connect().execution_options(
            isolation_level="READ UNCOMMITTED"
        ) as conn:
            result = conn.execute(
                text("""
                    SELECT * FROM volunteer_schedule
                    WHERE volunteer_id = :vid
                    AND shift_date = :date
                """),
                {"vid": volunteer_id, "date": shift_date}
            )
            schedules = [dict(row) for row in result]
            return jsonify(schedules), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/pets/popularity-scores', methods=['GET'])
def get_all_popularity_scores():
    try:
        scores = {}
        pets = Pet.query.all()
        for pet in pets:
            pending_applications = AdoptionApplication.query.filter_by(
                pet_id=pet.pet_id, 
                status='Pending'
            ).count()
            
            with db.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT calculate_popularity_score(:breed, :age, :apps)"),
                    {"breed": pet.breed, "age": pet.age, "apps": pending_applications}
                )
                scores[pet.pet_id] = result.scalar()
        
        return jsonify(scores), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/init-sample-data', methods=['POST'])
def init_sample_data():
    try:
        # Sample Pets with vaccination information
        current_date = datetime.utcnow()
        sample_pets = [
            Pet(
                name='Max', 
                breed='Labrador', 
                age=2, 
                weight=25.5, 
                health_condition='Good', 
                vaccination_status='Vaccinated',
                vaccination_due_date=(current_date + timedelta(days=180)).date(),
                status='Available'
            ),
            Pet(
                name='Luna', 
                breed='Beagle', 
                age=1, 
                weight=12.3, 
                health_condition='Good',
                vaccination_status='Vaccinated',
                vaccination_due_date=(current_date + timedelta(days=90)).date(),
                status='Available'
            ),
            Pet(
                name='Rocky', 
                breed='German Shepherd', 
                age=3, 
                weight=30.0, 
                health_condition='Fair',
                vaccination_status='Not Vaccinated',
                vaccination_due_date=(current_date + timedelta(days=30)).date(),
                status='Available'
            ),
            Pet(
                name='Bella', 
                breed='Persian Cat', 
                age=4, 
                weight=4.5, 
                health_condition='Poor',
                vaccination_status='Not Vaccinated',
                vaccination_due_date=(current_date + timedelta(days=7)).date(),
                status='Not Available'
            ),
            Pet(
                name='Charlie', 
                breed='Golden Retriever', 
                age=2, 
                weight=27.8, 
                health_condition='Good',
                vaccination_status='Vaccinated',
                vaccination_due_date=(current_date + timedelta(days=120)).date(),
                status='Available'
            )
        ]
        
        # Rest of the sample data initialization remains the same
        sample_adopters = [
            Adopter(full_name='John Smith', contact_info='john@email.com'),
            Adopter(full_name='Sarah Johnson', contact_info='sarah@email.com'),
            Adopter(full_name='Michael Brown', contact_info='michael@email.com'),
            Adopter(full_name='Emily Davis', contact_info='emily@email.com'),
            Adopter(full_name='David Wilson', contact_info='david@email.com')
        ]
        
        # Add pets and adopters first
        db.session.add_all(sample_pets)
        db.session.add_all(sample_adopters)
        db.session.commit()
        
        # Sample Volunteers
        sample_volunteers = [
            Volunteer(full_name='Alice Cooper', contact_info='alice@email.com', skills='Dog Walking, Grooming', availability='Weekdays'),
            Volunteer(full_name='Bob Martin', contact_info='bob@email.com', skills='Cat Care, Cleaning', availability='Weekends'),
            Volunteer(full_name='Carol White', contact_info='carol@email.com', skills='Medical Care, Training', availability='Flexible'),
            Volunteer(full_name='Dan Brown', contact_info='dan@email.com', skills='Event Planning, Marketing', availability='Weekends'),
            Volunteer(full_name='Eva Green', contact_info='eva@email.com', skills='Administration, Dog Training', availability='Weekdays')
        ]
        
        db.session.add_all(sample_volunteers)
        db.session.commit()

        # Sample Adoption Applications
        sample_applications = [
            AdoptionApplication(
                pet_id=sample_pets[0].pet_id,
                adopter_id=sample_adopters[0].adopter_id,
                status='Pending',
                application_date=current_date
            ),
            AdoptionApplication(
                pet_id=sample_pets[1].pet_id,
                adopter_id=sample_adopters[1].adopter_id,
                status='Approved',
                application_date=current_date - timedelta(days=5)
            ),
            AdoptionApplication(
                pet_id=sample_pets[2].pet_id,
                adopter_id=sample_adopters[2].adopter_id,
                status='Pending',
                application_date=current_date - timedelta(days=2)
            )
        ]
        
        db.session.add_all(sample_applications)
        db.session.commit()
        
        return jsonify({
            "message": "Sample data initialized successfully",
            "pets_added": len(sample_pets),
            "adopters_added": len(sample_adopters),
            "volunteers_added": len(sample_volunteers),
            "applications_added": len(sample_applications)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing sample data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/pets/<int:pet_id>', methods=['DELETE'])
def delete_pet(pet_id):
    try:
        pet = Pet.query.get_or_404(pet_id)
        db.session.delete(pet)
        db.session.commit()
        return jsonify({"message": "Pet deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/adopters/<int:adopter_id>', methods=['DELETE'])
def delete_adopter(adopter_id):
    try:
        adopter = Adopter.query.get_or_404(adopter_id)
        db.session.delete(adopter)
        db.session.commit()
        return jsonify({"message": "Adopter deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    try:
        create_database()
        with app.app_context():
            init_db()
            # setup_federated_connection()
            setup_remote_database()
            init_functions()
            init_procedures()
            init_triggers()
        app.run(debug=True)
    except Exception as e:
        logger.error(f"Application startup error: {str(e)}")
