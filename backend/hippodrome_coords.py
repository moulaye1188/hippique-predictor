"""Hippodrome coordinates mapping - France"""

HIPPODROME_COORDS = {
    'PARISLONGCHAMP': {
        'latitude': 48.8566,
        'longitude': 2.2562,
        'name': 'Paris-Longchamp'
    },
    'VINCENNES': {
        'latitude': 48.8381,
        'longitude': 2.3953,
        'name': 'Hippodrome de Vincennes'
    },
    'AUTEUIL': {
        'latitude': 48.8456,
        'longitude': 2.1631,
        'name': 'Hippodrome d\'Auteuil'
    },
    'LAVAL': {
        'latitude': 48.0753,
        'longitude': -0.7662,
        'name': 'Hippodrome de Laval'
    },
    'LYON': {
        'latitude': 45.7640,
        'longitude': 4.8357,
        'name': 'Hippodrome de Lyon'
    },
    'MARSEILLE': {
        'latitude': 43.3569,
        'longitude': 5.3720,
        'name': 'Hippodrome de Marseille'
    },
    'BORDEAUX': {
        'latitude': 44.8378,
        'longitude': -0.5736,
        'name': 'Hippodrome de Bordeaux'
    },
    'TOULOUSE': {
        'latitude': 43.5890,
        'longitude': 1.4407,
        'name': 'Hippodrome de Toulouse'
    },
    'SAINT-CLOUD': {
        'latitude': 48.8583,
        'longitude': 2.2273,
        'name': 'Hippodrome de Saint-Cloud'
    },
    'CHANTILLY': {
        'latitude': 49.1904,
        'longitude': 2.4760,
        'name': 'Hippodrome de Chantilly'
    },
    'MAISONS-LAFFITTE': {
        'latitude': 48.9554,
        'longitude': 2.1549,
        'name': 'Hippodrome de Maisons-Laffitte'
    },
    'DEAUVILLE': {
        'latitude': 49.3510,
        'longitude': 0.0911,
        'name': 'Hippodrome de Deauville'
    },
    'ARCUEIL': {
        'latitude': 48.8131,
        'longitude': 2.3377,
        'name': 'Hippodrome d\'Arcueil'
    },
    'AMIENS': {
        'latitude': 49.8942,
        'longitude': 2.2864,
        'name': 'Hippodrome d\'Amiens'
    },
    'ENGHIEN': {
        'latitude': 48.9731,
        'longitude': 2.3089,
        'name': 'Hippodrome d\'Enghien'
    },
    'FONTAINEBLEAU': {
        'latitude': 48.4047,
        'longitude': 2.7029,
        'name': 'Hippodrome de Fontainebleau'
    },
    'DIEPPE': {
        'latitude': 49.9237,
        'longitude': 1.0776,
        'name': 'Hippodrome de Dieppe'
    },
    'CAEN': {
        'latitude': 49.1829,
        'longitude': -0.3713,
        'name': 'Hippodrome de Caen'
    },
    'NANTES': {
        'latitude': 47.2199,
        'longitude': -1.5582,
        'name': 'Hippodrome de Nantes'
    },
    'ANGERS': {
        'latitude': 47.4741,
        'longitude': -0.5539,
        'name': 'Hippodrome d\'Angers'
    }
}


def get_hippodrome_coords(hippodrome_name: str) -> dict:
    """
    Get latitude/longitude for a hippodrome
    
    Args:
        hippodrome_name: Hippodrome name (e.g., 'VINCENNES', 'PARISLONGCHAMP')
    
    Returns:
        Dict with 'latitude', 'longitude', 'name' keys
    """
    return HIPPODROME_COORDS.get(hippodrome_name.upper(), {
        'latitude': 48.8566,  # Default to Paris
        'longitude': 2.3522,
        'name': 'Unknown'
    })
