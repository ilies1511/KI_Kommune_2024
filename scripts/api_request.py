import requests
import matplotlib.pyplot as plt
import pandas as pd

# Basis-URL der API
BASE_URL = "https://datacenter.bernard-gruppe.com/api/v3"
ENDPOINT = "/moving_traffic/nodes/meta"

# Zusammengesetzte URL für den API-Endpunkt
url = BASE_URL + ENDPOINT

# Beispiel-Parameter: Datum für den Zeitraum
params = {
    'start_date': '2024-11-01',  # Startdatum
    'end_date': '2024-11-06'     # Enddatum
}

# Dein API-Schlüssel
api_key = ""

# Header mit API-Schlüssel (falls erforderlich)
headers = {'Authorization': f'Bearer {api_key}'}
# headers = {'Authorization': 'Bearer izi_code'}



# API-Anfrage stellen
response = requests.get(url, params=params, headers=headers)

# Überprüfung der Antwort
if response.status_code == 200:
    data = response.json()  # Antwort in JSON umwandeln
    print("Daten erfolgreich abgerufen:")
    print(data)

    # Umwandeln der Daten in ein DataFrame (wenn die Antwort eine Liste von Nodes enthält)
    traffic_nodes = data.get('traffic_nodes', [])
    parking_nodes = data.get('parking_nodes', [])

    # Beispiel: Verkehrsknoten und Parkknoten visualisieren
    if traffic_nodes:
        traffic_df = pd.DataFrame(traffic_nodes)
        print(traffic_df.head())

        # Visualisierung der Verkehrsknoten nach Startdatum (Beispiel)
        plt.plot(traffic_df['start_date'], traffic_df['lat'], marker='o', label='Verkehrsknoten')
        plt.xlabel('Startdatum')
        plt.ylabel('Latitude')
        plt.title('Verkehrsknoten über die Zeit')
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.legend()
        plt.show()

    if parking_nodes:
        parking_df = pd.DataFrame(parking_nodes)
        print(parking_df.head())

        # Visualisierung der Parkknoten (Beispiel)
        plt.plot(parking_df['start_date'], parking_df['capacity'], marker='x', label='Parkknoten')
        plt.xlabel('Startdatum')
        plt.ylabel('Kapazität')
        plt.title('Parkknoten Kapazität über die Zeit')
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.legend()
        plt.show()

else:
    print(f"Fehler bei der Anfrage: {response.status_code} - {response.text}")
