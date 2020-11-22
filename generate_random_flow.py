# -*- coding: utf-8 -*-
"""
Created on Thu May 14 16:42:35 2020

@author: Mr.Du
"""

import xml.etree.ElementTree
import numpy as np
import os


def random_flow(path, base_flow4mainline, base_flow4ramp, factor_ramp, factor_mainline):
    random_mainline = (np.random.random(base_flow4mainline.shape) - 0.5) / 0.5 * factor_mainline + 1
    random_ramp = (np.random.random(base_flow4ramp.shape) - 0.5) / 0.5 * factor_ramp + 1
    mainline_flow = base_flow4mainline * random_mainline
    ramp_flow = base_flow4ramp * random_ramp
    index_m = 0
    index_r = 0
    tree = xml.etree.ElementTree.parse(path + 'random_routes.xml')
    root = tree.getroot()
    for elem in root.iter(tag='routes'):
        for flow in elem.iter(tag='flow'):
            if 'm' in flow.get('id'):
                flow.attrib['vehsPerHour'] = str(int(mainline_flow[index_m]))
                index_m += 1
            else:
                if flow.get('departLane') == "0" or flow.get('departLane') == "6":
                    flow.attrib['vehsPerHour'] = str(int(ramp_flow[index_r//4] * 0.22))
                else:
                    flow.attrib['vehsPerHour'] = str(int(ramp_flow[index_r//4] * 0.28))
                index_r += 1
    tree.write(path + 'random_routes.xml')
    return mainline_flow, ramp_flow


if __name__ == '__main__':
    average_demand_mainline = np.load('average_demand_mainline.npy')
    average_demand_ramp = np.load('average_demand_ramp.npy')
    sim_path = 'D://Users//LLH//PycharmProjects//BH_rampcontrol//simulation_cfg//'
    m, r = random_flow(sim_path, average_demand_mainline, average_demand_ramp, 0.2, 0.1)
