from __future__ import division
import math
import json
import numpy as np
import draw_figures


def get_number_of_cells(config):

    total_num_cells = 0
    freeway_num_cells = 0

    for link_idx in range(len(config["link_properties"])):
        if config["link_properties"][link_idx] == "freeway":
            freeway_num_cells += len(config["cell_length"][link_idx])
        total_num_cells += len(config["cell_length"][link_idx])

    return freeway_num_cells, total_num_cells


def get_cell_properties(config):

    cell_indices, num_lanes, cell_types, cell_lengths, link_indices = [], [], [], [], []
    idx = 0

    for link_idx in range (len(config["cell_length"])):
        for cell_idx in range(len(config["cell_length"][link_idx])):
            cell_indices.append(idx)
            num_lanes.append(config["num_lanes"][link_idx][cell_idx])
            cell_types.append(config["cell_properties"][link_idx][cell_idx])
            cell_lengths.append(config["cell_length"][link_idx][cell_idx])
            link_indices.append(link_idx)
            idx += 1

    return cell_indices, num_lanes, cell_types, cell_lengths, link_indices


def get_cell_idx_from_upstream_link(link_idx, config):

    cell_idx = 0
    for idx in range(link_idx + 1):
        cell_idx += len(config["cell_length"][idx])

    return cell_idx - 1


def get_cell_idx_from_downstream_link(link_idx, config):

    cell_idx = 0
    for idx in range(link_idx):
        cell_idx += len(config["cell_length"][idx])

    return cell_idx


def find_cells_indices_from_nodes(config):

    cell_indices_node = []
    for node in config["nodes_connections"]:
        upstream_links = node[0]
        downstream_links = node[1]

        upstream_cells, downstream_cells = [], []
        for link in upstream_links:
            cell_idx = get_cell_idx_from_upstream_link(link, config)
            upstream_cells.append(cell_idx)
        for link in downstream_links:
            cell_idx = get_cell_idx_from_downstream_link(link, config)
            downstream_cells.append(cell_idx)

        cell_indices_node.append([upstream_cells, downstream_cells])

    return cell_indices_node


def get_nodes_connected_cells(config):

    nodes_connected_cells = {}
    cell_indices_node = find_cells_indices_from_nodes(config)
    for node_type in config["nodes_properties"]:
        node_idx = config["nodes_properties"].index(node_type)
        if node_type not in nodes_connected_cells:
            nodes_connected_cells[node_type] = {}

        if node_type == "merge":
            key = str(cell_indices_node[node_idx][1][0])
            nodes_connected_cells[node_type][key] = cell_indices_node[node_idx][0]

        if node_type == "diverge":
            key = str(cell_indices_node[node_idx][0][0])
            nodes_connected_cells[node_type][key] = cell_indices_node[node_idx][1]

    return nodes_connected_cells


def state_initialization(config, num_step, initial_state):

    freeway_num_cells, total_num_cells = get_number_of_cells(config)
    density = np.zeros((total_num_cells, num_step))
    flow = np.zeros((total_num_cells, num_step))
    speed = np.zeros((total_num_cells, num_step))
    num_vehicles = np.zeros((total_num_cells, num_step))
    if initial_state != "":
        density[:, 0] = initial_state["density"]
        flow[:, 0] = initial_state["flow"]
        speed[:, 0] = initial_state["speed"]
        num_vehicles[:, 0] = initial_state["num_vehicles"]

    return density, flow, speed, num_vehicles


def state_update_origin(demand, num_vehicles, parameters, num_lanes, cell_idx, link_idx, step_num, config, density, flow):

    incoming_vehicles = demand[link_idx][step_num]
    outflow_max = num_vehicles[cell_idx][step_num] / parameters["duration_time_step"]
    if config["link_properties"][link_idx] != "freeway":
        outflow_capacity = parameters["link_capacity"][link_idx]
    else:
        if density[cell_idx, step_num] > parameters["cri_density"]:
            outflow_capacity = parameters["capacity"] * num_lanes[cell_idx + 1] * (density[cell_idx, step_num] - parameters["cri_density"]) / (parameters["jam_density"] - parameters["cri_density"])
        else:
            outflow_capacity = parameters["capacity"] * num_lanes[cell_idx + 1]
    outflow = min(outflow_max, outflow_capacity)
    flow[cell_idx, step_num] = outflow
    outgoing_vehicles = outflow * parameters["duration_time_step"]
    num_vehicles[cell_idx, step_num + 1] = num_vehicles[cell_idx, step_num] + incoming_vehicles - outgoing_vehicles

    return num_vehicles, flow


