from typing import List, Dict
import math
import random
import time

class Participant:
    #adds new participant to graph
    def __init__(self, graph, node_id, type, id=0):
        node = graph.nodes[node_id]
        self.graph = graph
        self.x = node.x
        self.y = node.y
        self.type = type
        self.cur = node
        self.target = node
        self.passed_meters = 0 #distance from start
        self.distance_meters = 0 #distance to target
        self.id = id #some id to ident participants
        self.meters_per_sec = 10
        self.total_dist = 1 #some init val to avoid zero div
        self.total_meters = 1#some init val to avoid zero div

    #participant changes destination goal(used when prev destionation was reached)
    def new_target(self):
        possible_targets = self.target.neighbors
        if not possible_targets:
            self.distance_meters = 0
            self.passed_meters = 0
            return
        last = self.cur
        self.cur = self.target
        self.target = random.choice(possible_targets)
        while len(possible_targets) > 1 and last.id == self.target.id:
            self.target = random.choice(possible_targets)
        self.x = self.target.x
        self.y = self.target.y
        self.passed_meters = 0
        self.passed_coords = 0

        dx = self.target.x - self.cur.x
        dy = self.target.y - self.cur.y
        self.dx_coords = dx
        self.dy_coords = dy
        total_distance = math.sqrt(dx * dx + dy * dy) #edge len
        if total_distance != 0:
            self.unit_dx = dx / total_distance
            self.unit_dy = dy / total_distance
        else:
            self.unit_dx = 0
            self.unit_dy = 0
        #get a some what representation in meters for this area
        dx *= 73
        dy *= 111.32
        self.distance_meters = math.sqrt(dx * dx + dy * dy)
        self.distance_meters *= 1600
        self.total_meters = self.distance_meters

    #participant moves the amount of his speed * time
    def move(self, time=1, speed_scala=1):
        if self.distance_meters <= 0:
            self.new_target()
        if self.distance_meters <= 0:
            return
        self.distance_meters -= time * self.meters_per_sec * speed_scala
        self.passed_meters += time * self.meters_per_sec * speed_scala

        if self.distance_meters < 0:
            self.distance_meters = 0
            self.x = self.target.x
            self.y = self.target.y
        else:
            self.x = self.cur.x + self.dx_coords * (self.passed_meters / self.total_meters)
            self.y = self.cur.y + self.dy_coords * (self.passed_meters / self.total_meters)

        #print("distance to last node:", self.passed_meters)
        #print("distance to next node:", self.distance_meters)
        #
        #print("x:", self.x, ", y:", self.y)


#(sensor)
#use node.connect() to create edges in a graph
#edges go in both directions
class Node:
    def __init__(self, graph, id, x, y, is_sensor=True):
        self.graph = graph
        self.x = x
        self.y = y
        self.id = id
        self.neighbors = []
        self.graph.nodes[id] = self
        self.is_sensor = is_sensor

    #if the node is not a sensor returns an empty list
    #returns a list of the participants in the radius if it is a sensor
    #currently a sensor has a 360 fov
    def detect(self, radius=10):
        detects = []
        if not self.is_sensor:
            return detects
        for participant in self.graph.participants:
            if participant.target.id == self.id and participant.distance_meters <= radius:
                detects.append(participant)
            elif participant.cur.id == self.id and participant.passed_meters <= radius:
                detects.append(participant)
        return detects

    #creates an edge between two nodes
    def connect(self, node):
        if any(neighbor.id == node.id for neighbor in self.neighbors):
            return
        self.neighbors.append(node)
        node.neighbors.append(self)

class Graph:
    #set the speed to control the speed of the simulation
    #(1-> 1simulation sec/1real sec)
    #too fast speeds will be buggy for small maps
    def __init__(self, speed=1, car_count=10):
        self.speed = speed
        self.nodes = {}
        self.participants = []

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
            self.nodes[id] = Node(self, id, lat, lon)
        self.nodes["Europaplatz"].connect(self.nodes["Kaiserstraße at Europaplatz"])
        self.nodes["Europaplatz"].connect(self.nodes["Karlstraße at Europaplatz"])
        self.nodes["Europaplatz"].connect(self.nodes["Douglasstraße at Europaplatz"])
        self.nodes["Karlstraße at Europaplatz"].connect(self.nodes["Mühlburger Tor"])
        self.nodes["Kaiserstraße at Europaplatz"].connect(self.nodes["Karlstor"])
        self.nodes["Douglasstraße at Europaplatz"].connect(self.nodes["Lammstraße"])
        self.nodes["Douglasstraße at Europaplatz"].connect(self.nodes["Waldstraße"])
        self.nodes["Durlacher Tor"].connect(self.nodes["Kaiserstraße at Durlacher Tor"])
        self.nodes["Durlacher Tor"].connect(self.nodes["Durlacher Allee at Durlacher Tor"])
        self.nodes["Durlacher Tor"].connect(self.nodes["Karl-Wilhelm-Straße at Durlacher Tor"])
        self.nodes["Kaiserstraße at Durlacher Tor"].connect(self.nodes["Gottesauer Platz"])
        self.nodes["Kaiserstraße at Durlacher Tor"].connect(self.nodes["Tullastraße"])
        self.nodes["Durlacher Allee at Durlacher Tor"].connect(self.nodes["Ostring"])
        self.nodes["Durlacher Allee at Durlacher Tor"].connect(self.nodes["Durlach Auer Straße"])
        self.nodes["Karl-Wilhelm-Straße at Durlacher Tor"].connect(self.nodes["Schlossgarten"])
        self.nodes["Karl-Wilhelm-Straße at Durlacher Tor"].connect(self.nodes["Rintheimer Straße"])
        i = 0
        while i < car_count:
            car = Participant(self, "Europaplatz", "car", i)
            self.participants.append(car)
            i += 1

    def get_participants_positions(self):
        #todo
        pass

    def get_sensor_list(self):
        #returns a list of
        #[
        #   (
        #       {SENSOR_ID=.., X_COORDS=.., Y_COORDS=...},
        #       [{PARTICIPENT_TYPE=.., PARTICIPANT_ID=...,PARTICIPANT_X_COORDS= PARTICIPANT_Y_COORDS=..},...]
        #   ),...more pairs
        #]
        #todo
        
            
    def add_node(self, new_node):
        self.nodes[new_node.id] = new_node

    #advance simulation by 1 simulation second
    def pass_time(self, time=1):
        for participant in self.participants:
            participant.move(time, self.speed)

    #prints the current cars in sensor ranges
    def print_detects(self, range=1):
        for node in self.nodes.values():
            detects = node.detect(range)
            for participant in detects:
                print(node.id, ": ", participant.type, "(id: ", participant.id, ")")

if __name__ == '__main__':
    graph = Graph()
    graph.print_detects()
    passed_time = 0
    while 1:
        graph.pass_time()
        graph.print_detects(10)
        passed_time += 1
        print("passed time: ", passed_time)
        time.sleep(1)

