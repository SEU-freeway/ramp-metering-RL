# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 19:47:23 2020

@author: Mr.Du
"""

import os
import sys

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
import numpy as np
from functools import reduce


def cal_rate_alinea(critic_occupancy, current_occupancy, merge_rate0, k):  # alinea计算流率
    r = merge_rate0 - k * (current_occupancy - critic_occupancy)
    return r


def cal_rate_pi_alinea(critic_occupancy, current_occupancy, last_step_occupancy, merge_rate0, kr, kp):  # alinea计算流率
    r = merge_rate0 - kr * (current_occupancy - critic_occupancy) - kp*(current_occupancy - last_step_occupancy)
    return r

def cal_rate_q(T, q, qmax, flow0):
    rq = -1 / T * 3600 * (qmax - q) + flow0
    return rq


def cal_rate_qmin(T, q, qmin, flow0):
    rqmin = -1 / T * 3600 * (qmin - q) + flow0
    return rqmin


def cal_redtime(rate, NumLanes):  # 将流率转为红灯时长
    greentime = 2
    redtime = 3600 * NumLanes / rate - greentime  # 绿灯时间定为2
    return round(redtime, 1)  # 红灯时间保留一位小数即可


def redtime_cal_r(redtime, NumLanes):  # 用最后计算的红灯时长校验流率
    greentime = 2
    r = 3600 / (greentime + redtime) * NumLanes
    return r


'''def cal_oc(critial_occupancy, occupancy0, occupancy, delta, flow, flow0):#将流率转为红灯时长
    ratio = (flow-flow0)/(occupancy-occupancy0)
    if ratio>=-0.5*(delta) and ratio<=delta: return critial_occupancy
    if ratio<-0.5*(delta): return max(10, critial_occupancy*0.99) #不小于10
    if ratio>delta: return min(critial_occupancy*1.01, 30)#不大于30'''


def alinea_control(flag, info):
    control_algorithm = info['control_algorithm']
    ramp_name = info['ramp_name']
    tls_id = info['tls_id']
    ramp_lnum = info['ramp_lnum']
    main_lnum = info['main_lnum']
    interval = info['interval']
    merge_rate0 = info['merge_rate0']
    alinea_occupancy_critic = info['alinea_occupancy_critic']
    alinea_k = info['alinea_k']
    if control_algorithm == 'pi-alinea':
        alinea_kp = info['alinea_kp']
    max_add = info['max_add']
    max_minus = info['max_minus']
    detector = info['detector']
    ramp_edge = info['ramp_edge']
    ramp_space = info['ramp_space']
    all_edge_id = info['all_edge_id']

    occupied_duration = {}
    car_num = []
    car_num_ramp = []
    o = {}
    if control_algorithm == 'pi-alinea':
        o0 = {}
    queue = {}
    step_queue = {}
    red_time = {}
    phrase = {}
    for i in range(len(ramp_name)):
        queue[ramp_name[i]] = [0]
        step_queue[ramp_name[i]] = 0
        phrase[ramp_name[i]] = []
        car_num_ramp.append([])
        red_time[ramp_name[i]] = [cal_redtime(merge_rate0[i], ramp_lnum[i])]
        for j in range(len(detector[i])):
            occupied_duration[detector[i][j]] = 0

    traci.start(['sumo', "-c", "BH_anzac.sumocfg", "--output-prefix", str(flag)])

    for step in range(0, 18600):  # 仿真时长
        step_car_num = np.sum([traci.edge.getLastStepVehicleNumber(x) for x in all_edge_id])
        car_num.append(step_car_num)
        for i in range(len(ramp_name)):
            car_num_ramp[i].append(
                traci.edge.getLastStepVehicleNumber(ramp_edge[i][0]) + traci.edge.getLastStepVehicleNumber(ramp_edge[i][1]))
        if step != 0 and step % interval == 0:  # 第一步是不调节的
            for i in range(len(ramp_name)):
                ramp = ramp_name[i]
                queue[ramp].append(step_queue[ramp])
                if control_algorithm == 'pi-alinea':
                    if i > interval:
                        o0[ramp] = o[ramp]
                    else:
                        o0[ramp] = alinea_occupancy_critic[i]
                o[ramp] = min(
                    np.mean(reduce(lambda x, y: x + y, [occupied_duration[d] for d in detector[i]])) / main_lnum[
                        i] / interval * 100, 100)
                if control_algorithm == 'alinea':
                    ra = cal_rate_alinea(alinea_occupancy_critic[i], o[ramp], merge_rate0[i],
                                     alinea_k[i])  # 每20s重新计算一次merge rate；此时步长为1
                elif control_algorithm == 'pi-alinea':
                    ra = cal_rate_pi_alinea(alinea_occupancy_critic[i], o[ramp], o0[ramp], merge_rate0[i],
                                         alinea_k[i], alinea_kp[i])
                else:
                    raise ValueError('Unidentified control algorithm!')
                r = ra
                print(o, ra)
                r = max(min(r, 900 * ramp_lnum[i]), 180 * ramp_lnum[i])  # 存在最大最小值
                redtime1 = max(min(red_time[ramp][-1] + max_add[i], cal_redtime(r, ramp_lnum[i])),
                               red_time[ramp][-1] - max_minus[i])  # 判断变化值是否过大
                if queue[ramp][-1] > ramp_space[i]:
                    redtime1 = 2
                red_time[ramp].append(redtime1)
                r = redtime_cal_r(redtime1, ramp_lnum[i])
                merge_rate0[i] = r  # 存贮调整率

            for d in occupied_duration.keys():
                occupied_duration[d] = 0

        traci.simulationStep()
        for d in occupied_duration.keys():
            v_info = traci.inductionloop.getVehicleData(d)
            for car in v_info:
                if car[3] != -1.0:
                    occupied_duration[d] += car[3] - car[2]

        for i in range(len(ramp_name)):
            ramp = ramp_name[i]
            step_queue[ramp] = traci.edge.getLastStepVehicleNumber(ramp_edge[i][0]) + traci.edge.getLastStepVehicleNumber(
                ramp_edge[i][1])
            phrase[ramp].append(traci.trafficlight.getPhase(tls_id[i]))  # 记录信号灯相位

        # 第一步的时候不能进行以下计算
        if step > 15:  # 第一个周期无调节
            for i in range(len(ramp_name)):
                ramp = ramp_name[i]
                if phrase[ramp][step] == 1 and phrase[ramp][step - 1] == 0:  # 没有黄灯
                    traci.trafficlight.setPhaseDuration(tls_id[i], red_time[ramp][-1] - 1)

    traci.close()
    return queue['A'], red_time['A']
if __name__ == '__main__':
    import os
    import json
    os.chdir(r'D:\Users\LLH\PycharmProjects\BH_rampcontrol\simulation_cfg')
    with open('info_controlled_ramps.json', 'r') as f:
        info = json.load(f)
    q, r = alinea_control(1, info)