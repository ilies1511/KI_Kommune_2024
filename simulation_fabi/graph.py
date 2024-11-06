from typing import List, Dict
import math
import random
import time

class Participant:
    def __init__(self, graph, node_id, type, id=0):
        node = graph.nodes[node_id]
        self.graph = graph
        self.x = node.x
        self.y = node.y
        self.type = type
        self.target = node
        #values to check distances to nodes:
        self.passed = 0
        self.distance = 0 #distance to target
        self.id = id

    def new_target(self):
        possible_targets = self.target.neighbors
        if not possible_targets:
            self.distance = 0
            self.passed = 0
            return
        cur = self.target
        self.target = random.choice(possible_targets)
        dx = self.target.x - cur.x
        dy = self.target.y - cur.y
        self.distance = math.sqrt(dx * dx + dy * dy) * self.graph.scale
        self.passed = 0

    def move(self, time=1):
        if self.distance <= 0:
            self.new_target()
        if self.distance <= 0:
            return
        self.distance -= time
        self.passed += time
        if self.distance < 0:
            self.distance = 0


#(sensor)
class Node:
    def __init__(self, graph, id, x, y):
        self.graph = graph
        self.x = x
        self.y = y
        self.id = id
        self.neighbors = []
        self.graph.nodes[id] = self

#retus a list of the participants in the radius
    def detect(self, radius=1):
        detects = []
        for participant in self.graph.participants:
            if participant.target.id == self.id:
                detects.append(participant)
        return detects

    def connect(self, node):
        if any(neighbor.id == node.id for neighbor in self.neighbors):
            return
        self.neighbors.append(node)
        node.neighbors.append(self)

class Graph:
    def __init__(self, scale=1):
        self.scale = scale
        self.nodes = {}
        self.participants = []

    def add_node(self, new_node):
        self.nodes[new_node.id] = new_node

    def pass_time(self, time=1):
        for participant in self.participants:
            participant.move(time)

    def print_detects(self):
        for node in self.nodes.values():
            detects = node.detect()
            for participant in detects:
                print(node.id, ": ", participant.type, "(id: ", participant.id, ")")


graph = Graph(0.010)

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

for id, lat, lon in coordinates:
    graph.nodes[id] = Node(graph, id, lat, lon)

graph.nodes["Europaplatz"].connect(graph.nodes["Kaiserstraße at Europaplatz"])
graph.nodes["Europaplatz"].connect(graph.nodes["Karlstraße at Europaplatz"])
graph.nodes["Europaplatz"].connect(graph.nodes["Douglasstraße at Europaplatz"])

graph.nodes["Karlstraße at Europaplatz"].connect(graph.nodes["Mühlburger Tor"])
graph.nodes["Kaiserstraße at Europaplatz"].connect(graph.nodes["Karlstor"])



car = Participant(graph, "Europaplatz", "car", 1)
graph.participants.append(car)
graph.print_detects()

passed_time = 0
while 1:
    graph.pass_time()
    graph.print_detects()
    passed_time += 1
    print("passed time: ", passed_time)
    time.sleep(1)









