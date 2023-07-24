# This is not a sample Python script.
import os
import pathlib
import opendssdirect as dss
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def mon_file_name(mon_files_loc, mon_name):
    temp_1 = str(mon_files_loc)
    temp_2 = str(mon_name)
    temp_3 = "_1.csv"
    return temp_1 + temp_2 + temp_3


print("--------------- Initiating Data Retrieval - Reading files -----------------------")
# Basic information like metadata of feeders
script_path = os.path.dirname(os.path.abspath(__file__))
# dss_file = pathlib.Path(script_path).joinpath("../data_files/feeders/13Bus/IEEE13Nodeckt.dss")
dss_file = pathlib.Path(script_path).joinpath("../data_files/feeders/Baneshwor_SS_Feeders/Master.dss")

folder_name = "Baneshwor_V2_Legion"

monitoring_files_path = pathlib.Path(script_path).joinpath("../data_files/outputs/monitor_files/")

# Flags of the result
simulated_cases = 301
condition_monitoring = False  # condition monitoring
maintenance_model = 1  # maintenance model 0: weekend based maintenance, 1: night based maintenance

# Variables to calculate
load_energy = []
energy_not_served = []

for casenumber in range(0, simulated_cases):
    if casenumber == 0:
        casename = "01_Without_Fault"

    else:
        if condition_monitoring:
            casename = f"{casenumber}_CM_Model_{maintenance_model}_With_Fault"
        else:
            casename = f"{casenumber}_Base_With_Fault"

    dss.Text.Command("Clear")
    dss.Text.Command(f"compile [{dss_file}]")
    dss.Text.Command("set hour=0 sec=0")
    dss.Text.Command(f"set case = {casename}")

    dss.Basic.DataPath("../../outputs/monitor_files/")

    dss.Basic.AllowEditor(0)
    dss.Basic.AllowForms(0)
    lst_monitors = dss.Monitors.AllNames()

    # ---------------------Monitors for energy monitoring of load in the circuit------------------------
    df_load_consumption = pd.DataFrame(lst_monitors, columns=['Monitors'])
    df_load_consumption['P1_kWh'] = 0
    df_load_consumption['Q1_kVARh'] = 0
    df_load_consumption['P2_kWh'] = 0
    df_load_consumption['Q2_kVARh'] = 0
    df_load_consumption['P3_kWh'] = 0
    df_load_consumption['Q3_kVARh'] = 0

    casename_mon = casename + "_Mon_"
    mon_files_path = pathlib.Path(monitoring_files_path).joinpath(casename_mon)

    # some monitor files are giving error while reading from the disk
    file_error_flag = False

    for i in range(0, len(lst_monitors)):
        if file_error_flag:
            print(f"---------------------------skipped the set with {mon_file}---------------------------------")
            break

        mon_file = mon_file_name(mon_files_path, lst_monitors[i])
        try:
            df = pd.read_csv(mon_file, sep=',')
        except(Exception,):
            file_error_flag = True
            continue

        df['sec2hours'] = df.iloc[:, [1]] * (1 / 3600)
        df['hours'] = df[['hour', 'sec2hours']].sum(axis=1, skipna=True)
        df.drop('sec2hours', axis=1, inplace=True)

        df_load_consumption.iat[i, 1] = df['P1 (kW)'].sum(axis=0, skipna=True)
        df_load_consumption.iat[i, 2] = df['Q1 (kvar)'].sum(axis=0, skipna=True)
        df_load_consumption.iat[i, 3] = df['P2 (kW)'].sum(axis=0, skipna=True)
        df_load_consumption.iat[i, 4] = df['Q2 (kvar)'].sum(axis=0, skipna=True)

        if df.shape[1] > 7:  # For only three phase loads else generates error
            df_load_consumption.iat[i, 5] = df['P3 (kW)'].sum(axis=0, skipna=True)
            df_load_consumption.iat[i, 6] = df['Q3 (kvar)'].sum(axis=0, skipna=True)

    if file_error_flag:
        print(f"---------skipped the calculation for casenumber {casenumber}--------")
        continue

    # finding sum over index axis
    # By default the axis is set to 0
    df_load_consumption.to_csv("load_consumption.csv")
    df_load_cons_from_file = pd.read_csv("load_consumption.csv")

    # finding sum over index axis
    # By default the axis is set to 0
    df_load_cons_total = df_load_cons_from_file.sum(axis=0, skipna=True)

    # recording load energy and energy not served data
    load_consumption = df_load_cons_total.P1_kWh + df_load_cons_total.P2_kWh + df_load_cons_total.P3_kWh
    load_energy.append(load_consumption)
    if len(load_energy) > 1:
        ens_case = load_energy[0] - load_consumption
        energy_not_served.append(ens_case)

