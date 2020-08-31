from __future__ import division
import math
import json
import numpy as np
import scipy.optimize as op
import METANET_simulation


def data_reverse(data):

    new_data = np.zeros((np.size(data, 0), np.size(data, 1)))
    for row_idx in range(np.size(data, 0)):
        new_data[row_idx, :] = data[-row_idx - 1, :]
    new_data[0: -1, :] = new_data[1:, :]
    for row_idx in range(np.size(new_data, 0)):
        for column_idx in range(np.size(new_data, 1)):
            if not new_data[row_idx, column_idx] > 0:
                new_data[row_idx, column_idx] = (new_data[row_idx, column_idx - 1] + new_data[row_idx, column_idx + 1]) / 2

    return new_data


def get_initial_state(config, flow_data, speed_data, ramp_flow, ramp_speed, ramp_queue, demand):

    freeway_num_cells, total_num_cells = METANET_simulation.get_number_of_cells(config)

    initial_state = {}
    initial_state["flow"] = np.zeros((total_num_cells, ))
    initial_state["density"] = np.zeros((total_num_cells, ))
    initial_state["speed"] = np.zeros((total_num_cells, ))
    initial_state["num_vehicles"] = np.zeros((total_num_cells, ))

    initial_state["flow"][0] = demand[0, 1] * 720
    initial_state["flow"][1: 3] = flow_data[1:3, 1] / 3
    initial_state["flow"][3: 5] = flow_data[3:5, 1] / 4
    initial_state["flow"][5: 7] = flow_data[5:7, 1] / 3
    initial_state["flow"][8] = demand[2, 1] * 720
    initial_state["flow"][9] = demand[2, 1] * 720
    initial_state["flow"][10] = ramp_flow[1] / 2

    initial_state["speed"][1: 7] = speed_data[:, 1]
    initial_state["speed"][10] = ramp_speed[1] * 3.6

    initial_state["density"][1: 7] = initial_state["flow"][1: 7] / initial_state["speed"][1: 7]
    initial_state["density"][10] = initial_state["flow"][10] / initial_state["speed"][10]
    initial_state["num_vehicles"][0] = demand[0, 1]
    initial_state["num_vehicles"][8] = demand[2, 1]
    initial_state["num_vehicles"][9] = demand[2, 1]

    return initial_state


def cali_METANET(initial):

    with open("config.json", 'r') as json_file:
        config = json.load(json_file)

    flow_data = np.load('flow.npy')
    ramp_flow = flow_data[-1, :] * 60
    flow_data = data_reverse(flow_data) * 60

    speed_data = np.load('speed.npy')
    ramp_speed = speed_data[-1, :]
    speed_data = data_reverse(speed_data) * 3.6
    ramp_queue = np.load("ramp_queue.npy")

    demand = np.zeros((len(config["link_properties"]), 720))
    demand_data = np.load('demand.npy')
    duration_demand_change = 120 # 10 min

    for idx in range(6):
        demand[0, duration_demand_change * idx: duration_demand_change * (idx + 1)] = demand_data[idx, 0] / 720
        demand[2, duration_demand_change * idx: duration_demand_change * (idx + 1)] = demand_data[idx, 1] / 720
    initial_state = get_initial_state(config, flow_data, speed_data, ramp_flow, ramp_speed, ramp_queue, demand)

#    speed_data_minute = np.zeros((np.size(speed_data, 0), int(np.size(speed_data, 1) / 3)))
#    flow_data_minute = np.zeros((np.size(flow_data, 0), int(np.size(flow_data, 1) / 3)))

#    for row_idx in range(np.size(speed_data_minute, 0)):
#        for column_idx in range(np.size(speed_data_minute, 1)):
#            speed_data_minute[row_idx, column_idx] = sum(speed_data[row_idx, column_idx * 3: (column_idx + 1) * 3]) / 3
#            flow_data_minute[row_idx, column_idx] = sum(flow_data[row_idx, column_idx * 3: (column_idx + 1) * 3]) / 3

    with open('parameters.json', 'r') as json_file:
        parameters = json.load(json_file)
    parameters["duration_time_step"] = parameters["duration_time_step"] / 3600
    parameters["tao"] = parameters["tao"] / 3600
    parameters['am'] = initial[0]
    parameters['free_speed'] = initial[1]
    parameters['capacity'] = initial[2]
    parameters['fai'] = initial[3]
    parameters['delta'] = initial[4]
    parameters['cri_density'] = parameters["capacity"] / (parameters['free_speed'] * math.exp(-1 / parameters['am']))

    density, flow, speed, num_vehicles, num_lanes = METANET_simulation.traffic_dynamics(config, 720, demand, parameters, initial_state, 1)

    simulated_flow = flow[1: 7, :]
    simulated_speed = speed[1: 7, :]
    flow_data_lane = np.zeros((np.size(flow_data, 0), np.size(flow_data, 1)))
    flow_data_lane[0: 2, :] = flow_data[0: 2, :] / 3
    flow_data_lane[2: 4, :] = flow_data[2: 4, :] / 4
    flow_data_lane[4: 6, :] = flow_data[4: 6, :] / 3

    ave_flow = sum(sum(flow_data_lane[:, :])) / (np.size(flow_data_lane, 0) * np.size(flow_data_lane, 1))
    ave_speed = sum(sum(simulated_speed[:, :])) / (np.size(simulated_speed, 0) * np.size(simulated_speed, 1))

    flow_array = np.zeros((np.size(flow_data, 0), np.size(flow_data, 1)))
    speed_array = np.zeros((np.size(speed_data, 0), np.size(speed_data, 1)))

    for row_idx in range(np.size(speed_array, 0)):
        for column_idx in range(np.size(speed_array, 1)):
            speed_array[row_idx, column_idx] = sum(simulated_speed[row_idx, column_idx * 12: (column_idx + 1) * 12]) / 12
            flow_array[row_idx, column_idx] = sum(simulated_flow[row_idx, column_idx * 12: (column_idx + 1) * 12]) / 12

    flow_loss_all = 0
    speed_loss_all = 0
    total_points = 0

    for row_idx in range(np.size(flow_data, 0)):
        for column_idx in range(5, 55):
            flow_loss_all += (flow_data_lane[row_idx, column_idx] - flow_array[row_idx, column_idx]) * (flow_data_lane[row_idx, column_idx] - flow_array[row_idx, column_idx])
            speed_loss_all += (speed_data[row_idx, column_idx] - speed_array[row_idx, column_idx]) * (speed_data[row_idx, column_idx] - speed_array[row_idx, column_idx])
            total_points += 1

    flow_error = math.sqrt(flow_loss_all / total_points) / ave_flow
    speed_error = math.sqrt(speed_loss_all / total_points) / ave_speed
    Loss = flow_error + speed_error

    return Loss


if __name__ == "__main__":

    initial = np.array([1.367, 108.6, 1679.8, 0.527, 2.54])
    result = op.minimize(cali_METANET, initial, method='nelder-mead', options={'xtol': 1e-8, 'disp': True})
    print result