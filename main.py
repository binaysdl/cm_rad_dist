# This is not a sample Python script.
import os
import pathlib
import opendssdirect as dss
import pandas as pd
import numpy as np
import random

from src import basecase
from src import load_info
from src import get_dictionary
from src import generate_times
from src import ckt_info

from datetime import datetime

print("--------------- Initiating simulation - Reading files -----------------------")
start_time = datetime.now().now()
print(f" Start of simulation {start_time}")

# Basic information like metadata of feeders
script_path = os.path.dirname(os.path.abspath(__file__))
# dss_file = pathlib.Path(script_path).joinpath("data_files/feeders/13Bus/IEEE13Nodeckt.dss")
# dss_file = pathlib.Path(script_path).joinpath("data_files/feeders/EuropeanLVTestCase/Master.dss")
dss_file = pathlib.Path(script_path).joinpath("data_files/feeders/Baneshwor_SS_Feeders/Master.dss")
# coordinate_file = pathlib.Path(script_path).joinpath("feeders/13Bus/IEEE13Node_BusXY.csv")
# coordinate_file = pathlib.Path(script_path).joinpath("feeders/EuropeanLVTestCase/Buscoords.csv")

print(dss.__version__)
dss.Text.Command(f'compile {dss_file}')

# basic flags for the simulation
condition_monitoring = False  # condition monitoring
maintenance_model = 0  # maintenance model 0: weekend based maintenance, 1: express based maintenance
simulation_case_begin = 1
simulated_cases = 3  # change this to number of simulations; add 1 more as it starts from 1

print("-----------------Obtaining load files-----------------------------")
df_loads_kW, df_loads_kVAR, loads_kW, loads_kVAR = load_info.get_load_details(script_path)

print("-----------------Calling basecase load flow-----------------------------")
print(f"Base case start {datetime.now().now() - start_time}")
# =====================================================================================================================
# =====================================================================================================================
# =====================================================================================================================
# =====================================================================================================================
# =====================================================================================================================
# basecase.get_basecase_results(dss_file, loads_kW, loads_kVAR, df_loads_kW, df_loads_kVAR)

print("-----------------Initiating Monte Carlo Procedure-----------------------------")

dict_all = get_dictionary.get_dictionary_file(script_path, condition_monitoring)
df_upstream_bkr = pd.read_csv(pathlib.Path(script_path).joinpath("data_files/system_info/upstream_ckt_bkr.csv"), low_memory=False)
dict_upstream_bkr = df_upstream_bkr.set_index(df_upstream_bkr.iloc[:, 0]).agg(list, axis=1).to_dict()

print("--------------- Initiating load flow with disconnections in the system -----------------------")

# working on system components
df_fault_able_elements = ckt_info.get_fault_able_elements(dss.Circuit.AllElementNames())
df_switch_elements = ckt_info.get_switch_elements(df_fault_able_elements, dict_all)
df_cm_elements = ckt_info.get_cm_elements(df_fault_able_elements, dict_all)

df_fault_able_elements[1] = ''

for i in range(df_fault_able_elements.shape[0]):
    df_fault_able_elements.iat[i, 1] = dict_all[3][df_fault_able_elements.iloc[i][0]]

breaker_array = np.array(df_fault_able_elements[1].to_list())

# Run simulation without fault for one year
dss.Basic.AllowForms(0)

