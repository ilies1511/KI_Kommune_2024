from typing import List, Dict
import osmnx as ox
import math
import random
import time
import diagram
import numpy as np

class Participant:
    #adds new participant to graph
    def __init__(self, graph, node_id, type, id=0, meters_per_sec=10):
        node = graph.nodes[node_id]
        self.active_time = 0
        self.graph = graph
        self.x = node.x
        self.y = node.y
        self.type = type
        self.cur = node
        self.target = node
        self.passed_meters = 0 #distance from start
        self.distance_meters = 0 #distance to target
        self.id = id #some id to ident participants
        self.meters_per_sec = meters_per_sec
        self.total_dist = 1 #some init val to avoid zero div
        self.total_meters = 1#some init val to avoid zero div

    def refresh_active_time(self):
        day_time = self.graph.day_time
        variance = random.randint(-1, 1)
        if self.type == "car":
            if 7 <= day_time < 10 or 17 <= day_time < 20:
                base_active_time = random.randint(6, 8)
            else:
                base_active_time = random.randint(2, 5)
        elif self.type == "truck":
            if day_time < 6 or day_time > 20:
                base_active_time = random.randint(5, 8)
            else:
                base_active_time = random.randint(2, 4)
        elif self.type == "foot":
            if 6 <= day_time < 20:
                base_active_time = random.randint(3, 6)
            else:
                base_active_time = random.randint(1, 3)
        elif self.type == "bicycle":
            if 8 <= day_time < 18:
                base_active_time = random.randint(4, 7)
            else:
                base_active_time = random.randint(1, 3)
        elif self.type == "motor_bike":
            if 6 <= day_time < 22:
                base_active_time = random.randint(4, 6)
            else:
                base_active_time = random.randint(2, 5)
        if self.month in [5, 6, 7, 8]:
            base_active_time += 1
        elif self.month in [11, 0, 1]:
            base_active_time -= 1
        return max(base_active_time + variance, 1)

    def traffic_distribution(self) -> dict:
        #todo: use weather
        weather = self.graph.weather
        weather_types = ["rain", "sunny", "hot", "freezing"]
        day = self.graph.day
        month = self.graph.month
        if not (0 <= day < 30) or not (0 <= month < 12):
            raise ValueError("invalid date")
        distribution = {
            "car": 0.3,
            "truck": 0.03,
            "foot": 0.37,
            "bicycle": 0.22,
            "motor_bike": 0.08,
        }
        if 5 <= month <= 8:
            distribution["bicycle"] += 0.15
            distribution["foot"] += 0.15
            distribution["car"] -= 0.2
        elif month == 11 or month <= 1:
            distribution["car"] += 0.3
            distribution["bicycle"] -= 0.15
            distribution["foot"] -= 0.15
        if day % 7 < 5:
            distribution["truck"] += 0.02
            distribution["car"] += 0.08
            distribution["foot"] -= 0.1
        else:
            distribution["bicycle"] += 0.1
            distribution["foot"] += 0.03
            distribution["truck"] -= 0.13
        total = sum(distribution.values())
        distribution = {k: v / total for k, v in distribution.items()}
        print(distribution)
        return distribution

    def traffic_activity(self):
        p_morning = 0.6
        sigma_morning = 1.5
        p_noon = 0.35
        sigma_noon = 1.0
        p_evening = 0.6
        sigma_evening = 1.5
        baseline = 0.05
        t = self.graph.day_time
        y = (p_morning * np.exp(-((t - 8) ** 2) / (2 * sigma_morning ** 2)) +
             p_noon * np.exp(-((t - 12) ** 2) / (2 * sigma_noon ** 2)) +
             p_evening * np.exp(-((t - 17) ** 2) / (2 * sigma_evening ** 2)) +
             baseline)
        return y

    def is_active(self, move=False):
        if self.active_time:
            if move:
                self.active_time -= 1
            return True
        if not move:
            return False
        chance = self.traffic_activity()
        if random.random() > chance:
            return False
        self.active_time = random.randint(4, 8)
        distribution = self.traffic_distribution()

        types = list(distribution.keys())
        probabilities = list(distribution.values())
        self.type = random.choices(types, weights=probabilities, k=1)[0]
        if self.type == "car" or self.type == "truck" or self.type == "motor_bike":
            self.meters_per_sec = 10
        elif self.type == "bicycle":
            self.meters_per_sec = 3
        elif self.type == "foot":
            self.meters_per_sec = 1
        return True

    #participant changes destination goal(used when prev destionation was reached)
    def new_target(self):
        possible_targets = [neighbor for neighbor in self.target.neighbors if neighbor.id != self.cur.id]
        if not possible_targets:
            old_target = self.target
            self.target = self.cur
            self.cur = old_target
            self.distance_meters = 0
            self.passed_meters = 0
            return
        weights = [neighbor.weight for neighbor in possible_targets]
        self.cur = self.target
        self.target = random.choices(possible_targets, weights=weights, k=1)[0]

        self.x = self.target.x
        self.y = self.target.y
        self.passed_meters = 0
        self.passed_coords = 0

        dx = self.target.x - self.cur.x
        dy = self.target.y - self.cur.y
        self.dx_coords = dx
        self.dy_coords = dy
        total_distance = math.hypot(dx, dy)  # Edge length
        if total_distance != 0:
            self.unit_dx = dx / total_distance
            self.unit_dy = dy / total_distance
        else:
            self.unit_dx = 0
            self.unit_dy = 0
        dx_meters = dx * 73 * 1600
        dy_meters = dy * 111.32 * 1600
        self.distance_meters = math.hypot(dx_meters, dy_meters)
        self.total_meters = self.distance_meters

    #participant moves the amount of his speed * time
    def move(self, time=1, speed_scala=1):
        if not self.is_active(move=True):
            return
        self.active_time -= time
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
        self.distance_to_center = 0
        self.weight = 1

    #if the node is not a sensor returns an empty list
    #returns a list of the participants in the radius if it is a sensor
    #currently a sensor has a 360 fov
    def detect(self, radius=10):
        detects = []
        if not self.is_sensor:
            return detects
        for participant in self.graph.participants:
            if not participant.is_active():
                continue
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
    def __init__(self,
                 #[(type, count, meters per sec), <more types>
                 #participants=[("car", 10, 10)],
                 participants=400,
                 #simulation speed
                 speed=1,
                 #where is the simulation:
                 x=49.007706, y=8.394864, radius_meters=400):
        self.speed = speed
        self.nodes = {}
        self.participants = []
        self.center_x = x
        self.center_y = y
        self.day_time = 0
        self.day = 0
        self.month = 0
        self.weather = "sunny"
        self.weather_duration = 5

        self.add_intersections(x, y, radius_meters)
        self.compute_node_distances_and_weights()
        node_ids = list(self.nodes.keys())
        id = 0
        #for participant in participants:
        #    type, count, meters_per_sec = participant
        i = 0
        while i < participants:
            random_node_id = random.choice(node_ids)
            participant_obj = Participant(self, random_node_id, type, id)
            id += 1
            i += 1
            self.participants.append(participant_obj)

    def add_intersections(self, center_lat, center_lon, radius_meters=400):
        G = ox.graph_from_point((center_lat, center_lon), dist=radius_meters, network_type='drive')
        osm_id_to_node = {}
        for node_id, node_data in G.nodes(data=True):
            unique_id = f"node_{node_id}"
            lat = node_data['y']
            lon = node_data['x']
            if unique_id not in self.nodes:
                node = Node(self, unique_id, lat, lon)
                osm_id_to_node[node_id] = node
                self.nodes[unique_id] = node

        for u, v, data in G.edges(data=True):
            node_u = osm_id_to_node.get(u)
            node_v = osm_id_to_node.get(v)
            if node_u and node_v:
                node_u.connect(node_v)

    def compute_node_distances_and_weights(self):
        max_distance = 0
        for node in self.nodes.values():
            dx = (node.x - self.center_x) * 73 * 1600
            dy = (node.y - self.center_y) * 111.32 * 1600
            distance = math.hypot(dx, dy)
            node.distance_to_center = distance
            if distance > max_distance:
                max_distance = distance

        for node in self.nodes.values():
            normalized_distance = node.distance_to_center / max_distance
            node.weight = 1 + 2 * (1 - normalized_distance)  # from 3(center)-1(outer)

    def get_participants_positions(self):
        positions = []
        for participant in self.participants:
            if not participant.is_active():
                continue
            participant_info = {
                'TYPE': participant.type,
                'ID': participant.id,
                'X': participant.x,
                'Y': participant.y,
                'Current Node': participant.cur.id,
                'Target Node': participant.target.id,
                'Distance to Target': participant.distance_meters,
            }
            positions.append(participant_info)
        return positions

    def print_participants_positions(self):
        positions = self.get_participants_positions()
        print("Current Participants Positions:")
        for participant_info in positions:
            print(f"Type: {participant_info['TYPE']}, ID: {participant_info['ID']}, "
                  f"X: {participant_info['X']}, Y: {participant_info['Y']}, "
                  f"Current Node: {participant_info['Current Node']}, "
                  f"Target Node: {participant_info['Target Node']}, "
                  f"Distance to Target: {participant_info['Distance to Target']:.2f} meters")
        print("-" * 40)

    def get_sensor_list(self, sensor_meter_radius=10):
        sensor_list = []
        for node in self.nodes.values():
            if node.is_sensor:
                detects = node.detect(sensor_meter_radius)
                detected_participants = [
                    {
                        "TYPE": participant.type,
                        "ID": participant.id,
                        "X": participant.x,
                        "Y": participant.y,
                    }
                    for participant in detects
                ]
                sensor_info = {
                    "ID": node.id,
                    "X": node.x,
                    "Y": node.y,
                }
                sensor_list.append((sensor_info, detected_participants))
        return sensor_list

    def print_sensor_data(self, radius=10):
        sensor_list = self.get_sensor_list(radius)
        for sensor_info, detected_participants in sensor_list:
            if not detected_participants:
                continue  # Use continue instead of return
            print(f"Sensor ID: {sensor_info['ID']}")
            print(f"  Coordinates: ({sensor_info['X']}, {sensor_info['Y']})")
            if detected_participants:
                print("  Detected Participants:")
                for participant in detected_participants:
                    print(f"    - Type: {participant['TYPE']}, "
                          f"ID: {participant['ID']}, "
                          f"Coordinates: ({participant['X']}, {participant['Y']})")
            else:
                print(" no participants in sensor range")
            print("-" * 40)

    def get_enviormental_data(self):
        data = {}
        data["HOUR"] = self.day_time
        data["DAY"] = self.day #0-29
        data["MONTH"] = self.MONTH #0-11
        data["WEATHER"] = self.weather #"rain", "sunny", "hot", "freezing"
        #todo: measure destribution of types
        destribution = {}
        data["DESTRIBUTION"] = destribution

    def print_enviormental_data(self):
        data = self.get_enviormental_data()
        print(data)

    def add_node(self, new_node):
        self.nodes[new_node.id] = new_node

    def weather_prediction(self):
        day = self.day
        month = self.month
        if not (0 <= day < 30) or not (0 <= month < 12):
            return "Invalid input"
        weather_types = ["rain", "sunny", "hot", "freezing"]
        if month in [11, 0, 1]:
            probabilities = [0.3, 0.2, 0.0, 0.5]  # rain, sunny, hot, freezing
        elif month in [2, 3, 4]:
            probabilities = [0.4, 0.4, 0.2, 0.1]
        elif month in [5, 6, 7]:
            probabilities = [0.2, 0.5, 0.3, 0.0]
        elif month in [8, 9, 10]:
            probabilities = [0.5, 0.3, 0.0, 0.2]
        weather = random.choices(weather_types, weights=probabilities, k=1)[0]
        return weather

    #advance simulation by 1 simulation second
    def pass_time(self, time=1):
        self.day_time += time
        if self.day_time >= 24:
            self.day += 1
            self.day_time = 0
        if self.day >= 30:
            self.month += 1
            self.day = 0
        self.month %= 12
        self.weather_duration -= 1
        if self.weather_duration <= 0:
            #todo:
            self.weather_duration = 5

        for participant in self.participants:
            self.weather = self.weather_prediction()
            participant.move(time, self.speed)

    #prints the current cars in sensor ranges
    #old version, of print_sensor_data, should print the same cases as print_sensor_data
    def print_detects(self, range=10):
        for node in self.nodes.values():
            detects = node.detect(range)
            for participant in detects:
                print(node.id, ": ", participant.type, "(id: ", participant.id, ")")

def get_large_graph():
    #"car", "truck","foot", "bicycle","motor_bike"
    #participant_list = [("car", 400, 10), ("truck", 20, 10), ("foot", 400, 1), ("bicycle", 400, 2), ("motor_bike", 40, 10)]
    #graph = Graph(speed=5, participants=participant_list, x=49.00587, y=8.40162, radius_meters=3000)
    graph = Graph(speed=5, participants=600, x=49.00587, y=8.40162, radius_meters=3000)
    return graph


if __name__ == '__main__':
    #graph = Graph()
    graph = get_large_graph()
    #graph.print_detects()
    passed_time = 0
    ids_in_range = diagram.get_ids(graph)
    all_time_stamps = []
    while 1:
        all_time_stamps.append(diagram.filter_sensors(graph, ids_in_range))
        diagram.animation1(all_time_stamps)

        graph.pass_time()
        #graph.print_participants_positions()
        #graph.print_sensor_data(10)
        passed_time += 1
        print("passed time: ", passed_time)
        print("day time: ", graph.day_time)
        #time.sleep(1)