def state_update_store_cells(num_vehicles, cell_idx, step_num, parameters, num_lanes, cell_property, flow, metering_rate, link_idx):

    num_vehicles[cell_idx, step_num + 1] = num_vehicles[cell_idx, step_num] + (flow[cell_idx - 1, step_num] - flow[cell_idx, step_num]) * parameters["duration_time_step"]
    sending_flow = min(num_vehicles[cell_idx - 1, step_num] / parameters["duration_time_step"], parameters["link_capacity"][link_idx])
    if cell_property[cell_idx] == "metering":
        sending_flow = min(num_vehicles[cell_idx - 1, step_num] / parameters["duration_time_step"], parameters["link_capacity"][link_idx] * metering_rate)
    flow[cell_idx, step_num + 1] = sending_flow

    return flow, num_vehicles


def state_update_ramp_normal_cells(density, flow, speed, parameters, num_lanes, cell_idx, step_num, cell_length, nodes_connected_cells):

    # if the most downstream cell of a ramp  is a normal cell
    for key in nodes_connected_cells["merge"]:
        if cell_idx in nodes_connected_cells["merge"][key]:
            downstream_cell = int(key)

    density[cell_idx, step_num + 1] = density[cell_idx, step_num] + (flow[cell_idx - 1, step_num] - flow[cell_idx, step_num] * num_lanes[cell_idx]) * parameters["duration_time_step"] / num_lanes[cell_idx] / cell_length[cell_idx]
    desired_speed = parameters['free_speed'] * math.exp(-1 / parameters['am'] * (density[cell_idx, step_num] / parameters['cri_density']) ** parameters['am'])
    anticipation_term = parameters['vartheta'] * parameters['duration_time_step'] / (parameters['tao'] * cell_length[cell_idx]) * (density[downstream_cell, step_num] - density[cell_idx, step_num]) / (density[cell_idx, step_num] + parameters['kappa'])
    v = speed[cell_idx, step_num] + parameters['duration_time_step'] / parameters['tao'] * (desired_speed - speed[cell_idx, step_num]) - anticipation_term
    v = min(v, parameters['free_speed'])
    v = max(0, v)
    speed[cell_idx, step_num + 1] = v
    flow[cell_idx, step_num + 1] = density[cell_idx, step_num + 1] * speed[cell_idx, step_num + 1]

    return density, speed, flow


def state_update_ramp_store_cells(density, flow, speed, parameters, num_lanes, cell_idx, step_num, cell_length, nodes_connected_cells):

    # if the most downstream cell of a ramp  is a store_and_forward cell
    for key in nodes_connected_cells["merge"]:
        if cell_idx in nodes_connected_cells["merge"][key]:
            downstream_cell = int(key)

    density[cell_idx, step_num + 1] = density[cell_idx, step_num] + (flow[cell_idx - 1, step_num] - flow[cell_idx, step_num] * num_lanes[cell_idx]) * parameters["duration_time_step"] / num_lanes[cell_idx] / cell_length[cell_idx]
    desired_speed = parameters['free_speed'] * math.exp(-1 / parameters['am'] * (density[cell_idx, step_num] / parameters['cri_density']) ** parameters['am'])
    anticipation_term = parameters['vartheta'] * parameters['duration_time_step'] / (parameters['tao'] * cell_length[cell_idx]) * (density[downstream_cell, step_num] - density[cell_idx, step_num]) / (density[cell_idx, step_num] + parameters['kappa'])
    v = speed[cell_idx, step_num] + parameters['duration_time_step'] / parameters['tao'] * (desired_speed - speed[cell_idx, step_num]) - anticipation_term
    v = min(v, parameters['free_speed'])
    v = max(0, v)
    speed[cell_idx, step_num + 1] = v
    flow[cell_idx, step_num + 1] = density[cell_idx, step_num + 1] * speed[cell_idx, step_num + 1]

    return density, speed, flow


def state_update_destination_cells(num_vehicles, cell_idx, step_num, flow, parameters):

    num_vehicles[cell_idx, step_num + 1] = num_vehicles[cell_idx, step_num] + flow[cell_idx - 1, step_num] * parameters["duration_time_step"]
    return num_vehicles


