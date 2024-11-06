import requests
import datetime

# Der API-Schlüssel sollte hier sicher gesetzt sein
api_key = "YOUR_API_KEY"

# Konfiguriere die API-URL und Endpunkt
BASE_URL = "https://datacenter.bernard-gruppe.com/api/v3"
ENDPOINT = "/moving_traffic/nodes/meta"

# Funktion query_api
def query_api() -> list:
	# Datum für den Zeitraum setzen (z.B. letzter Tag)
	end_date = datetime.datetime.now().strftime('%Y-%m-%d')
	start_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
	# API-Parameter und Header
	params = {
		'start_date': start_date,
		'end_date': end_date
	}
	headers = {'Authorization': f'Bearer {api_key}'}
	# API-Request senden
	try:
		response = requests.get(BASE_URL + ENDPOINT, params=params, headers=headers)
		response.raise_for_status()  # Prüft auf Fehler im Response
	except requests.exceptions.RequestException as e:
		print(f"Fehler bei der API-Anfrage: {e}")
		return []
	# Daten verarbeiten
	data = response.json()
	traffic_nodes = data.get('traffic_nodes', [])
	parking_nodes = data.get('parking_nodes', [])
	# Liste der relevanten Punkte zusammenstellen
	point_list = []
	# Beispiel: nur Latitude und Longitude extrahieren
	for node in traffic_nodes:
		point_list.append((node['lat'], node['lon']))
	for node in parking_nodes:
		point_list.append((node['lat'], node['lon']))
	return point_list
