# -*- coding: utf-8 -*-
"""
Created on Fri Feb 21 10:39:34 2020

@author: Mr.Du
"""

# -*- coding: utf-8 -*-
""" QuickStart """
import os
import sys
 
if 'SUMO_HOME' in os.environ:
     tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
     sys.path.append(tools)
else:
     sys.exit("please declare environment variable 'SUMO_HOME'")
     
import traci 
from sumolib import checkBinary  # noqa
import optparse
import json

def cal_redtime(rate, NumLanes):
    redtime = 3600*NumLanes/rate - 2 #绿灯时间定为2
    return round(redtime,1) #红灯时间保留一位小数即可

import random
import numpy as np
import geatpy as ea
import xml.etree.ElementTree
from multiprocessing import Pool as ProcessPool
from multiprocessing.dummy import Pool as ThreadPool
import multiprocessing as mp
import threading



class DetectorData(object):

    def __init__(self, name, NumberOfLanes):
        self.name = name
        self.n = NumberOfLanes
        self.speed = []
        self.occupancy = []
        self.flow =[]

    def readdata(self, pid, warmup, duration, interval, day = 1):#默认是5天的数据,跑一次
        starttime = warmup
        endtime = starttime+duration
        n = int(duration/interval)
        self.speed = np.zeros([day,n])
        self.occupancy = np.zeros([day,n])
        self.flow = np.zeros([day,n])
        tree = xml.etree.ElementTree.parse(str(pid)+"out.xml")
        root = tree.getroot()
        for i in range(day):
            s = []
            o = []
            f = []
            for elem in root.iter(tag='interval'):
                if float(elem.get('begin')) >= starttime :
                    if float(elem.get('end')) <= endtime :
                        if self.name == elem.get('id'):
                            s.append(float(elem.get('speed'))*float(elem.get('nVehContrib')))
                            o.append(float(elem.get('occupancy')))
                            f.append(float(elem.get('nVehContrib')))
            self.speed[i] = s
            self.occupancy[i] = o
            self.flow[i] = f
            starttime = endtime+warmup
            endtime = starttime+duration
        '''self.speed = np.mean(self.speed, axis=0)
        self.occupancy = np.mean(self.occupancy, axis=0)
        self.flow = np.mean(self.flow, axis=0)#只跑一次仿真不需要'''
    def edge(self):
        self.occupancy = self.occupancy/self.n

def aggragate(data, starttime = 0, endtime = 1440, interval = 15 ):
    result=[]
    for i in range(starttime, endtime, interval):#计算结果
        result.append(np.sum(data[i:i+interval]))
    return result

def average(data, starttime = 0, endtime = 1440, interval = 15 ):
    result=[]
    for i in range(starttime, endtime, interval):#计算结果
        result.append(np.mean(data[i:i+interval]))
    return result

def init(l):  
	global lock
	lock = l

'''tvolume = {}
with open('C:/Users/Mr.Du/Desktop/brisbane data/Analysis/j_Volume_20190902.json','r') as load_f:
    tvolume = json.load(load_f)
#speed
tspeed ={}
with open('C:/Users/Mr.Du/Desktop/brisbane data/Analysis/j_IDsimplifiedSpeed_20190902.json','r') as load_f:
    tspeed = json.load(load_f)
#occupancy
tocc ={}
with open('C:/Users/Mr.Du/Desktop/brisbane data/Analysis/j_Occupancy_20190902.json','r') as load_f:
    tocc = json.load(load_f)
fielddata =[]
detector = {'816 SB': 3, '815 SB': 3, '814 SB': 3, '813 SB': 3, '812 SB': 4}
for d in detector.keys():
    fielddata.append(DetectorData(d, detector[d]))
for d in fielddata:
    d.speed = np.array(average(tspeed[d.name],  390, 450, 5 ))
    d.occupancy = np.array(average(tocc[d.name], 390, 450, 5 ))
    d.flow = np.array(aggragate(tvolume[d.name], 390, 450, 5 ))
    if d.name == '813 SB': d.flow = d.flow*1.5
fielddata = multiprocessing.Manager().list(fielddata)'''
        
def lane2edge(detector, detectorData):
    for d in detectorData:
        if detector.name in d.name:
            if np.array(detector.speed).shape[0] == 0:
                detector.speed = d.speed
                detector.occupancy = d.occupancy
                detector.flow = d.flow
            else:
                speed = detector.speed
                detector.speed = speed+d.speed
                occupancy = detector.occupancy
                detector.occupancy = occupancy+d.occupancy
                flow = detector.flow
                detector.flow = flow+d.flow
    #detector.speed = detector.speed/detector.flow #没有考虑5min没车的情况
    speed = (detector.speed/detector.flow)
    np.nan_to_num(speed)
    detector.speed = speed
    return detector