def state_update_merging_and_lanedrop_cells(density, flow, speed, cell_idx, step_num, num_lanes, cell_length, nodes_connected_cells, parameters, cell_property):

    if cell_property[cell_idx] in ["merge", "merge_and_lane_drop"]:
        upstream_cells = nodes_connected_cells["merge"][str(cell_idx)]
        density[cell_idx, step_num + 1] = density[cell_idx, step_num] + (flow[upstream_cells[0], step_num] * num_lanes[upstream_cells[0]] + flow[upstream_cells[1], step_num] * num_lanes[upstream_cells[1]] - flow[cell_idx, step_num] * num_lanes[cell_idx]) * parameters["duration_time_step"] / num_lanes[cell_idx] / cell_length[cell_idx]
    else:
        density[cell_idx, step_num + 1] = density[cell_idx, step_num] + (flow[cell_idx - 1, step_num] * num_lanes[cell_idx - 1] - flow[cell_idx, step_num] * num_lanes[cell_idx]) * parameters["duration_time_step"] / num_lanes[cell_idx] / cell_length[cell_idx]

    desired_speed = parameters['free_speed'] * math.exp(-1 / parameters['am'] * (density[cell_idx, step_num] / parameters['cri_density']) ** parameters['am'])
    anticipation_term = parameters['vartheta'] * parameters['duration_time_step'] / (parameters['tao'] * cell_length[cell_idx]) * (density[cell_idx + 1, step_num] - density[cell_idx, step_num]) / (density[cell_idx, step_num] + parameters['kappa'])
    v = speed[cell_idx, step_num] + parameters['duration_time_step'] / parameters['tao'] * (desired_speed - speed[cell_idx, step_num]) - anticipation_term + + parameters['duration_time_step'] / cell_length[cell_idx] * speed[cell_idx, step_num] * (speed[cell_idx - 1, step_num] - speed[cell_idx, step_num])

    if cell_property[cell_idx] == "lane_drop":
        dropped_lanes = max(1, num_lanes[cell_idx - 1] - num_lanes[cell_idx])
        lane_drop_term = parameters["fai"] * parameters["duration_time_step"] / (cell_length[cell_idx] * num_lanes[cell_idx]) * (dropped_lanes * density[cell_idx, step_num] / parameters["cri_density"]) * speed[cell_idx, step_num] * speed[cell_idx, step_num]
        v -= lane_drop_term
    elif cell_property[cell_idx] == "merge":
        redundant_flow = redundant_merging_flow(cell_idx, num_lanes, nodes_connected_cells, flow, step_num, parameters)
        merging_term = parameters["delta"] * parameters["duration_time_step"] / (cell_length[cell_idx] * num_lanes[cell_idx]) * (redundant_flow * speed[cell_idx, step_num]) / (density[cell_idx, step_num] + parameters["kappa"])
        v -= merging_term
    elif cell_property[cell_idx] == "merge_and_lane_drop":
        dropped_lanes = num_lanes[cell_idx] - num_lanes[cell_idx + 1]
        lane_drop_term = parameters["fai"] * parameters["duration_time_step"] / (cell_length[cell_idx] * num_lanes[cell_idx]) * (dropped_lanes * density[cell_idx, step_num] / parameters["cri_density"]) * speed[cell_idx, step_num] * speed[cell_idx, step_num]
        redundant_flow = redundant_merging_flow(cell_idx, num_lanes, nodes_connected_cells, flow, step_num, parameters)
        merging_term = parameters["delta"] * parameters["duration_time_step"] / (cell_length[cell_idx] * num_lanes[cell_idx]) * (redundant_flow * speed[cell_idx, step_num]) / (density[cell_idx, step_num] + parameters["kappa"])
        v = v - merging_term - lane_drop_term

    speed[cell_idx, step_num + 1] = v
    flow[cell_idx, step_num + 1] = density[cell_idx, step_num + 1] * speed[cell_idx, step_num + 1]

    return density, speed, flow


def state_update_freeway_cells(density, flow, speed, parameters, cell_idx, step_num, cell_length, num_lanes, cell_property):

    if cell_property[cell_idx - 1] not in ["normal", "merge", "lane_drop", "merge_and_lane_drop"]:
        density[cell_idx, step_num + 1] = density[cell_idx, step_num] + (flow[cell_idx - 1, step_num] - flow[cell_idx, step_num] * num_lanes[cell_idx]) * parameters["duration_time_step"] / num_lanes[cell_idx] / cell_length[cell_idx]
    else:
        density[cell_idx, step_num + 1] = density[cell_idx, step_num] + (flow[cell_idx - 1, step_num] * num_lanes[cell_idx - 1] - flow[cell_idx, step_num] * num_lanes[cell_idx]) * parameters["duration_time_step"] / num_lanes[cell_idx] / cell_length[cell_idx]
    desired_speed = parameters['free_speed'] * math.exp(-1 / parameters['am'] * (density[cell_idx, step_num] / parameters['cri_density']) ** parameters['am'])
    anticipation_term = parameters['vartheta'] * parameters['duration_time_step'] / (parameters['tao'] * cell_length[cell_idx]) * (density[cell_idx + 1, step_num] - density[cell_idx, step_num]) / (density[cell_idx, step_num] + parameters['kappa'])
    if cell_idx == 1:
        v = speed[cell_idx, step_num] + parameters['duration_time_step'] / parameters['tao'] * (desired_speed - speed[cell_idx, step_num]) - anticipation_term
    else:
        v = speed[cell_idx, step_num] + parameters['duration_time_step'] / parameters['tao'] * (desired_speed - speed[cell_idx, step_num]) - anticipation_term + + parameters['duration_time_step'] / cell_length[cell_idx] * speed[cell_idx, step_num] * (speed[cell_idx - 1, step_num] - speed[cell_idx, step_num])

    v = min(v, parameters['free_speed'])
    v = max(0, v)
    speed[cell_idx, step_num + 1] = v
    flow[cell_idx, step_num + 1] = density[cell_idx, step_num + 1] * speed[cell_idx, step_num + 1]

    return density, speed, flow


