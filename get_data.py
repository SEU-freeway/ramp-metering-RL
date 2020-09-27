# -*- coding: utf-8 -*-
"""
Created on Thu May 14 17:34:17 2020

@author: Mr.Du
"""

from ALINEA import alinea_control
from generate_random_flow import random_flow
from organize_RLdata import read_detectorout
import numpy as np
import json
import os

flag = 0
queue = []
redtime = []
mainline_set_flow = []
ramp_set_flow = []
detector_list = ['810 SB', '811 SB', '812 SB', '813 SB', '814 SB', 'ramp']
warmup = 600
speed = {'810 SB': [], '811 SB': [], '812 SB': [], '813 SB': [], '814 SB': [], 'ramp': []}
flow = {'810 SB': [], '811 SB': [], '812 SB': [], '813 SB': [], '814 SB': [], 'ramp': []}
average_demand_mainline = np.load('average_demand_mainline.npy')
average_demand_ramp = np.load('average_demand_ramp.npy')
all_date = np.array([])
path = 'D://Users//LLH//PycharmProjects//BH_rampcontrol//simulation_cfg//'
os.chdir(path)
with open(path + 'info_controlled_ramps.json', 'r') as f:
    info = json.load(f)
for i in range(1):
    m, r = random_flow(path, average_demand_mainline, average_demand_ramp, 0.2, 0.1)
    mainline_set_flow.extend(m)
    ramp_set_flow.extend(r)
    os.system(
        f"duarouter -n {path}A.net.xml -r {path}random_routes.xml --randomize-flows  -o {path}myrandomroutes.rou.xml")
    # 运行
    q, r = alinea_control(i, info)
    # 存储数据
    queue.extend(q[30:])
    redtime.extend(r[30:])
    # 获取输出文件中的检测器数据
    s, _, f = read_detectorout(detector_list, str(i) + 'detector_out.xml', warmup)
    for d in detector_list:
        speed[d].extend(s[d])
        flow[d].extend(f[d])

    mainline_demand_array = np.repeat(np.array(mainline_set_flow), 15 * 3).reshape(-1, 1)
    mainline_flow_array = np.vstack((np.array(flow['814 SB']), np.array(flow['813 SB']), np.array(flow['812 SB']),
                                     np.array(flow['811 SB']), np.array(flow['810 SB']))).T * 3600 / 20 / 4
    mainline_speed_array = np.vstack((np.array(speed['814 SB']), np.array(speed['813 SB']), np.array(speed['812 SB']),
                                      np.array(speed['811 SB']), np.array(speed['810 SB']))).T * 3.6
    ramp_demand_array = np.repeat(np.array(ramp_set_flow), 15 * 3).reshape(-1, 1)
    ramp_queue_array = np.array(queue).T.reshape(-1, 1)
    ramp_flow_array = (np.array(flow['ramp']).T * 3600 / 20 / 4).reshape(-1, 1)
    ramp_speed_array = (np.array(speed['ramp']).T * 3600 / 20 / 4).reshape(-1, 1)
    rl_state_array1 = ((np.array(flow['814 SB']) + np.array(flow['813 SB'])) * 3600 / 20 / 4 / 2 / 100).astype(
        int).reshape(-1, 1)
    rl_state_array2 = np.where(np.array(flow['812 SB']) != 0,
                               np.array(flow['812 SB']) * 3600 / 20 / 4 / (np.array(speed['812 SB']) * 3.6) / 2,
                               0).astype(int).reshape(-1, 1)
    rl_state_array3 = (ramp_queue_array / 10).astype(int).reshape(-1, 1)
    rl_state_array4 = (np.array(redtime) / 2).astype(int).reshape(-1, 1)
    rl_action_array = (np.array(redtime) / 2).astype(int).reshape(-1, 1)  # Need to be moved one step forward
    rl_action_array = np.vstack((0, rl_action_array[1:]))
    rl_queue_punish = np.where(ramp_queue_array > 130, 1 - (ramp_queue_array - 120) / 100, 1).reshape(-1, 1)
    rl_reward_array = np.array(flow['810 SB']).T.reshape(-1,
                                                         1) * 3600 / 20 / 4 * rl_queue_punish  # Need to be moved one step forward
    rl_reward_array = np.vstack((0, rl_reward_array[1:, :]))
    all_data = np.hstack((mainline_demand_array, mainline_flow_array, mainline_speed_array, ramp_demand_array,
                          ramp_queue_array, ramp_flow_array, ramp_speed_array, rl_state_array1, rl_state_array2,
                          rl_state_array3, rl_state_array4, rl_action_array, rl_reward_array))
    np.save('data' + str(i), all_data[1:, :])
