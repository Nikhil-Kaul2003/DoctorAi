import numpy as np
from sklearn.ensemble import RandomForestClassifier
from data.symptoms import all_symptoms, symptom_disease_map

# This is a simplified prediction model. In a production environment,
# this would be replaced with a properly trained ML model.

def predict_disease(symptoms, top_n=3):
    """
    Predict diseases based on symptoms
    
    Args:
        symptoms: List of user symptoms
        top_n: Number of top predictions to return
        
    Returns:
        List of tuples containing (disease_name, probability)
    """
    # Create a mapping of diseases to their symptoms
    disease_score = {}
    
    # For each symptom provided by the user
    for symptom in symptoms:
        # Get diseases associated with this symptom
        if symptom in symptom_disease_map:
            for disease in symptom_disease_map[symptom]:
                if disease not in disease_score:
                    disease_score[disease] = 0
                # Increment score for this disease
                disease_score[disease] += 1
    
    # Convert scores to probabilities
    if not disease_score:
        return []
    
    # Get total number of symptoms for each disease to normalize scores
    max_score = max(disease_score.values())
    
    # Calculate probabilities and sort by probability
    results = [(disease, round((score / max_score) * 100, 1)) 
               for disease, score in disease_score.items()]
    results.sort(key=lambda x: x[1], reverse=True)
    
    # Return top N results
    return results[:top_n]

def train_model():
    """
    Train a machine learning model for disease prediction.
    Note: This is a simplified version for demonstration.
    In a real application, this would use a properly trained model.
    """
    # In a production environment, this function would:
    # 1. Load a pre-labeled dataset
    # 2. Extract features and labels
    # 3. Split data into training and test sets
    # 4. Train a model (e.g., Random Forest, Neural Network)
    # 5. Evaluate the model
    # 6. Save the model for future predictions
    
    # For demonstration, we'll create a dummy model
    # In reality, this would be trained on medical data
    
    # Create a dummy training set
    X_train = np.zeros((1, len(all_symptoms)))  # Feature matrix
    y_train = np.array([''])  # Target disease labels
    
    # Initialize and train the model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    return model
