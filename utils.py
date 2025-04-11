import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from data.symptoms import all_symptoms, symptom_synonyms
from data.diseases import diseases_data

# Download necessary NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess_symptoms(selected_symptoms, additional_symptoms_text):
    """
    Process user-provided symptoms
    
    Args:
        selected_symptoms: List of symptoms selected from dropdown
        additional_symptoms_text: Free text symptoms entered by user
        
    Returns:
        List of normalized symptoms
    """
    processed_symptoms = set(selected_symptoms)
    
    if additional_symptoms_text:
        # Tokenize and extract symptoms from text
        text_symptoms = extract_symptoms_from_text(additional_symptoms_text)
        processed_symptoms.update(text_symptoms)
    
    return list(processed_symptoms)

def extract_symptoms_from_text(text):
    """
    Extract symptoms from free text input
    
    Args:
        text: User-entered symptom text
        
    Returns:
        Set of recognized symptoms
    """
    # Tokenize and clean text
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    words = nltk.word_tokenize(text)
    words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]
    
    # Match symptoms and their synonyms
    recognized_symptoms = set()
    
    # Check for single word symptoms
    for word in words:
        for symptom in all_symptoms:
            # Check if word matches symptom or any of its synonyms
            if word == symptom.lower() or word in symptom_synonyms.get(symptom, []):
                recognized_symptoms.add(symptom)
                break
    
    # Check for multi-word symptoms
    for i in range(len(words)):
        for j in range(i+1, min(i+5, len(words)+1)):  # Check phrases up to 4 words
            phrase = ' '.join(words[i:j])
            for symptom in all_symptoms:
                if phrase == symptom.lower() or phrase in symptom_synonyms.get(symptom, []):
                    recognized_symptoms.add(symptom)
                    break
    
    return recognized_symptoms

def get_disease_info(disease_name):
    """
    Get detailed information about a disease
    
    Args:
        disease_name: Name of the disease
        
    Returns:
        Dictionary with disease information
    """
    return diseases_data.get(disease_name, None)
