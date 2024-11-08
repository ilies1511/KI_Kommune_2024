from typing import List, Dict
import osmnx as ox
import math
import random
import time
import diagram
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

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
        self.active_time = 5#random.randint(4, 8)
        distribution = self.graph.traffic_pred
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
                 x=49.007706, y=8.394864, radius_meters=400,
                 loop_year=True#used as an exit conditions for simulation for 1 year
        ):
        self.loop_year = loop_year
        self.speed = speed
        self.nodes = {}
        self.participants = []
        self.year_data = []
        self.center_x = x
        self.center_y = y
        self.day_time = 0
        self.day = 0
        self.month = 0
        self.weather = "sunny"
        self.weather_duration = 5
        self.traffic_pred = self.predict_traffic_distribution()

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

    def predict_traffic_distribution(self) -> dict:
        weather = self.weather
        #weather_types = ["rain", "sunny", "hot", "freezing"]
        day = self.day
        month = self.month
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
            distribution["bicycle"] += 0.1
            distribution["foot"] += 0.1
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
            distribution["foot"] += distribution["truck"]
            distribution["truck"] = 0
        # weather
        if weather == "rain":
            distribution["car"] += 0.09
            distribution["foot"] -= 0.05
            distribution["bicycle"] -= 0.04
        elif weather == "hot" or weather == "sunny":
            too_add = distribution["car"] / 2
            distribution["car"] /= 2
            distribution["foot"] += too_add / 2
            distribution["bicycle"] += too_add / 2
        elif weather == "freezing":
            too_add = distribution["motor_bike"]
            distribution["motor_bike"] = 0
            distribution["car"] += 0.12 + too_add
            distribution["bicycle"] -= 0.07
            distribution["foot"] -= 0.05
        total = sum(distribution.values())
        for key, val in distribution.items():
            if val < 0 or val > 1.001:
                print(key)
                print(val)
                print(total)
                print(weather)
                print(month)
                print('')
        if (total < 0.99 or total > 1.0001):
            print(total)
            print(weather)
            print(month)
            print('')
            time.sleep(120)

        #print(total)
        distribution = {k: v / total for k, v in distribution.items()}
        if (total < 0.99 or total > 1.0001):
            print("wrong total after fix")
        return distribution

    def collect_year_data(self):
        """Collects DESTRIBUTION_REAL data over time for year progression analysis."""
        env_data = self.get_enviormental_data()
        self.year_data.append(env_data)

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

    def get_detected_participants_positions(self, sensor_meter_radius=10, from_print=False):
        detected_positions = []
        sensor_list = self.get_sensor_list(sensor_meter_radius, from_print)
        detected_ids = set()
        for sensor_info, detected_participants in sensor_list:
            for participant in detected_participants:
                detected_ids.add(participant["ID"])
        for participant in self.participants:
            if participant.id in detected_ids and participant.is_active():
                participant_info = {
                    'TYPE': participant.type,
                    'ID': participant.id,
                    'X': participant.x,
                    'Y': participant.y,
                    'Current Node': participant.cur.id,
                    'Target Node': participant.target.id,
                    'Distance to Target': participant.distance_meters,
                }
                detected_positions.append(participant_info)
        return detected_positions

    def get_participants_positions(self, from_print=False):
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

    def get_sensor_list(self, sensor_meter_radius=10, from_print=False):
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

    def get_actual_distribution(self, from_print=False) -> dict:
        """the actual distribution of participant types using backend data"""
        participants_data = self.get_participants_positions(from_print)
        counts = {"car": 0, "truck": 0, "foot": 0, "bicycle": 0, "motor_bike": 0}
        total_count = 0

        for participant in participants_data:
            participant_type = participant["TYPE"]
            if participant_type in counts:
                counts[participant_type] += 1
                total_count += 1
        if total_count > 0:
            actual_distribution = {k: v / total_count for k, v in counts.items()}
        else:
            actual_distribution = {k: 0 for k in counts.keys()}

        return actual_distribution

    def get_measured_distribution(self, radius=10, from_print=False) -> dict:
        """the distribution based of the sensor reads"""
        sensor_data = self.get_sensor_list(radius, from_print)
        counts = {"car": 0, "truck": 0, "foot": 0, "bicycle": 0, "motor_bike": 0}
        total_count = 0

        for _, detected_participants in sensor_data:
            for participant in detected_participants:
                participant_type = participant["TYPE"]
                if participant_type in counts:
                    counts[participant_type] += 1
                    total_count += 1
        if total_count > 0:
            measured_distribution = {k: v / total_count for k, v in counts.items()}
        else:
            measured_distribution = {k: 0 for k in counts.keys()}
        return measured_distribution

    def get_enviormental_data(self):
        data = {}
        data["HOUR"] = self.day_time
        data["DAY"] = self.day #0-29
        data["MONTH"] = self.month #0-11
        data["WEATHER"] = self.weather #"rain", "sunny", "hot", "freezing"
        #types: "car", "truck", "foot", "bicycle", "motor_bike"
        data["DESTRIBUTION_REAL"] = self.get_actual_distribution(from_print=True) #dict with key:type,value:float 0-1
        data["DESTRIBUTION_MEASURED"] = self.get_measured_distribution(from_print=True) #dict with key:type,value:float 0-1
        return data

    def print_enviormental_data(self):
        #data = self.get_enviormental_data()
        #print(data)
        #print("REAL:")
        print(self.get_actual_distribution(from_print=True))
        #print("MEASURED:")
        #print(self.get_measured_distribution(from_print=True))
        #print("")

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
        self.collect_year_data()
        if self.day_time >= 24:
            self.day += 1
            self.day_time = 0
        if self.day >= 30:
            self.month += 1
            self.day = 0
        if self.loop_year:
            self.month %= 12
        self.weather_duration -= 1
        if self.weather_duration <= 0:
            self.weather_duration = 5
            self.weather = self.weather_prediction()
        for participant in self.participants:
            participant.move(time, self.speed)

    #prints the current cars in sensor ranges
    #old version, of print_sensor_data, should print the same cases as print_sensor_data
    def print_detects(self, range=10):
        for node in self.nodes.values():
            detects = node.detect(range)
            for participant in detects:
                print(node.id, ": ", participant.type, "(id: ", participant.id, ")")

    def plot_actual_vs_measured_distribution(self):
        """Generates a box plot comparing actual vs. measured traffic distribution by type."""
        year_data = self.year_data
    
        # Collect data for plotting
        data = []
        for entry in year_data:
            for traffic_type, real_value in entry['DESTRIBUTION_REAL'].items():
                measured_value = entry['DESTRIBUTION_MEASURED'].get(traffic_type, 0)
                data.append({"type": traffic_type, "Distribution": "Real", "value": real_value})
                data.append({"type": traffic_type, "Distribution": "Measured", "value": measured_value})
    
        # Convert data to a DataFrame for easier plotting with Seaborn
        df = pd.DataFrame(data)
    
        try:
            plt.figure(figsize=(12, 6))
            sns.boxplot(data=df, x="Distribution", y="value", hue="type")
            plt.title("Comparison of Actual vs Measured Traffic Distribution by Type")
            plt.xlabel("Distribution Type")
            plt.ylabel("Traffic Proportion")
            plt.legend(title="Traffic Type", bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            plt.savefig("actual_vs_measured_distribution.png")
            plt.close()
            print("Saved plot as 'actual_vs_measured_distribution.png'")
            
        except Exception as e:
            print(f"Error generating actual vs measured distribution plot: {e}")


    def plot_year_progression(self):
        #each day has 24 hours
        #each month has exacly 30 days
        """Generates a time series line plot for DESTRIBUTION_REAL and DESTRIBUTION_MEASURED
        over the simulation year and saves it to 'Impact_of_Year_Progression.png'."""

        # Set up time steps and participant types
        time_steps = range(len(self.year_data))
        participant_types = ["car", "foot", "bicycle"]#self.year_data[0]['DESTRIBUTION_REAL'].keys()
        real_data_by_type = {ptype: [entry['DESTRIBUTION_REAL'][ptype] for entry in self.year_data] for ptype in participant_types}
        measured_data_by_type = {ptype: [entry['DESTRIBUTION_MEASURED'][ptype] for entry in self.year_data] for ptype in participant_types}

        try:
            plt.figure(figsize=(12, 8))
            
            for ptype in participant_types:
                plt.plot(time_steps, real_data_by_type[ptype], label=f'Real - {ptype}', linestyle='-', alpha=0.7)
                plt.plot(time_steps, measured_data_by_type[ptype], label=f'Measured - {ptype}', linestyle='--', alpha=0.7)

            plt.title("Impact of Year Progression on Traffic Trends (Real vs. Measured)")
            #plt.xlabel("Simulation Time Steps (Hours)")
            plt.xlabel("Month")
            plt.ylabel("Distribution Percentage")

            month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            month_positions = [i * 720 for i in range(12)]
            plt.xticks(month_positions, month_labels)

            plt.legend(title="Participant Type")
            plt.grid(True)

            # Save to file
            plt.savefig("Impact_of_Year_Progression.png")
            plt.close()
            print("Saved plot as 'Impact_of_Year_Progression.png'.")
        except Exception as e:
            print(f"Error generating plot: {e}")

    def plot_hourly_traffic_intensity(self):
        year_data = self.year_data
        """Generates a line plot showing hourly traffic intensity for cars and combined foot/bicycle group."""
    
        # Data aggregation: Summing values for each hour across days and months for "car" and combined "foot"/"bicycle"
        hourly_data = {'HOUR': [], 'Real_Car': [], 'Measured_Car': [], 'Real_FootBicycle': [], 'Measured_FootBicycle': []}
        hours_in_day = 24
    
        # Aggregating hourly data across all entries
        for hour in range(hours_in_day):
            real_car = 0
            measured_car = 0
            real_foot_bicycle = 0
            measured_foot_bicycle = 0
            
            # Collecting data only for the current hour
            for entry in year_data:
                if entry["HOUR"] == hour:
                    real_car += entry['DESTRIBUTION_REAL'].get("car", 0)
                    measured_car += entry['DESTRIBUTION_MEASURED'].get("car", 0)
                    
                    # Combine "foot" and "bicycle" into a single group
                    real_foot_bicycle += entry['DESTRIBUTION_REAL'].get("foot", 0) + entry['DESTRIBUTION_REAL'].get("bicycle", 0)
                    measured_foot_bicycle += entry['DESTRIBUTION_MEASURED'].get("foot", 0) + entry['DESTRIBUTION_MEASURED'].get("bicycle", 0)
            
            # Append aggregated data for each hour
            hourly_data['HOUR'].append(hour)
            hourly_data['Real_Car'].append(real_car)
            hourly_data['Measured_Car'].append(measured_car)
            hourly_data['Real_FootBicycle'].append(real_foot_bicycle)
            hourly_data['Measured_FootBicycle'].append(measured_foot_bicycle)
    
        # Convert the dictionary to a DataFrame for plotting
        df = pd.DataFrame(hourly_data)
    
        try:
            # Plotting the hourly data for both real and measured traffic intensities
            plt.figure(figsize=(12, 6))
            plt.plot(df['HOUR'], df['Real_Car'], label="Real - Car", linestyle='-', marker='o')
            plt.plot(df['HOUR'], df['Measured_Car'], label="Measured - Car", linestyle='--', marker='o')
            plt.plot(df['HOUR'], df['Real_FootBicycle'], label="Real - Foot + Bicycle", linestyle='-', marker='o')
            plt.plot(df['HOUR'], df['Measured_FootBicycle'], label="Measured - Foot + Bicycle", linestyle='--', marker='o')
            
            # Plot aesthetics
            plt.title("Hourly Traffic Intensity: Real vs. Measured")
            plt.xlabel("Hour of Day")
            plt.ylabel("Traffic Intensity (Count)")
            plt.xticks(range(hours_in_day))
            plt.legend(title="Traffic Type")
            plt.grid(True)
    
            # Save the plot as a PNG file
            plt.tight_layout()
            plt.savefig("hourly_traffic_intensity.png")
            plt.close()
            print("Saved plot as 'hourly_traffic_intensity.png'")
            
        except Exception as e:
            print(f"Error generating hourly traffic intensity plot: {e}")

    def plot_weather_impact_on_traffic_distribution(self):
        """Generates a box plot showing the impact of weather on traffic distribution by type."""
        year_data = self.year_data
        # Collect data for plotting
        data = []
        for entry in year_data:
            weather = entry['WEATHER']
            for traffic_type, real_value in entry['DESTRIBUTION_REAL'].items():
                data.append({"type": traffic_type, "weather": weather, "distribution": real_value})
    
        # Convert data to a DataFrame for easier plotting with Seaborn
        df = pd.DataFrame(data)
    
        try:
            plt.figure(figsize=(12, 6))
            sns.boxplot(data=df, x="weather", y="distribution", hue="type")
            plt.title("Impact of Weather on Traffic Distribution by Type")
            plt.xlabel("Weather Condition")
            plt.ylabel("Traffic Distribution Percentage")
            plt.legend(title="Traffic Type", bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            plt.savefig("weather_impact_on_traffic_distribution.png")
            plt.close()
            print("Saved plot as 'weather_impact_on_traffic_distribution.png'")
            
        except Exception as e:
            print(f"Error generating weather impact on traffic distribution plot: {e}")

    #todo: broken
    def estimate_co2_emissions_over_year(self):
        year_data = self.year_data
        """Generates a line plot showing estimated CO₂ emissions over the year."""
    
        # Constants for CO₂ emissions estimation (in grams per unit)
        emission_factors = {
            "car": 120,       # grams per unit
            "motor_bike": 80, # grams per unit
            "truck": 300      # grams per unit
        }
    
        # Initialize dictionary to store daily CO₂ emissions
        daily_emissions = {"Day": [], "Month": [], "Estimated_CO2_Emissions": []}
    
        # Aggregate daily CO₂ emissions by grouping "car", "motor_bike", and "truck"
        for entry in year_data:
            day = entry["DAY"]
            month = entry["MONTH"]
            
            # Estimate emissions for "car", "motor_bike", and "truck" types
            daily_emission = 0
            for vehicle_type, density in entry["DESTRIBUTION_REAL"].items():
                if vehicle_type in emission_factors:
                    daily_emission += density * emission_factors[vehicle_type]
    
            # Store daily emissions data
            daily_emissions["Day"].append(day + month * 30)  # Sequential day count over the year
            daily_emissions["Month"].append(month)
            daily_emissions["Estimated_CO2_Emissions"].append(daily_emission)
    
        # Convert data to a DataFrame for plotting
        df = pd.DataFrame(daily_emissions)
    
        try:
            plt.figure(figsize=(12, 6))
            plt.plot(df["Day"], df["Estimated_CO2_Emissions"], color='green', marker='o', linestyle='-', alpha=0.7)
            plt.title("Estimated CO₂ Emissions Over the Year")
            plt.xlabel("Day of Year")
            plt.ylabel("Estimated CO₂ Emissions per day(proportional comparison)")
            
            # Customize x-axis to show month labels every ~30 days
            month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            month_positions = [(i * 30) + 15 for i in range(12)]
            plt.xticks(month_positions, month_labels)
            
            plt.grid(True)
            
            # Save the plot as a PNG file
            plt.tight_layout()
            plt.savefig("estimated_co2_emissions_over_year.png")
            plt.close()
            print("Saved plot as 'estimated_co2_emissions_over_year.png'")
            
        except Exception as e:
            print(f"Error generating CO₂ emissions plot: {e}")

    #todo: broken
    def plot_traffic_volume_by_hour(self):
        """Generates a bar chart showing the effect of time of day on total traffic volume, comparing real vs. measured data."""
        year_data = self.year_data
    
        # Initialize dictionary to store hourly traffic volume for both real and measured data
        hourly_volume = {'HOUR': [], 'Real_Volume': [], 'Measured_Volume': []}
        hours_in_day = 24
    
        # Aggregate traffic volume by hour
        for hour in range(hours_in_day):
            real_volume = 0
            measured_volume = 0
            
            # Collect traffic data only for the current hour
            for entry in year_data:
                if entry["HOUR"] == hour:
                    # Sum up all traffic participants into a single group
                    real_volume += sum(entry['DESTRIBUTION_REAL'].values())
                    measured_volume += sum(entry['DESTRIBUTION_MEASURED'].values())
    
            # Store hourly volumes
            hourly_volume['HOUR'].append(hour)
            hourly_volume['Real_Volume'].append(real_volume)
            hourly_volume['Measured_Volume'].append(measured_volume)
    
        # Convert data to a DataFrame for easier plotting
        df = pd.DataFrame(hourly_volume)
    
        try:
            # Plotting the traffic volume by hour for both real and measured data
            plt.figure(figsize=(12, 6))
            bar_width = 0.4
            plt.bar(df['HOUR'] - bar_width / 2, df['Real_Volume'], width=bar_width, label="Real Volume", color='blue', alpha=0.6)
            plt.bar(df['HOUR'] + bar_width / 2, df['Measured_Volume'], width=bar_width, label="Measured Volume", color='orange', alpha=0.6)
            
            # Plot aesthetics
            plt.title("Effect of Time of Day on Total Traffic Volume (Real vs. Measured)")
            plt.xlabel("Hour of Day")
            plt.ylabel("Total Traffic Volume")
            plt.xticks(range(hours_in_day))
            plt.legend(title="Data Type")
            plt.grid(axis='y', linestyle='--', alpha=0.7)
    
            # Save the plot as a PNG file
            plt.tight_layout()
            plt.savefig("traffic_volume_by_hour.png")
            plt.close()
            print("Saved plot as 'traffic_volume_by_hour.png'")
            
        except Exception as e:
            print(f"Error generating traffic volume by hour plot: {e}")

def get_large_graph(loop_year=True):
    graph = Graph(speed=1, participants=600, x=49.00587, y=8.40162, radius_meters=3000, loop_year=loop_year)
    return graph

if __name__ == '__main__':
    graph = get_large_graph(loop_year=False)
    graph.month = 0

    while graph.month < 12:
        graph.pass_time()
        #graph.print_enviormental_data()
        #print("hour:", graph.day_time)
        print("day:", graph.day)
        print("month:", graph.month)
    #todo:
    #some plots are broken, some have very unclear output formatting some seem good
    graph.plot_year_progression()
    graph.plot_actual_vs_measured_distribution()
    graph.plot_hourly_traffic_intensity()
    graph.plot_weather_impact_on_traffic_distribution()
    graph.estimate_co2_emissions_over_year()
    graph.plot_traffic_volume_by_hour()

    #if __name__ == '__main__':
    #    #graph = Graph()
    #    graph = get_large_graph()
    #    #graph.print_detects()
    #    passed_time = 0
    #    ids_in_range = diagram.get_ids(graph)
    #    all_time_stamps = []
    #    while 1:
    #        #all_time_stamps.append(diagram.filter_sensors(graph, ids_in_range))
    #        #diagram.animation1(all_time_stamps)
    #
    #        graph.pass_time()
    #        #graph.print_participants_positions()
    #        #graph.print_sensor_data(10)
    #        passed_time += 1
    #        #env_data = graph.get_enviormental_data()
    #        graph.print_enviormental_data()
    #        #print("passed time: ", passed_time)
    #        #print("day time: ", graph.day_time)
    #        #time.sleep(1)
    #



