data example:

traffic flow data: a list with the following 15 elements, 
0: mainstream demand (veh/h)
1: 5: flows of those five detectors on the mainstream(veh/h/lane)
6: 10: speeds of those five detectors on the mainstream(km/h)
11: on-ramp demand (veh/h)
12: ramp queue (veh)
13: flow(veh/h/lane) of the ramp detector 
14: speed(km/h) of the ramp detector

e.g., [4500, 1500, 1500, 1500, 1500, 1500, 100, 100, 90, 90, 90, 1500, 10, 750, 90]

RL state data:

An RL state contains 4 variables, which are the mainstream arriving flow(veh/h/lane), the density of the merging area(veh/km/lane), 
the ramp queue(veh), and the red duration of the last control cycle(s). All these variables need to be discretized. 

The mainstream arriving flow is calculated as the average flow of the most upstream two detectors. The discrete interval is set to 100(veh/h/lane);
The density of  merging area is calculated by the detected flow over the detected speed. The discrete interval is set to 2(veh/km/lane);
The ramp queue denotes the number of vehicles behind the stop bar of the ramp metering signal. The discrete interval is set to 10(veh);
The discrete interval of the red duration is set to 2(s).
e.g., [15, 8, 2, 10]

Action data:
An action contains one variable, which is the red duration of this control cycle. The discrete interval of the red duration is set to 2(s).

Reward data:
Throughput: the flow(veh/h/lane) of the most downstream detector. The discrete interval is set to 100(veh/h/lane). Also add punishment if the ramp queue is too large.   