for casenumber in range(simulation_case_begin, simulated_cases):
    simulation_start_time = datetime.now().now()
    if condition_monitoring:
        casename = f"{casenumber}_CM_Model_{maintenance_model}_With_Fault"
    else:
        casename = f"{casenumber}_Base_With_Fault"
    dss.Text.Command("Clear")
    dss.Text.Command(f"compile [{dss_file}]")
    dss.Text.Command("set hour=0 sec=0")
    dss.Text.Command(f"set case = {casename}")
    dss.Text.Command("Set Mode=Dutycycle Stepsize=3600s number=1")

    if i % 5  ==0:
        print(f"{casename} start at {simulation_start_time}; Total elapsed time {datetime.now().now() - start_time}")

    # Initialize variables
    # information for each fault
    failed_elements_list = []
    was_cm_detected = []
    would_not_have_failed = []
    would_not_have_failed_flag = []
    breaker_enable = []
    breaker_obstructed = []  # Not sure why I am logging this information
    fault_loc = []
    time_of_fault = []
    time_of_repair = []
    breaker_enable = np.array(breaker_enable)
    breaker_enable = breaker_enable.astype(int)

    # times and flags
    ttf = []
    ttf_u = []
    ttr = []
    ttd = []
    ttd_flag = []  # just to see if ttd is reached or not before ttf.

    for i in range(0, df_fault_able_elements.shape[0]):
        # time to fail
        ttf.append(generate_times.ind_ttf(df_fault_able_elements.iloc[i][0], dict_all))
        # time to undetected failure
        if df_fault_able_elements.iloc[i][0] in df_switch_elements[0].unique():
            ttf_u.append(generate_times.ind_ttf_u(df_fault_able_elements.iloc[i][0], dict_all, ttf[i]))
        else:
            ttf_u.append(20000.00)
        # dummy data for time to repair
        ttr.append(0.00)
        # initiate time to detect flag as 0 for all for consistency
        # if condition_monitoring:
        ttd_flag.append(0)
        would_not_have_failed_flag.append(0)
        ttd.append(50000.00)

        # time for detection, only in case of condition monitoring
        if condition_monitoring and df_fault_able_elements.iloc[i][0] in df_cm_elements[0].unique():
            if df_fault_able_elements.iloc[i][0] in df_switch_elements[0].unique():
                ttd.append(generate_times.ind_ttd(df_fault_able_elements.iloc[i][0], dict_all, ttf[i], ttf_u[i]))
            else:
                ttd.append(generate_times.ind_ttd(df_fault_able_elements.iloc[i][0], dict_all, ttf[i]))

    # convert ttf and ttr to numpy arrays for easier working
    ttf = np.array(ttf)
    ttf_u = np.array(ttf_u)
    ttr = np.array(ttr)
    if condition_monitoring:
        ttd = np.array(ttd)
        ttd_flag = np.array(ttd_flag)
    # print(ttd)

    # List to record the times of failure_repair_detection
    ttf_list = []
    ttf_u_list = []
    ttr_list = []
    ttd_list = []

    # Start the hour wise simulation for the casenumber specified
    for i in range(0, 8760):

        # hour_start_time = datetime.now().now()
        # a code to have incidental failures based on lightning data
        if dict_all[4][i] == 1:
            random_element = random.choice(ttf)
            element_loc = np.where(ttf == random_element)[0][0]
            fault_chance = random.randint(0, 1)
            ttf[element_loc] = ttf[element_loc] * fault_chance

        # here goes the loop to check if each ttf is approaching zero quickly or not
        for j in range(0, len(ttf)):
            # check for all time to detect less than 1 and update ttf if necessary
            if condition_monitoring:
                if ttd[j] <= 1:
                    ttf_org = ttf[j]
                    # update ttf only if ttf is much different from the ttd
                    # this part of code had time to detect less than 1 missing earlier
                    if ttf[j] > 1 >= ttd[j]:
                        would_not_fail, ttd_flag[j], ttf[j] = generate_times.ttf_cm(maintenance_model,
                                                                                    df_fault_able_elements.iloc[j][0],
                                                                                    dict_all, ttf[j], i, df_loads_kW)
                        # ttd_flag[j] = 1
                        # this is used to identify whether a component has gone through CM detection or direct failure
                        ttd[j] = 50000  # big number, shall be updated when the component fails

                        # update the would_not_have_failed_flag
                        would_not_have_failed_flag[j] = would_not_fail

            # check for all time to failure less than 1
            if ttf[j] < 1:
                # get the failed element and
                failed_element = df_fault_able_elements[0][j]
                dss.Circuit.SetActiveElement(failed_element)

                # Obtain the time to repair, updated time to failure and time to detect of the failed element
                if condition_monitoring:
                    ttr[j] = generate_times.ind_ttr(failed_element, dict_all, i, ttd_flag[j])
                else:
                    ttr[j] = generate_times.ind_ttr(failed_element, dict_all, i)

                ttf[j] = generate_times.ind_ttf(failed_element, dict_all)
                ttf[j] = ttf[j] + ttr[j]
                ttf_u[j] = ttf_u[j] + ttr[j]

                # Record if the component was detected by CM
                was_cm_detected.append(ttd_flag[j])
                would_not_have_failed.append(would_not_have_failed_flag[j])

                # update time to detect
                if condition_monitoring:
                    ttd[j] = generate_times.ind_ttd(failed_element, dict_all, ttf[j])
                    ttd_flag[j] = 0

                # Update the lists for recording purpose for analysis
                breaker_obstructed.append(dict_all[3][failed_element])
                breaker_enable = np.append(breaker_enable, 0)
                fault_loc.append(j)
                failed_elements_list.append(failed_element)
                time_of_fault.append(i)
                time_of_repair.append(i)

                # identify the breaker to be opened is already faulty or not
                breaker_to_open = dict_all[3][failed_element]
                loc_in_element = int(
                    df_fault_able_elements[df_fault_able_elements[0] == breaker_to_open].index.values)
                if ttf_u[loc_in_element] < 1:
                    # get the failed element and
                    failed_element = breaker_to_open
                    dss.Circuit.SetActiveElement(failed_element)

                    # Obtain the time to repair, updated time to failure and time to detect of the failed element
                    if condition_monitoring:
                        ttr[j] = generate_times.ind_ttr(failed_element, dict_all, i, ttd_flag[j])
                    else:
                        ttr[j] = generate_times.ind_ttr(failed_element, dict_all, i)

                    ttf[j] = generate_times.ind_ttf(failed_element, dict_all)
                    ttf[j] = ttf[j] + ttr[j]
                    ttf_u[j] = generate_times.ind_ttf_u(failed_element, dict_all, ttf[j])
                    ttf_u[j] = ttf_u[j] + ttr[j]

                    # Record if the component was detected by CM
                    was_cm_detected.append(ttd_flag[j])
                    would_not_have_failed.append(would_not_have_failed_flag[j])

                    if condition_monitoring:
                        ttd[j] = generate_times.ind_ttd(failed_element, dict_all, ttf[j])
                        ttd_flag[j] = 0

                    # Update the lists for recording purpose for analysis
                    breaker_obstructed.append(dict_all[3][failed_element])
                    breaker_enable = np.append(breaker_enable, 0)
                    fault_loc.append(j)
                    failed_elements_list.append(failed_element)
                    time_of_fault.append(i)
                    time_of_repair.append(i)

        # print(f"Looping for ttf for hour {i} took {datetime.now().now() - hour_start_time} seconds")
        # find the first element to start the loop of observation
        # this is done to reduce the simulation time
        # first check if there is no content then 0
        # second check if there is no zero then complete length
        # third check if there is zero, go for first 0

        disabled_items = np.array([])

        if breaker_enable.size == 0:
            pass
            # non_enabled = [0, 0]
        elif np.all(breaker_enable):
            pass
            # non_enabled = [len(breaker_enable), len(breaker_enable)]
        else:
            # first_non_enabled = breaker_enable.tolist().index(0)
            non_enabled = np.where(breaker_enable == 0)[0]

            # print(f"Breaker enable lower value assign for hour {i}
            # took {datetime.now().now() - hour_start_time} seconds")

            for j in non_enabled:
                # set up active breaker from the list of failed elements, if fault has occurred earlier.
                active_breaker = dict_all[3][failed_elements_list[j]]
                dss.Circuit.SetActiveElement(active_breaker)
                # if the time to repair is less than 1 repair the element
                if ttr[fault_loc[j]] < 1:
                    if breaker_enable[j] == 0:
                        time_of_repair[j] = i
                    breaker_enable[j] = 1

                # update the status, either 0 or 1 depending upon the system
                dss.CktElement.Enabled(breaker_enable[j])

                downstream_items = np.where(breaker_array == breaker_obstructed[j])[0]
                disabled_items = np.append(disabled_items, downstream_items)

        # disabled_items = disabled_items.tolist()
        disabled_items = disabled_items.astype(int)
        ttf = ttf - 1
        ttf_u = ttf_u - 1

        ttf[disabled_items] += 1
        ttf_u[disabled_items] += 1
        if condition_monitoring:
            ttd = ttd - 1
            ttd[disabled_items] += 1

        # Now for time to repair
        ttr = ttr - 1
        # Update the time to repair of the components of the distribution system if less than 0 to 0
        low_values_flags = ttr < 0  # Where values are lower than 0
        ttr[low_values_flags] = 0  # All low values set to 0

        # Keep the variations in time to fail and else to see if your code is working as expected
        # List to record the times of failure_repair_detection
        ttf_list.append(list(ttf))
        ttf_u_list.append(list(ttf_u))
        ttd_list.append(list(ttd))
        ttr_list.append(list(ttr))

        # load is update after here and then simulated
        for j in range(0, df_loads_kW.shape[1]):
            dss.Text.Command(f"{loads_kW[j]}.kW={df_loads_kW.iloc[i][j]}")
            dss.Text.Command(f"{loads_kVAR[j]}.kVAR={df_loads_kVAR.iloc[i][j]}")
        dss.Solution.Solve()

        # if i%730 == 0:
            # print(f"{casename}'s hour {i} took {datetime.now().now() - hour_start_time}")
            # print(f"{casename} so far took {datetime.now().now() - simulation_start_time}")

        # print(f"Hour {i} took {datetime.now().now() - hour_start_time} seconds")

        # ------------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------------
        # saving of file in each iteration is commented out to speed up the process. - do not delete
        # ------------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------------
        # recording of loop info if required, not sure after today's presentation
        if condition_monitoring:
            save_info_filename = "CM_" + casename + "_failure_data.csv"
        else:
            save_info_filename = "Base_" + casename + "_failure_data.csv"
        dict_loop_info = {'Failed Element': failed_elements_list, 'Time of Fault': time_of_fault,
                          'Failure Detected by CM': was_cm_detected,
                          'Time of Repair': time_of_repair,
                          'Breaker selected': breaker_obstructed,
                          'Breaker Status': breaker_enable,
                          'Would not have failed': would_not_have_failed}

        df_loop_info = pd.DataFrame(dict_loop_info)
        path = pathlib.Path(script_path).joinpath(f"data_files/outputs/loop_wise_output/{save_info_filename}")
        df_loop_info.to_csv(path, index=False, header=['Failed Element', 'Time of Fault', 'Failure Detected by CM',
                                                       'Time of Repair', 'Breaker selected', 'Breaker Status',
                                                       'Would not have failed'])
    #
    #     # recording of loop info if required, not sure after today's presentation
    #     if condition_monitoring:
    #         record_path = pathlib.Path(script_path).joinpath("data_files/outputs/time_dump/CM_")
    #         ttf_filename = str(record_path) + casename + "-" + "ttf.csv"
    #         ttf_u_filename = str(record_path) + casename + "-" + "ttf_u.csv"
    #         ttd_filename = str(record_path) + casename + "-" + "ttd.csv"
    #         ttr_filename = str(record_path) + casename + "-" + "ttr.csv"
    #         del record_path
    #     else:
    #         record_path = pathlib.Path(script_path).joinpath("data_files/outputs/time_dump/Base_")
    #         ttf_filename = str(record_path) + casename + "-" + "ttf.csv"
    #         ttf_u_filename = str(record_path) + casename + "-" + "ttf_u.csv"
    #         ttr_filename = str(record_path) + casename + "-" + "ttr.csv"
    #         del record_path
    #
    # np.savetxt(ttf_filename, ttf_list, delimiter=", ", fmt='% s')
    # np.savetxt(ttf_u_filename, ttf_u_list, delimiter=", ", fmt='% s')
    # np.savetxt(ttr_filename, ttr_list, delimiter=", ", fmt='% s')
    # if condition_monitoring:
    #     np.savetxt(ttd_filename, ttd_list, delimiter=", ", fmt='% s')

    # monitor data is exported in this part, once in each loop
    dss.Basic.DataPath("../../outputs/monitor_files/")
    dss.Basic.AllowEditor(0)
    # first monitor is selected followed by next monitors
    dss.Monitors.First()
    for i in range(dss.Monitors.Count()):
        dss.Monitors.Show()
        dss.Monitors.Next()
    dss.Solution.Cleanup()

    print(f"{casename} had {len(failed_elements_list)} failures and {was_cm_detected.count(1)} was detected by cm")
    print(f"{casename} took {datetime.now().now() - simulation_start_time}")

print(f"End of Simulation {datetime.now().now() - start_time}")
