import json
import numpy as np
import METANET_simulation


def get_initial_state(data, config, prediction_horizon):

    freeway_num_cells, total_num_cells = METANET_simulation.get_number_of_cells(config)

    initial_state = {}
    initial_state["flow"] = np.zeros((total_num_cells, ))
    initial_state["density"] = np.zeros((total_num_cells, ))
    initial_state["speed"] = np.zeros((total_num_cells, ))
    initial_state["num_vehicles"] = np.zeros((total_num_cells, ))

    initial_state["flow"][0] = data[0]
    initial_state["flow"][1: 6] = data[1: 6]
    initial_state["flow"][6] = data[5]
    initial_state["flow"][8] = data[11]
    initial_state["flow"][9] = data[11]
    initial_state["flow"][10] = data[13]

    initial_state["speed"][1: 6] = data[6: 11]
    initial_state["speed"][6] = data[10]
    initial_state["speed"][10] = data[14]

    initial_state["density"][1: 7] = initial_state["flow"][1: 7] / initial_state["speed"][1: 7]
    initial_state["density"][10] = initial_state["flow"][10] / initial_state["speed"][10]
    initial_state["num_vehicles"][0] = data[0] / 720
    initial_state["num_vehicles"][8] = data[11] / 720
    initial_state["num_vehicles"][9] = data[11] / 720

    demand = np.zeros((len(config["link_properties"]), prediction_horizon))
    demand[0, :] = data[0]
    demand[2, :] = data[11]

    return initial_state, demand


def get_feasible_control_action(rl_data, traffic_flow_data, data, critical_merge_density):

    red_time = rl_data[traffic_flow_data.index(data)][1]
    state = rl_data[traffic_flow_data.index(data)][0]
    if state[1] >= critical_merge_density:
        feasible_control_actions = [red_time, red_time + 2, red_time + 4]
    else:
        feasible_control_actions = [red_time, red_time - 2, red_time - 4]

    return feasible_control_actions


if __name__ == "__main__":

    with open("traffic_flow_data.json", 'r') as json_file:
        traffic_flow_data = json.load(json_file)
    with open("rl_data.json", 'r') as json_file:
        rl_data = json.load(json_file)
    with open('parameters.json', 'r') as json_file:
        parameters = json.load(json_file)
    with open("config.json", 'r') as json_file:
        config = json.load(json_file)

    prediction_horizon = 4
    critical_merge_density = 30
    min_red = 2
    max_red = 18
    cycle = 20

    for data in traffic_flow_data:
        initial_state, demand = get_initial_state(data, config, prediction_horizon)
        feasible_control_actions = get_feasible_control_action(rl_data, traffic_flow_data, data, critical_merge_density)

        for control_action in feasible_control_actions:
            if min_red <= control_action <= max_red:
                metering_rate = (cycle - control_action) / cycle * parameters["link_capacity"][2]
                density, flow, speed, num_vehicles, num_lanes = METANET_simulation.traffic_dynamics(config, prediction_horizon, demand, parameters, initial_state, metering_rate)