def redundant_merging_flow(cell_idx, num_lanes, nodes_connected_cells, flow, step_num, parameters):

    num_dedicated_lanes = num_lanes[cell_idx] - num_lanes[cell_idx - 1]
    merge_cell = nodes_connected_cells["merge"][str(cell_idx)][-1]
    merging_flow = flow[merge_cell, step_num]
    redundant_flow = max(0, merging_flow - num_dedicated_lanes * parameters["capacity"])

    return redundant_flow


def state_update(config, density, flow, speed, num_vehicles, step_idx, cell_idx, link_idx, demand, cell_property, num_lanes, cell_length, nodes_connected_cells, parameters, metering_rate):

    if cell_property[cell_idx] == 'origin':
        num_vehicles, flow = state_update_origin(demand, num_vehicles, parameters, num_lanes,  cell_idx, link_idx, step_idx, config, density, flow)
    if cell_property[cell_idx] == "normal":
        density, speed, flow = state_update_freeway_cells(density, flow, speed, parameters, cell_idx, step_idx, cell_length, num_lanes, cell_property)
    if cell_property[cell_idx] in ['merge', "lane_drop", "merge_and_lane_drop"]:
        density, speed, flow  = state_update_merging_and_lanedrop_cells(density, flow, speed, cell_idx, step_idx, num_lanes, cell_length, nodes_connected_cells, parameters, cell_property)
    if cell_property[cell_idx] in ["store", "metering"]:
        flow, num_vehicles = state_update_store_cells(num_vehicles, cell_idx, step_idx, parameters, num_lanes, cell_property, flow, metering_rate, link_idx)
    if cell_property[cell_idx] == "destination":
        num_vehicles = state_update_destination_cells(num_vehicles, cell_idx, step_idx, flow, parameters)
    if cell_property[cell_idx] == "ramp_normal":
        density, speed, flow = state_update_ramp_normal_cells(density, flow, speed, parameters, num_lanes, cell_idx, step_idx, cell_length, nodes_connected_cells)

    return density, flow, speed, num_vehicles


def traffic_dynamics(config, num_step, demand, parameters, initial_state):

    density, flow, speed, num_vehicles = state_initialization(config, num_step, initial_state)
    cell_indices, num_lanes, cell_types, cell_lengths, link_indices = get_cell_properties(config)
    nodes_connected_cells = get_nodes_connected_cells(config)
    metering_rate = 1

    for step_idx in range(num_step - 1):
        for cell_idx in cell_indices:
            link_idx = link_indices[cell_idx]
            density, flow, speed, num_vehicles = state_update(config, density, flow, speed, num_vehicles, step_idx, cell_idx, link_idx, demand, cell_types, num_lanes, cell_lengths, nodes_connected_cells, parameters, metering_rate)

    return density, flow, speed, num_vehicles, num_lanes


def traffic_demand_input(num_step, config):

    demand = np.zeros((len(config["link_properties"]), num_step))
    demand[0, :] = 5
    demand[2, :] = 1

    return demand


if __name__ == "__main__":

    with open("config.json", 'r') as json_file:
        config = json.load(json_file)
    with open("parameters.json", 'r') as json_file:
        parameters = json.load(json_file)

    parameters["duration_time_step"] = parameters["duration_time_step"] / 3600
    parameters["tao"] = parameters["tao"] / 3600

    num_step = int(parameters["simulation_period"] / parameters["duration_time_step"])
    demand = traffic_demand_input(num_step, config)
    density, flow, speed, num_vehicles, num_lanes = traffic_dynamics(config, num_step, demand, parameters)

    draw_figures.plot_speed_contour(speed, parameters, config)
    draw_figures.plot_density_contour(density, parameters, config)
    draw_figures.plot_flow_contour(flow, parameters, config)