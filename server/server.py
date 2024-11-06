from http.server import HTTPServer, SimpleHTTPRequestHandler
import json


# Define the server address and port
HOST = 'localhost'
PORT = 8000


def query_api() => list:
	""" Ilies entry point"""
	pass


def query_json() => list:
	""" Fabians entry point"""
	pass


def enrich_map(point_list: list):
	""" Silvesters entry point"""
	pass

def get_data(handler):
	# here we fill the response with test data
	response_data = query_api()

	# here we paint the map
	enrich_map(response_data)

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
