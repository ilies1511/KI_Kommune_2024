import requests
import os
import time

api_key = os.getenv('API_KEY')
if api_key is None:
	raise ValueError("API_KEY ist nicht gesetzt. Bitte die Umgebungsvariable API_KEY festlegen.")


# Konfiguriere die API-URL
BASE_URL = "https://apis.smartcity.hn/bildungscampus/iotplatform/trafficsensor/v1"

# Funktion zum Abfragen von Entity-IDs und deren Werten
def get_entity_ids(auth_group: str, page: int = 0) -> dict:
	# Endpoint für die Entity-ID-Anfrage
	url = f"{BASE_URL}/authGroup/{auth_group}/entityId"

	# Parameter und API-Schlüssel als Query-Parameter setzen
	params = {
		'x-apikey': api_key,
		'page': page  # Seite für Paginierung festlegen
	}

	# API-Request senden
	try:
		response = requests.get(url, params=params)
		response.raise_for_status()  # Prüft auf Fehler im Response
	except requests.exceptions.RequestException as e:
		print(f"Fehler bei der API-Anfrage: {e}")
		return {}

	# Daten verarbeiten
	data = response.json()

	# Ausgabe der gesamten Antwort zur Überprüfung
	print("Vollständige API-Antwort:")
	print(data)

	# Extrahiere `entities`, falls vorhanden
	entities = data.get('entities', [])
	total_pages = data.get('totalPages', 1)
	total_elements = data.get('totalElements', 0)
	has_next = data.get('hasNext', False)

	# Liste der relevanten Entitäteninformationen zusammenstellen
	entity_list = {
		'entities': entities,
		'totalPages': total_pages,
		'totalElements': total_elements,
		'hasNext': has_next
	}

	return entity_list

# Testaufruf der Funktion
if __name__ == "__main__":
	auth_group = "trafficsensor_devices"  # Beispiel-Authentifizierungsgruppe
	page = 0  # Startseite für die Paginierung

	entity_data = get_entity_ids(auth_group, page)
	print("Liste der Entitäten und aktuelle Werte:")
	print(entity_data)
