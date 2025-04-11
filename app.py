import os
import logging
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from predictor import predict_disease
from utils import get_disease_info, preprocess_symptoms
from data.diseases import diseases_data
from data.symptoms import all_symptoms
from models import db, User, Diagnosis, DiagnosisResult

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-doctor-ai-secret")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "connect_args": {
        "sslmode": "require"
    }
}

# Initialize the database
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()
    logging.info("Database tables created")

@app.route('/')
def index():
    """Render the home page with symptom selection form"""
    return render_template('index.html', symptoms=sorted(all_symptoms))

@app.route('/diagnose', methods=['POST'])
def diagnose():
    """Process symptoms and provide diagnosis"""
    try:
        # Get user input
        user_symptoms = request.form.getlist('symptoms')
        additional_symptoms = request.form.get('additional_symptoms', '')
        
        # Check if symptoms were provided
        if not user_symptoms and not additional_symptoms.strip():
            flash("Please select at least one symptom for diagnosis", "warning")
            return redirect(url_for('index'))
        
        # Process symptoms
        processed_symptoms = preprocess_symptoms(user_symptoms, additional_symptoms)
        
        if not processed_symptoms:
            flash("No valid symptoms were found. Please try again.", "warning")
            return redirect(url_for('index'))
            
        # Predict disease based on symptoms
        predicted_diseases = predict_disease(processed_symptoms)
        
        if not predicted_diseases:
            flash("Unable to determine a diagnosis based on provided symptoms. Please consult a medical professional.", "info")
            return redirect(url_for('index'))
        
        # Get information about predicted diseases
        results = []
        for disease, probability in predicted_diseases:
            disease_info = get_disease_info(disease)
            if disease_info:
                results.append({
                    'disease': disease,
                    'probability': probability,
                    'info': disease_info
                })
        
        # Store results in session for use in recommendations
        session['diagnosis_results'] = results
        
        # Save diagnosis to the database (as anonymous user for now)
        max_retry = 3
        retry_count = 0
        saved_to_db = False
        
        while retry_count < max_retry and not saved_to_db:
            try:
                # Create a new diagnosis record
                diagnosis = Diagnosis(
                    symptoms=processed_symptoms,
                )
                db.session.add(diagnosis)
                db.session.flush()  # Get the diagnosis ID
                
                # Save each diagnosis result
                for result in results:
                    disease_info = result['info']
                    diagnosis_result = DiagnosisResult(
                        diagnosis_id=diagnosis.id,
                        disease=result['disease'],
                        probability=result['probability'],
                        description=disease_info.get('description'),
                        precautions=disease_info.get('precautions'),
                        diet=disease_info.get('diet'),
                        workout=disease_info.get('workout'),
                        medication=disease_info.get('medication')
                    )
                    db.session.add(diagnosis_result)
                
                db.session.commit()
                logging.info(f"Saved diagnosis ID {diagnosis.id} to database")
                
                # Store diagnosis ID in session for future reference
                session['diagnosis_id'] = diagnosis.id
                saved_to_db = True
                
            except Exception as db_error:
                retry_count += 1
                logging.error(f"Database error (attempt {retry_count}/{max_retry}): {str(db_error)}")
                db.session.rollback()
                
                # If it's the last retry, continue anyway - we'll show results even if DB save fails
                if retry_count >= max_retry:
                    logging.warning("Maximum retry attempts reached, proceeding without saving to database")
                else:
                    # Add a small delay before retrying
                    import time
                    time.sleep(0.5)
        
        return render_template('results.html', results=results)
        
    except Exception as e:
        logging.error(f"Error during diagnosis: {str(e)}")
        flash("An error occurred while processing your symptoms. Please try again.", "danger")
        return redirect(url_for('index'))

@app.route('/history')
def history():
    """Display patient diagnosis history"""
    max_retry = 3
    retry_count = 0
    
    while retry_count < max_retry:
        try:
            # Get all diagnoses from the database, ordered by newest first
            diagnoses = Diagnosis.query.order_by(Diagnosis.created_at.desc()).all()
            
            history_items = []
            for diagnosis in diagnoses:
                # Get the top result for this diagnosis
                top_result = DiagnosisResult.query.filter_by(diagnosis_id=diagnosis.id)\
                    .order_by(DiagnosisResult.probability.desc()).first()
                
                if top_result:
                    history_items.append({
                        'id': diagnosis.id,
                        'date': diagnosis.created_at,
                        'symptoms': diagnosis.symptoms,
                        'top_disease': top_result.disease,
                        'probability': top_result.probability
                    })
            
            return render_template('history.html', history_items=history_items)
            
        except Exception as e:
            retry_count += 1
            logging.error(f"Error retrieving history (attempt {retry_count}/{max_retry}): {str(e)}")
            
            if retry_count >= max_retry:
                flash("An error occurred while retrieving your diagnosis history.", "danger")
                return redirect(url_for('index'))
            
            # Add a small delay before retrying
            import time
            time.sleep(0.5)

@app.route('/history/<int:diagnosis_id>')
def diagnosis_detail(diagnosis_id):
    """View details of a specific diagnosis"""
    max_retry = 3
    retry_count = 0
    
    while retry_count < max_retry:
        try:
            # Get the diagnosis and its results
            diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
            results = DiagnosisResult.query.filter_by(diagnosis_id=diagnosis_id)\
                .order_by(DiagnosisResult.probability.desc()).all()
            
            # Format results for the template
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'disease': result.disease,
                    'probability': result.probability,
                    'info': {
                        'description': result.description,
                        'precautions': result.precautions,
                        'diet': result.diet,
                        'workout': result.workout,
                        'medication': result.medication
                    }
                })
            
            return render_template('results.html', results=formatted_results, from_history=True)
            
        except Exception as e:
            retry_count += 1
            logging.error(f"Error retrieving diagnosis detail (attempt {retry_count}/{max_retry}): {str(e)}")
            
            if retry_count >= max_retry:
                flash("An error occurred while retrieving diagnosis details.", "danger")
                return redirect(url_for('history'))
            
            # Add a small delay before retrying
            import time
            time.sleep(0.5)

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('error.html', error_code=404, error_message="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('error.html', error_code=500, error_message="Server error"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