# Sneak peek of ENS data
df_ens = pd.DataFrame(energy_not_served, columns=['ENS, MWh'])
df_ens = df_ens / 1000
df_ens_d = df_ens.describe()
df_ens_d = df_ens_d.round(decimals=3)
print(df_ens_d)

# Calculation of coefficient of variation
beta = []
for i in range(df_ens.shape[0]):
    N = i + 1  # +1 as pandas start indexing from 0
    # Getting first 3 rows from df
    df_ens_i = df_ens.head(N)
    ens_series = df_ens_i['ENS, MWh'].squeeze()
    beta_i = ens_series.std() / (N * ens_series.mean())
    beta.append(beta_i)

# The following lines work on to save the results of load energy and energy not served in the files
# These files shall be used to plot the results for the thesis work
df_load_energy = pd.DataFrame(load_energy, columns=['Energy in kWh'])
df_energy_not_served = pd.DataFrame(energy_not_served, columns=['Energy not served in kWh'])
df_beta = pd.DataFrame(beta, columns=['Coefficient of Variation'])


# make a directory for saving files of this case, if it doesn't exist
load_energy_filepath = pathlib.Path(script_path).joinpath(
        f'outputs/{folder_name}')
try:
    os.mkdir(load_energy_filepath)
except(Exception,):
    pass

if condition_monitoring:
    df_load_energy.to_csv(pathlib.Path(load_energy_filepath).joinpath(f'CM{maintenance_model}_LE.csv'), index =False, header=['Energy_kWh'])

else:
    df_load_energy.to_csv(pathlib.Path(load_energy_filepath).joinpath(f'Base_LE.csv'), index =False, header=['Energy_kWh'])

print(f"----Files needed for report figures preparation saved in \n {load_energy_filepath}------")

if condition_monitoring:
    df_load_energy.to_csv(pathlib.Path(script_path).joinpath(
        f'outputs/load_energy_cm_model_{maintenance_model}_case.csv'),
        index=False, header=['Energy_kWh'])
    df_energy_not_served.to_csv(pathlib.Path(script_path).joinpath(
        f'outputs/ENS_cm_model_{maintenance_model}_case.csv'),
        index=False, header=["ENS_kWh"])
    df_beta.to_csv(pathlib.Path(script_path).joinpath(
        f'outputs/beta_cm_model_{maintenance_model}_case.csv'),
        index=False, header=["ENS_kWh"])
    df_ens_d.to_csv(pathlib.Path(script_path).joinpath(
        f'outputs/ENS_Statistics_CM_{maintenance_model}_case.csv'),
        index=False, header=["ENS_kWh"])
else:
    df_load_energy.to_csv(pathlib.Path(script_path).joinpath("outputs/load_energy_basecase.csv"),
                          index=False, header=['Energy_kWh'])
    df_energy_not_served.to_csv(pathlib.Path(script_path).joinpath("outputs/ENS_basecase.csv"),
                                index=False, header=["ENS_kWh"])
    df_beta.to_csv(pathlib.Path(script_path).joinpath("outputs/beta_basecase.csv"),
                   index=False, header=["ENS_kWh"])
    df_ens_d.to_csv(pathlib.Path(script_path).joinpath("outputs/ENS_Statistics_basecase.csv"),
                    index=False, header=["ENS_kWh"])




# Plotting the beta curve
plt.style.use('seaborn-talk')
plt.rcParams["font.family"] = "Times New Roman"
fig, ax = plt.subplots(figsize=(9, 6))
# Using Numpy to create an array X
hours = np.arange(1, df_beta.shape[0] + 1, 1)
ax.plot(hours, df_beta, label="beta", linewidth=0.5)

# Naming the x-axis, y-axis and the whole graph
ax.set_xlabel("Simulation Years")
ax.set_ylabel("Coefficient of variation")
ax.set_title("Convergence of coefficient of variation")
# ax.set_xlim(0, df_beta.shape[0])
ax.grid(color='0.95', linestyle='-', linewidth=1)

# Adding legend, which helps us recognize the curve according to it's color
ax.legend(loc='upper right')
plt.show()
