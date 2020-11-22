import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def read_json_file(path, file):
    if file[-5:] != '.json':
        file = file + '.json'
    with open(path + file, 'r') as f:
        data = json.load(f)
    return data


def draw_main_demand_figure(detector, data, step, date):
    data = np.array(data[detector][300: 600]).reshape(-1, step)  # Average per step minutes
    data = np.mean(data, axis=1)
    # data = data.reshape(1, -1)
    x = np.array(pd.date_range(date + ' 05:00:00', date + ' 10:00:00', freq=str(step) + 'min'))[1:]
    plt.figure(dpi=300)
    plt.plot(x, data)
    plt.title(date + 'Mainline Demand')
    plt.xlabel('Time(min)')
    plt.ylabel('veh/h')
    plt.savefig(date + '_main_demand(813 SB).png')
    plt.show()
    return data


def draw_ramp_demand_figure(data, date, step):
    data = np.sum(data, axis=0)
    data = data.reshape(-1, step * 3)  # Average per step minutes
    data = np.mean(data, axis=1)
    # data = data.reshape(1, -1)
    x = np.array(pd.date_range(date + ' 05:00:00', date + ' 10:00:00', freq=str(step) + 'min'))[1:]
    plt.figure(dpi=300)
    plt.plot(x, data)
    plt.xlabel('Time(min)')
    plt.ylabel('veh/h')
    plt.title(date + ' Ramp Demand')
    plt.savefig(date + '_ramp_demand.png')
    plt.show()
    return data


if __name__ == '__main__':
    file_path = r'G:\项目与论文\BH_RL\brisbane data\Analysis\\'  # Where flow data saved
    # 'j_Flow_20190906.json' is wrong, but trend is similar
    files = ['j_Flow_20190902.json', 'j_Flow_20190903.json', 'j_Flow_20190904.json', 'j_Flow_20190905.json']
    dates = ['2019-09-02', '2019-09-03', '2019-09-04', '2019-09-05', '2019-09-06']
    detector = '814 SB'
    step = 15
    flow_data = {}
    for i in range(len(files)):
        file_name = files[i]
        flow_data[file_name] = read_json_file(file_path, file_name)
        test = draw_main_demand_figure(detector, flow_data[file_name], step, dates[i])
    '''ramp_flow_data = read_json_file('./data/', 'rflow.json')
    anzac_flow = np.array([np.array(ramp_flow_data['Anzac_lane1']), np.array(ramp_flow_data['Anzac_lane2']),
                           np.array(ramp_flow_data['Anzac_lane3']), np.array(ramp_flow_data['Anzac_lane4'])]).reshape(4,
                                                                                                                      -1)
    anzac_flow_day = [0, 0, 0, 0, 0]  # 5 hours in 5 work days 5:00-10:00
    for day in range(5):
        anzac_flow_day[day] = np.array(anzac_flow[:, (day * 24 + 5) * 180: (day * 24 + 10) * 180], dtype=float)
        draw_ramp_demand_figure(anzac_flow_day[day], dates[day], 15)'''
    # Draw d big fig
    plt.figure(dpi=300)
    x = np.array(pd.date_range('05:00:00', '10:00:00', freq=str(step) + 'min'))[1:]
    sum_flow = np.zeros([20,])
    plt.title('Mainline Demand')
    plt.xlabel('Time(min)')
    plt.ylabel('veh/h')
    for i in range(len(files)):
        file_name = files[i]
        flow_data[file_name] = read_json_file(file_path, file_name)
        data = np.array(flow_data[file_name][detector][300: 600]).reshape(-1, 15)
        data = np.mean(data, axis=1)
        sum_flow += data
        # data = data.reshape(1, -1)
        plt.plot(x, data)
    plt.plot(x, sum_flow/4, linewidth=3, linestyle=':')
    plt.savefig('Mainline Demand.png')

    '''plt.figure(dpi=300)
    x = np.array(pd.date_range('05:00:00', '10:00:00', freq=str(step) + 'min'))[1:]
    sum_ramp_flow = np.zeros([20, ])
    plt.title('Ramp Demand')
    plt.xlabel('Time(min)')
    plt.ylabel('veh/h')
    for day in range(5):
        data = anzac_flow_day[day]
        data = np.sum(data, axis=0)
        data = data.reshape(-1, step * 3)  # Average per step minutes
        data = np.mean(data, axis=1)
        sum_ramp_flow += data
        # data = data.reshape(1, -1)
        plt.plot(x, data)
    average_ramp_flow = sum_ramp_flow / 5
    plt.plot(x, average_ramp_flow, linewidth=3, linestyle=':')
    plt.savefig('Ramp Demand.png')
    np.save('Ramp Demand', average_ramp_flow.flatten())'''
