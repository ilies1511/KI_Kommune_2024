from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
from dataclasses import dataclass
import folium
from typing import List
from graph import Graph


# Define the server address and port
HOST = 'localhost'
PORT = 8000

graph = Graph()
car_icon_url = "car.png"

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

@dataclass
class Point:
	coordinate: tuple
	sensor: Sensor

class Map:
	pass


def generate_map():
	sensor_list = graph.get_sensor_list()
	coordinates = [[coordinate["X"], coordinate["Y"]] for coordinate, _ in sensor_list]

	my_map = folium.Map(location=coordinates[0], zoom_start=15)

	# Add all coordinates as CircleMarkers
	for coord in coordinates:
		folium.CircleMarker(
			location=coord,
			radius=5,
			color="blue",
			fill=True,
			fill_color="blue"
		).add_to(my_map)

	# Save the map to an HTML file
	my_map.save("map.html")


def query_api() -> list[Sensor]:
	""" Ilies entry point"""
	pass


def get_map_coordinates(sensors: list[Sensor]) -> list[Point]:
	""" Maras entry point"""
	# check for right format of parameters
	# if len(sensors) != len(coordinates):
	# 	print("Error: Sensor list length does not equal coordinates list length")
	
	# produce list of points
	points = [Point(coordinates[i], sensors[i]) for i in range(len(sensors))]

	# return points list
	return points


def enrich_map():
	""" Silvesters entry point"""

	# # add traffic members
	# for participant in graph.get_participants_positions():
	# 	color = "black"
	# 	if participant["TYPE"] == "car":
	# 		color = "red"
	# 	folium.Marker(
	# 		location=[participant["X"], participant["Y"]],
	# 		icon=folium.CustomIcon(car_icon_url, icon_size=(25, 25))
	# 	).add_to(my_map)

	# # Get the HTML representation as a string
	# map_html = my_map.get_root().render()

	return None


def get_data(handler):
	# here we fill the response with test data
	# response_data = query_api()

	# get sensor data from api
	sensors = query_api()

	# get coordinates and pair them with sensors
	# points = get_map_coordinates(sensors)

	# simulate traffic
	graph.pass_time()

	# paint points to map
	response_data = enrich_map()

	# print sensor data
	graph.print_sensor_data()

	# Send response status
	handler.send_response(200)

	# Set headers for JSON response
	handler.send_header("Content-Type", "application/json")
	handler.end_headers()

	# Write JSON response
	# handler.wfile.write(response_data.encode('utf-8'))
	# handler.wfile.write(response_data.encode('utf-8'))

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/data":
            get_data(self)
        else:
            super().do_GET()

# generate the base map html file
generate_map()

# Create a handler to handle HTTP requests
handler = CustomHTTPRequestHandler

# Create the HTTP server
httpd = HTTPServer((HOST, PORT), handler)

print(f"Serving HTTP on {HOST}:{PORT}...")

# Run the server
httpd.serve_forever()
