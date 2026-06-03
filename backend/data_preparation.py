import re
import numpy as np
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk

# Download required NLTK data
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

try:
    nltk.data.find('punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('stopwords')
except LookupError:
    nltk.download('stopwords')

sia = SentimentIntensityAnalyzer()

class TextFeatureExtractor:
    """Extract features from horse description texts"""
    
    POSITIVE_KEYWORDS = {
        'invaincue': 1.0,
        'invaincu': 1.0,
        'excellent': 0.9,
        'dominer': 0.8,
        'podium': 0.7,
        'adore': 0.8,
        'gagnant': 1.0,
        'victoire': 0.9,
        'opportunité': 0.6,
        'perform': 0.7,
        'sûr': 0.7,
        'fort': 0.7,
    }
    
    NEGATIVE_KEYWORDS = {
        'difficile': -0.8,
        'faible': -0.7,
        'plaqué': -0.6,
        'dominée': -0.8,
        'échoué': -0.9,
        'rentrée': -0.4,
        'décevoir': -0.8,
        'tâche': -0.5,
        'problème': -0.7,
        'blessure': -0.9,
        'mauvais': -0.8,
        'perte': -0.7,
    }
    
    def __init__(self):
        self.stop_words = set(stopwords.words('french'))
    
    def extract_features(self, text):
        """Extract numerical features from description text"""
        if not text or len(str(text).strip()) == 0:
            return {
                'sentiment_score': 0.0,
                'keyword_score': 0.0,
                'experience_score': 0.0,
                'confidence_score': 0.0,
            }
        
        text = str(text).lower()
        
        # 1. Sentiment analysis
        sentiment = sia.polarity_scores(text)
        sentiment_score = sentiment['compound']  # -1 to 1
        
        # 2. Keyword-based scoring
        keyword_score = self._extract_keyword_score(text)
        
        # 3. Experience indicator (mentions of previous performances)
        experience_score = self._extract_experience_score(text)
        
        # 4. Confidence score (mentions of favorites, odds indications)
        confidence_score = self._extract_confidence_score(text)
        
        return {
            'sentiment_score': (sentiment_score + 1) / 2,  # Normalize to 0-1
            'keyword_score': keyword_score,
            'experience_score': experience_score,
            'confidence_score': confidence_score,
        }
    
    def _extract_keyword_score(self, text):
        """Score based on positive/negative keywords"""
        score = 0.0
        keyword_count = 0
        
        for keyword, value in self.POSITIVE_KEYWORDS.items():
            if keyword in text:
                score += value
                keyword_count += 1
        
        for keyword, value in self.NEGATIVE_KEYWORDS.items():
            if keyword in text:
                score += value
                keyword_count += 1
        
        if keyword_count == 0:
            return 0.5
        
        # Normalize to 0-1
        return (score / keyword_count + 1) / 2
    
    def _extract_experience_score(self, text):
        """Score based on mentions of experience and track record"""
        experience_indicators = [
            'podium', 'victoire', 'gagnant', 'victoires',
            'sorties', 'sortes', 'parcours', 'expérience',
            'trois', 'quatre', 'cinq', 'plusieurs'
        ]
        
        count = sum(1 for indicator in experience_indicators if indicator in text)
        return min(count / 5, 1.0)  # Normalize
    
    def _extract_confidence_score(self, text):
        """Score based on perceived chance to win"""
        high_confidence = ['invaincue', 'excellent', 'dominer', 'favori', 'favorite']
        low_confidence = ['difficile', 'plaqué', 'rentrée', 'tâche']
        
        high_count = sum(1 for word in high_confidence if word in text)
        low_count = sum(1 for word in low_confidence if word in text)
        
        score = (high_count - low_count) / 5
        return max(0, min(score, 1.0))


class OddsConverter:
    """Convert betting odds to implied probabilities"""
    
    @staticmethod
    def fractional_to_decimal(fractional_str):
        """Convert fractional odds (e.g., '77/1') to decimal (e.g., 78.0)"""
        try:
            if '/' not in str(fractional_str):
                return float(fractional_str)
            
            parts = str(fractional_str).strip().split('/')
            if len(parts) != 2:
                return None
            
            numerator = float(parts[0])
            denominator = float(parts[1])
            
            if denominator == 0:
                return None
            
            return (numerator + denominator) / denominator
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def decimal_to_probability(decimal_odds):
        """Convert decimal odds to implied probability"""
        if decimal_odds is None or decimal_odds <= 0:
            return 0.0
        
        probability = 1.0 / decimal_odds
        return max(0.0, min(probability, 1.0))
    
    @staticmethod
    def fractional_to_probability(fractional_str):
        """Convert fractional odds directly to probability"""
        decimal = OddsConverter.fractional_to_decimal(fractional_str)
        return OddsConverter.decimal_to_probability(decimal)
    
    @staticmethod
    def normalize_probabilities(probabilities):
        """Normalize probabilities to sum to 1.0"""
        total = sum(probabilities)
        if total == 0:
            return [1.0 / len(probabilities) for _ in probabilities]
        return [p / total for p in probabilities]


class FeatureNormalizer:
    """Normalize features for neural network input"""
    
    def __init__(self):
        self.means = None
        self.stds = None
    
    def fit(self, features):
        """Calculate statistics for normalization"""
        features_array = np.array(features)
        self.means = np.mean(features_array, axis=0)
        self.stds = np.std(features_array, axis=0)
        
        # Avoid division by zero
        self.stds[self.stds == 0] = 1.0
    
    def normalize(self, features):
        """Normalize features using fitted statistics"""
        if self.means is None or self.stds is None:
            # If not fitted, just use simple 0-1 normalization
            features_array = np.array(features)
            min_vals = np.min(features_array, axis=0)
            max_vals = np.max(features_array, axis=0)
            return (features_array - min_vals) / (max_vals - min_vals + 1e-8)
        
        return (np.array(features) - self.means) / self.stds


def prepare_race_data(horses_data):
    """
    Prepare race data for model input
    
    Input format:
    [
        {
            'number': 1,
            'name': 'JIBI DU FRUITIER',
            'description': 'Text...',
            'odds': '77/1'
        },
        ...
    ]
    
    Returns:
        features_array: (n_horses, n_features) array for model input
        horses_info: List of horse info with processed odds
        implicit_probabilities: Market-implied probabilities from odds
    """
    
    text_extractor = TextFeatureExtractor()
    odds_converter = OddsConverter()
    
    horses_info = []
    implicit_probs = []
    text_features = []
    odds_features = []
    
    for horse in horses_data:
        # Extract text features
        text_feats = text_extractor.extract_features(horse.get('description', ''))
        text_features.append([
            text_feats['sentiment_score'],
            text_feats['keyword_score'],
            text_feats['experience_score'],
            text_feats['confidence_score'],
        ])
        
        # Convert odds to probability
        odds_str = horse.get('odds', '')
        decimal_odds = odds_converter.fractional_to_decimal(odds_str)
        odds_prob = odds_converter.decimal_to_probability(decimal_odds)
        implicit_probs.append(odds_prob)
        odds_features.append([odds_prob])
        
        horses_info.append({
            'number': horse.get('number', 0),
            'name': horse.get('name', ''),
            'odds': odds_str,
            'decimal_odds': decimal_odds,
            'odds_probability': odds_prob,
            'text_features': text_feats
        })
    
    # Normalize implicit probabilities
    implicit_probs = odds_converter.normalize_probabilities(implicit_probs)
    
    # Combine all features
    text_features = np.array(text_features)
    odds_features = np.array(odds_features)
    
    # Simple concatenation for now
    combined_features = np.hstack([text_features, odds_features])
    
    return combined_features, horses_info, implicit_probs