def changevalue(parameterdict):
    # Open original file
    tree = xml.etree.ElementTree.parse('vtype.xml')
    for parameter in parameterdict.keys():
        value = parameterdict[parameter]
        for element in tree.findall('vType'):
            element.attrib[parameter] = str(value)
    tree.write('vtype.xml')
    return

def Objfunction(simulationdata):
    devspeed = 0
    devflow = 0
    num = 0
    with open('./fielddata/Weighted_Speed0902.json','r') as load_f:
        tspeed = json.load(load_f)
    with open('./fielddata/Flow0902.json','r') as load_f:
        tflow = json.load(load_f)
    for d in simulationdata:
        d.speed = d.speed.flatten()

        devspeed += np.sum((d.speed*3.6 - tspeed[d.name])**2)

        num += len(d.speed)
        devflow += np.sum((d.flow - np.array(tflow[d.name])/60)**2)
    #print(num, devspeed, devocc)
#    return devspeed, devocc, devflow
    return (devspeed/num)**0.5, (devflow/num)**0.5

def subaimFunc(args):
    warmup = 600
    duration = 7200
    runtime = 1
    interval =60
    detector = {'813 SB': 3, '812 SB': 4, '811 SB': 3, '810 SB': 3}
    d1=[]
    d2=[]
    for key in detector.keys():
        d1.append(DetectorData(key, detector[key]))
        for j in range(detector[key]):
            d2.append(DetectorData(key+'_'+str(j+1),1))   
    #信号灯ID
    tlsID_A = '30885212'
    #车道数
    Num_A = 4

    redtime_A = 10

    j = 0 #处于第几个20秒
    p_A = []

    pid = mp.current_process().name
    with open('./fielddata/megerate8_10.json','r') as load_f:
        megerate = json.load(load_f) #假设是所需的，完整的数据  
    #lock.acquire()
    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    
    para = {'sigma': args[0], 'tau': args[1],
            'accel': args[2],'speedDev': args[3],
            'speedFactor': args[4], 'minGap': args[5], 'length':args[6]}
    pid = mp.current_process().name
    lock.acquire()
    changevalue(para)
    traci.start(['sumo', "-c", "BH4calib.sumocfg", "--output-prefix", str(pid)])
    threading.Timer(3, lock.release).start() # release in a second
    for step in range(0,7800):
        if step%20 == 0:
            r_A = megerate['Anzac'][j]

            j = j+1
            redtime_A = min(max(cal_redtime(r_A, Num_A), redtime_A-10),redtime_A+5)

        traci.simulationStep()
        p_A.append(traci.trafficlight.getPhase(tlsID_A))

        #第一步的时候不能进行以下计算
        if step != 0:
            if p_A[step] == 1 and p_A[step-1] == 0: #进入红灯,但是只能是刚进入
                traci.trafficlight.setPhaseDuration(tlsID_A, redtime_A)#每个周期都设置一下红灯时长
    traci.close()
    for d in d2:
        d.readdata(pid, warmup, duration, interval, 1)
    for de in d1:
        de = lane2edge(de, d2)
        de.edge()
    r = Objfunction(d1)
    """================改=============="""
    f=open("relength.txt","a")
    f.writelines(str(args))
    f.writelines(str(r)+"\n")
    f.close()
    return r

