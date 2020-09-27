# -*- coding: utf-8 -*-
"""
Created on Wed May 13 09:05:44 2020

@author: Mr.Du
"""
import xml.etree.ElementTree
from functools import reduce
import numpy as np
import json
import pandas as pd

def read_detectorout(detector_list, filename, warmup): #warmup单位按秒
    tree = xml.etree.ElementTree.parse(filename)
    root = tree.getroot()
    s = {}
    o = {}
    f = {}
    for elem in root.iter(tag='interval'):
        if float(elem.get('begin')) >= warmup :
            detectorid = elem.get('id')
            if detectorid not in s.keys():
                s[detectorid] = [float(elem.get('speed'))*float(elem.get('nVehContrib'))]
                o[detectorid] = [float(elem.get('occupancy'))]
                f[detectorid] = [float(elem.get('nVehContrib'))]
            else:
                s[detectorid].append(float(elem.get('speed'))*float(elem.get('nVehContrib')))
                o[detectorid].append(float(elem.get('occupancy')))
                f[detectorid].append(float(elem.get('nVehContrib')))
    s_edge = {}
    o_edge = {}
    f_edge = {}
    
    for detector in detector_list:
        lanedetectors = [x for x in s.keys() if detector in x]
        s_lanes = [s[x] for x in lanedetectors]
        o_lanes = [o[x] for x in lanedetectors]
        f_lanes = [f[x] for x in lanedetectors]
        s_edge[detector] = reduce(lambda x, y: np.array(x) + np.array(y), s_lanes)
        o_edge[detector] = reduce(lambda x, y: np.array(x) + np.array(y), o_lanes)/len(lanedetectors)
        f_edge[detector] = reduce(lambda x, y: np.array(x) + np.array(y), f_lanes)
        s_edge[detector] = s_edge[detector]/f_edge[detector]
    return s_edge, o_edge, f_edge

def read_calibrator(ramp_list, filename, warmup):
    tree = xml.etree.ElementTree.parse(filename)
    root = tree.getroot()
    f = {}
    for elem in root.iter(tag='interval'):
        if float(elem.get('begin')) >= warmup :
            cid = elem.get('id')
            nVeh = float(elem.get('nVehContrib')) + float(elem.get('inserted')) - float(elem.get('removed')) -  float(elem.get('cleared'))  
            if cid not in f.keys():
                f[cid] = [nVeh]
            else:
                f[cid].append(nVeh)
    f_ramp = []
    for ramp in ramp_list:
        lanedetectors = [x for x in f.keys() if ramp in x]
        f_lanes = [f[x][:-1] for x in lanedetectors] # calibrator最后会多一个
        f_ramp = reduce(lambda x, y: np.array(x) + np.array(y), f_lanes)
 
    return f_ramp
    
def read_json(filename):
    with open(filename,'r',encoding='utf-8') as file:
        data=json.load(file) 
    return data

flow_ramp = []
queue = []
redtime = []
carnum = []
carnum_ramp = []
speed_detector = {'813 SB': [], '812 SB': []}
occupancy_detector = {'813 SB': [], '812 SB': []}
flow_detector = {'813 SB': [], '812 SB': []}

def main():
    detector_list = ['813 SB', '812 SB']
    ramp_list = ['A']
    warmup = 600
    flag_list = [1.2, 2.2, 3.2, 4.2, 5.2, 1.4, 2.4, 3.4, 4.4, 5.4, 1.6, 2.6, 3.6, 4.6, 5.6, 1.8, 2.8, 3.8, 4.8, 5.8]
    for flag in flag_list:
        filename = str(flag)+'out.xml'
        s, o, f = read_detectorout(detector_list, filename, warmup)
        for d in detector_list:
            speed_detector[d].extend(s[d])
            occupancy_detector[d].extend(o[d])
            flow_detector[d].extend(f[d])
        filename = str(flag)+'cal.xml'
        flow_ramp.extend(read_calibrator(ramp_list, filename, warmup))
    q = read_json('queue.json')
    r = read_json('redtime.json')
    c = read_json('carnum.json')
    cr = read_json('carnumr.json')
    for i in range(len(q)):
        queue.extend(q[i]['A'][30:]) #整理成一个长列表；去掉warmup
        redtime.extend(r[i]['A'][30:])
    #处理一下carnum；画图看了一下max与mean的区别不大
        for j in range(599, 18580, 20):
            carnum.append(np.mean(c[i][j:j+20]))
            carnum_ramp.append(np.mean(cr[i][j:j+20]))

def punish_queue(x, base): #能不能再细分一下
    p = 0
    if x <= base:
        return p
    else:
        return (x-base)*2
'''main()
reward = [-carnum[i] - punish_queue(carnum_ramp[i], 100) for i in range(len(carnum))] # 如果匝道排队长度大于
data_dict={"speed813": speed_detector['813 SB'],
           "speed812": speed_detector['812 SB'],
           "occupancy813": occupancy_detector['813 SB'],
           "occupancy812": occupancy_detector['812 SB'],
           "flow813": flow_detector['813 SB'],
           "flow812": flow_detector['812 SB'],
           "rampflow": flow_ramp,
           "queue_rate": [x/110 for x in queue],
           "redtime": redtime,
           "carnum": carnum,
           "ramp_carnum": carnum_ramp,
           'reward': reward
           }        
df = pd.DataFrame(data_dict)
df.fillna(method='pad', inplace=True) # 用前一个数据代替NaN：method='pad'
df.to_csv('Adata.csv')'''
    
            


