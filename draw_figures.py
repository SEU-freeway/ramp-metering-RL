import matplotlib.pyplot as plt


def plot_speed_contour(data, parameters, config):

    freeway_num_cells = 0
    cell_lengths = []
    for link_idx in range(len(config["link_properties"])):
        if config["link_properties"][link_idx] == "freeway":
            freeway_num_cells += len(config["cell_length"][link_idx])
            for cell_idx in range(len(config["cell_length"][link_idx])):
                if config["cell_properties"][link_idx][cell_idx] not in ["origin", "destination"]:
                    if link_idx == 0 and cell_idx == 1:
                        cell_lengths.append(config["cell_length"][link_idx][cell_idx])
                    else:
                        cell_lengths.append(cell_lengths[-1] + config["cell_length"][link_idx][cell_idx])

    plt.rcParams['font.size'] = 14
    plt.contourf(data[1: freeway_num_cells - 1, :], cmap="jet")
    plt.colorbar()

    simulated_steps = parameters['simulation_period'] / parameters['duration_time_step']
    num_xticks = 6

    ori_xtick = [idx * simulated_steps / num_xticks for idx in range(num_xticks + 1)]
    new_xtick = [int(num * parameters['duration_time_step'] * 3600 / 60) for num in ori_xtick]

    num_yticks = len(cell_lengths) - 1
    ori_ytick = [idx for idx in range(1, num_yticks + 1)]
    new_ytick = cell_lengths[0: -1]

    plt.xticks(ori_xtick, new_xtick)
    plt.yticks(ori_ytick, new_ytick)
    plt.xlabel("Time [min]")

    plt.ylabel("Location [km]")
    plt.title('Speed [km/h] contour plot')
    plt.savefig("speed", dpi=1000)
    plt.close()


def plot_density_contour(data, parameters, config):

    freeway_num_cells = 0
    cell_lengths = []
    for link_idx in range(len(config["link_properties"])):
        if config["link_properties"][link_idx] == "freeway":
            freeway_num_cells += len(config["cell_length"][link_idx])
            for cell_idx in range(len(config["cell_length"][link_idx])):
                if config["cell_properties"][link_idx][cell_idx] not in ["origin", "destination"]:
                    if link_idx == 0 and cell_idx == 1:
                        cell_lengths.append(config["cell_length"][link_idx][cell_idx])
                    else:
                        cell_lengths.append(cell_lengths[-1] + config["cell_length"][link_idx][cell_idx])

    plt.rcParams['font.size'] = 14
    plt.contourf(data[1: freeway_num_cells - 1, :], cmap="jet")
    plt.colorbar()

    simulated_steps = parameters['simulation_period'] / parameters['duration_time_step']
    num_xticks = 6

    ori_xtick = [idx * simulated_steps / num_xticks for idx in range(num_xticks + 1)]
    new_xtick = [int(num * parameters['duration_time_step'] * 3600 / 60) for num in ori_xtick]

    num_yticks = len(cell_lengths) - 1
    ori_ytick = [idx for idx in range(1, num_yticks + 1)]
    new_ytick = cell_lengths[0: -1]

    plt.xticks(ori_xtick, new_xtick)
    plt.yticks(ori_ytick, new_ytick)
    plt.xlabel("Time [min]")

    plt.ylabel("Location [km]")
    plt.title('Density [veh/km/lane] contour plot')
    plt.savefig("Density", dpi=1000)
    plt.close()


def plot_flow_contour(data, parameters, config):

    freeway_num_cells = 0
    cell_lengths = []
    for link_idx in range(len(config["link_properties"])):
        if config["link_properties"][link_idx] == "freeway":
            freeway_num_cells += len(config["cell_length"][link_idx])
            for cell_idx in range(len(config["cell_length"][link_idx])):
                if config["cell_properties"][link_idx][cell_idx] not in ["origin", "destination"]:
                    if link_idx == 0 and cell_idx == 1:
                        cell_lengths.append(config["cell_length"][link_idx][cell_idx])
                    else:
                        cell_lengths.append(cell_lengths[-1] + config["cell_length"][link_idx][cell_idx])

    plt.rcParams['font.size'] = 14
    plt.contourf(data[1: freeway_num_cells - 1, :], cmap="jet")
    plt.colorbar()

    simulated_steps = parameters['simulation_period'] / parameters['duration_time_step']
    num_xticks = 6

    ori_xtick = [idx * simulated_steps / num_xticks for idx in range(num_xticks + 1)]
    new_xtick = [int(num * parameters['duration_time_step'] * 3600 / 60) for num in ori_xtick]

    num_yticks = len(cell_lengths) - 1
    ori_ytick = [idx for idx in range(1, num_yticks + 1)]
    new_ytick = cell_lengths[0: -1]

    plt.xticks(ori_xtick, new_xtick)
    plt.yticks(ori_ytick, new_ytick)
    plt.xlabel("Time [min]")

    plt.ylabel("Location [km]")
    plt.title('Flow [veh/h/lane] contour plot')
    plt.savefig("Flow", dpi=1000)
    plt.close()