# 自定义问题类
class MyProblem(ea.Problem): # 继承Problem父类
    def __init__(self, M, PoolType):
        name = 'GA_Calibration' # 初始化name（函数名称，可以随意设置）
        maxormins = [1] * M # 初始化maxormins（目标最小最大化标记列表，1：最小化该目标；-1：最大化该目标）暂定flow，occupancy，speed三个
        Dim = 7 # 初始化Dim（决策变量维数） 
        varTypes = np.array([0, 0, 0, 0, 0, 0, 0]) # 初始化varTypes（决策变量的类型，0：实数；1：整数）
        '''lb = [0.6, 0, 1, 1, 0.3, 0, 0, 2] # 决策变量下界 probability0.6-1 speedDev0-1 speedFactor1-1.5 tau1-3 CC10.3-1.3 CC20-6 CC40-2 CC82-3.5 
        ub = [1, 1, 1.5, 3, 1.3, 6, 2, 3.5] # 决策变量上界
        lbin = [0, 0, 1, 1, 1, 1, 1, 1] # 决策变量下边界
        ubin = [0, 0, 1, 1, 1, 1, 1, 1] # 决策变量上边界'''
        #不再关心换道模型
        #2个tau，2个speedDev， 2个speedFactor， 2个minGap， sigma, 3个p
        lb = [0, 1, 1, 0, 1, 1, 6] 
        ub = [1, 4, 3, 0.5, 1.5, 3, 10] # 决策变量上界
        lbin = [1, 1, 1, 1, 1, 1, 1] # 决策变量下边界
        ubin = [1, 1, 1, 1, 1, 1, 1] # 
        # 调用父类构造方法完成实例化
        ea.Problem.__init__(self, name, M, maxormins, Dim, varTypes, lb, ub, lbin, ubin)
        self.PoolType = PoolType
        if self.PoolType == 'Thread':
            self.pool = ThreadPool(2) # 设置池的大小
        elif self.PoolType == 'Process':
            num_cores = int(mp.cpu_count()) # 获得计算机的核心数
            self.pool = ProcessPool(3, initializer=init, initargs=(lock,)) # 设置池的大小
    
    def aimFunc(self, pop):
        Vars = pop.Phen # 得到决策变量矩阵
        lVars = list(Vars)
        if self.PoolType == 'Thread':
            pop.ObjV = np.array(list(self.pool.map(subaimFunc, lVars)))
        elif self.PoolType == 'Process':
            result = self.pool.map_async(subaimFunc, lVars)
            result.wait()
            pop.ObjV = np.array(result.get())
        '''result = list (map(subaimFunc, lVars))
        print(result)
        pop.ObjV = np.array(result).reshape(-1,1)'''
        
    def calReferObjV(self): # 计算全局最优解
        uniformPoint, ans = ea.crtup(self.M, 10000) # 生成10000个在各目标的单位维度上均匀分布的参考点
        globalBestObjV = uniformPoint / 2
        return globalBestObjV

if __name__ == '__main__':
    
    # 编写执行代码
    """===============================实例化问题对象=============================="""
    lock = mp.Lock()
    M = 2  
    PoolType = 'Process'                   # 设置目标维数
    problem = MyProblem(M, PoolType)    # 生成问题对象
    """==================================种群设置================================="""
    Encoding = 'RI'           # 编码方式
    NIND = 32                 # 种群规模
    Field = ea.crtfld(Encoding, problem.varTypes, problem.ranges, problem.borders) # 创建区域描述器
    population = ea.Population(Encoding, Field, NIND) # 实例化种群对象（此时种群还没被初始化，仅仅是完成种群对象的实例化）
    """================================算法参数设置==============================="""
    myAlgorithm = ea.moea_NSGA3_templet(problem, population) # 实例化一个算法模板对象
    myAlgorithm.MAXGEN = 50  # 最大进化代数
    myAlgorithm.drawing = 2   # 设置绘图方式（0：不绘图；1：绘制结果图；2：绘制过程动画）
    """==========================调用算法模板进行种群进化=========================
    调用run执行算法模板，得到帕累托最优解集NDSet。NDSet是一个种群类Population的对象。
    NDSet.ObjV为最优解个体的目标函数值；NDSet.Phen为对应的决策变量值。
    详见Population.py中关于种群类的定义。
    """
    NDSet = myAlgorithm.run() # 执行算法模板，得到非支配种群
    NDSet.save()              # 把结果保存到文件中
    problem.pool.close() # 及时关闭问题类中的池，否则在采用多进程运算后内存得不到释放
    # 输出
    print('用时：%f 秒'%(myAlgorithm.passTime))
    print('评价次数：%d 次'%(myAlgorithm.evalsNum))
    print('非支配个体数：%d 个'%(NDSet.sizes))
    print('单位时间找到帕累托前沿点个数：%d 个'%(int(NDSet.sizes // myAlgorithm.passTime)))
    # 计算指标
    PF = problem.getReferObjV() # 获取真实前沿，详见Problem.py中关于Problem类的定义
    if PF is not None and NDSet.sizes != 0:
        GD = ea.indicator.GD(NDSet.ObjV, PF)       # 计算GD指标
        IGD = ea.indicator.IGD(NDSet.ObjV, PF)     # 计算IGD指标
        HV = ea.indicator.HV(NDSet.ObjV, PF)       # 计算HV指标
        Spacing = ea.indicator.Spacing(NDSet.ObjV) # 计算Spacing指标
        print('GD',GD)
        print('IGD',IGD)
        print('HV', HV)
        print('Spacing', Spacing)
        """============================进化过程指标追踪分析==========================="""
    if PF is not None:
        metricName = [['IGD'], ['HV']]
        [NDSet_trace, Metrics] = ea.indicator.moea_tracking(myAlgorithm.pop_trace, PF, metricName, problem.maxormins)
        # 绘制指标追踪分析图
        ea.trcplot(Metrics, labels = metricName, titles = metricName)

