from typing import List, Dict
import math
import random

class Participant:
    def __init__(self, graph, node, type):
        self.graph = graph
        self.x = node.x
        self.y = node.y
        self.type = type
        self.target = node
        self.distatance = 0 #distance to target

    def new_target(self):
        possible_targets = self.target.get_neightbors()
        if not possible_targets:
            self.distance = 0
            return
        self.target = random.choice(possible_targets)
#self.distance = self.graph.get_edge_length(self.current_node, self.target)
        self.distance = self.target.distance

    def move(self, time=1):
        if self.dstance <= 0:
            self.new_target()
        if self.dstance <= 0:
            return
        self.distance -= time
        if self.distance < 0:
            self.distance = 0
        #todo: update x,y on the distance distance/edge_size with start/end x/y


#(sensor)
class Node:
    def __init__(self, graph, x, y, id):
        self.graph = graph
        self.x = x
        self.y = y
        self.id = id
        self.neighbors = []
        self.graph.nodes[id] = self

#retus a list of the participants in the radius
    def detect(self, radius=1):
        detects = {}
        return detects


    def connect(self, node):
        self.graph.add_edge(Edge(self, node))

#returns nodes connected to this directly
    def get_neighbors(self):
        pass

class Edge:
    def __init__(self, start_node, end_node):
        self.start_node = start_node
        self.end_node = end_node
        dx = end_node.x - start_node.x
        dy = end_node.y - start_node.y
        scala = 1
        self.len = math.sqrt(dx * dx + dy * dy) * scala


class Graph:
    def __init__(self):
        self.edges = []
        self.nodes = {}
        self.participants = []

    def add_edge(self, edge):
        self.edges.append(edge)

    def add_node(self, node):
        self.nodes.append(node)

#moves all participant by time
    def pass_time(self, time=1):
        pass


graph = Graph()

node1 = Node(graph, 0, 0)
node2 = Node(graph, 1, 0)
node3 = Node(graph, 1, 1)
node4 = Node(graph, 0, 1)

node1.connect(node2)
node2.connect(node3)
node3.connect(node4)
node4.connect(node1)

graph.add_node(node1)
graph.add_node(node2)
graph.add_node(node3)
graph.add_node(node4)

participant = Participant(graph, node1, "car")

# Create a sensor on node3
sensor = Sensor(1, 1)

# Move the participant and check if the sensor detects it
participant.move()
print(f"Participant is at ({participant.x}, {participant.y})")
#if sensor.detect(participant):
#    print("Sensor detected the participant!")
#else:
#    print("Sensor did not detect the participant.")
