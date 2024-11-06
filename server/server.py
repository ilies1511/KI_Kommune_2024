from http.server import HTTPServer, SimpleHTTPRequestHandler
import json


# Define the server address and port
HOST = 'localhost'
PORT = 8000


def query_api() => list[Sensor]:
	""" Ilies entry point"""
	pass


def get_map_coordinates(sensors: list[Sensor]) => list[Point]:
	""" Maras entry point"""
	pass


def move_traffic(list[Point]) => list[Point]:
	""" Fabians part"""
	pass


def enrich_map(coordinates: list[Point] -> Map):
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
