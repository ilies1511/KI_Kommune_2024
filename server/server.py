from http.server import HTTPServer, SimpleHTTPRequestHandler
import json


# Define the server address and port
HOST = 'localhost'
PORT = 8000

# define coordinates in Karlsruhe
# List of GPS coordinates: (latitude, longitude)
coordinates = [
    # Europaplatz
    ("Europaplatz", 49.0080, 8.3960),
    # Neighbors of Europaplatz
    ("Kaiserstraße at Europaplatz", 49.0080, 8.3965),
    ("Karlstraße at Europaplatz", 49.0075, 8.3960),
    ("Douglasstraße at Europaplatz", 49.0085, 8.3955),

    # Neighbors of "Kaiserstraße at Europaplatz"
    ("Kronenplatz", 49.0085, 8.4030),
    ("Marktplatz", 49.0080, 8.4000),

    # Neighbors of "Karlstraße at Europaplatz"
    ("Mühlburger Tor", 49.0065, 8.3930),
    ("Karlstor", 49.0070, 8.3990),

    # Neighbors of "Douglasstraße at Europaplatz"
    ("Lammstraße", 49.0087, 8.3925),
    ("Waldstraße", 49.0092, 8.3970),

    # Durlacher Tor
    ("Durlacher Tor", 49.0090, 8.4180),
    # Neighbors of Durlacher Tor
    ("Kaiserstraße at Durlacher Tor", 49.0090, 8.4175),
    ("Durlacher Allee at Durlacher Tor", 49.0095, 8.4185),
    ("Karl-Wilhelm-Straße at Durlacher Tor", 49.0085, 8.4180),

    # Neighbors of "Kaiserstraße at Durlacher Tor"
    ("Gottesauer Platz", 49.0090, 8.4240),
    ("Tullastraße", 49.0092, 8.4295),

    # Neighbors of "Durlacher Allee at Durlacher Tor"
    ("Ostring", 49.0100, 8.4320),
    ("Durlach Auer Straße", 49.0110, 8.4365),

    # Neighbors of "Karl-Wilhelm-Straße at Durlacher Tor"
    ("Schlossgarten", 49.0090, 8.4135),
    ("Rintheimer Straße", 49.0100, 8.4200)
]

class Sensor:
	def __init__(self, entity_id, value, timestamp, count, sensor_type):
		self.entity_id = entity_id  # Die eindeutige ID des Sensors
		self.value = value  # Der Wert (z.B. gemessene Geschwindigkeit oder Anzahl der Fahrzeuge)
		self.timestamp = timestamp  # Der Zeitstempel der Messung
		self.count = count  # Die Anzahl des Typs (z.B. 5 Autos)
		self.type = sensor_type  # Der Typ des Objekts (z.B. "Car", "Bus", "Bike")

	def __repr__(self):
		# Gibt eine benutzerfreundliche Darstellung des Sensor-Objekts zurück
		return (f"Sensor(entity_id={self.entity_id}, value={self.value}, "
				f"timestamp={self.timestamp}, count={self.count}, type={self.type})")

class Point:
	pass

class Map:
	pass

def query_api() -> list[Sensor]:
	""" Ilies entry point"""
	pass


def get_map_coordinates(sensors: list[Sensor]) -> list[Point]:
	""" Maras entry point"""
	print(len(coordinates))


def move_traffic(points: list[Point]) -> list[Point]:
	""" Fabians part"""
	pass


def enrich_map(coordinates: list[Point]) -> Map:
	""" Silvesters entry point"""
	pass

def get_data(handler):
	# here we fill the response with test data
	response_data = query_api()

	# get sensor data from api
	sensors = query_api()

	# get coordinates and pair them with sensors
	points = get_map_coordinates(sensors)

	# simulate traffic
	points = move_traffic(points)

	# paint points to map
	response_data = enrich_map(points)

	# test with list of points
	test_response_data = [(1, 1), (2, 2), (3, 3)]

	# Send response status
	handler.send_response(200)

	# Set headers for JSON response
	handler.send_header("Content-Type", "application/json")
	handler.end_headers()

	# Write JSON response
	handler.wfile.write(json.dumps(test_response_data).encode())

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/data":
            get_data(self)
        else:
            super().do_GET()


# Create a handler to handle HTTP requests
handler = CustomHTTPRequestHandler

# Create the HTTP server
httpd = HTTPServer((HOST, PORT), handler)

print(f"Serving HTTP on {HOST}:{PORT}...")

# Run the server
httpd.serve_forever()
