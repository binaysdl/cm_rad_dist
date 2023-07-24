import random

import numpy as np
import pandas as pd


# function to assign a failure time to individual component
def ind_ttf(component_name, dict_all):
    # return 0.1
    # try to see if the component is line
    # if line the failure rate is obtained dividing by the line length, which is in km
    if component_name.split('.', 1)[0] == 'Line':
        if dict_all[12][component_name] != 1:
            unit_divider = dict_all[7][component_name]
        else:
            unit_divider = 1
    else:
        unit_divider = 1

    # try to see if the component has a failure rate specified to the particular component
    try:
        f_lambda = dict_all[0][component_name] / unit_divider
        # obtain the failure time from the failure rate assigned above multiplied by a normal distribution
        ttf = -(1 / f_lambda) * 8760 * np.log(random.uniform(0, 1))
        return ttf

    # if the specific component is not available, take a generic fault rate of the component
    except (Exception,):
        f_lambda = dict_all[0][component_name.split('.', 1)[0]] / unit_divider
        # obtain the failure time from the failure rate assigned above multiplied by a normal distribution
        ttf = -(1 / f_lambda) * 8760 * np.log(random.uniform(0, 1))
        return ttf


# function to assign failure and undetected time for a Switch component
def ind_ttf_u(component_name, dict_all, ttf):
    ttf * 1
    # try to see if the component has a failure rate specified to the particular component
    try:
        f_lambda = dict_all[16][component_name]
        # obtain the failure time from the failure rate assigned above multiplied by a normal distribution
        ttf_u = -(1 / f_lambda) * 8760 * np.log(random.uniform(0, 1))
        # print(f"Undetected failure time is {ttf_u} and Detectable failure is {ttf}")
        return ttf_u

    # if the specific component is not available, take a generic fault rate of the component
    except (Exception,):
        f_lambda = dict_all[16][component_name.split('.', 1)[0]]
        # obtain the failure time from the failure rate assigned above multiplied by a normal distribution
        ttf_u = -(1 / f_lambda) * 8760 * np.log(random.uniform(0, 1))
        # print(f"Undetected failure time is {ttf_u} and Detectable failure is {ttf}")
        return ttf_u


# function to assign time to detect for a component
def ind_ttd(component_name, dict_all, ttf, ttf_u=-1000):
    # try to see if the component has a failure rate specified to the particular component
    try:
        cm_rate = dict_all[2][component_name]
    except (Exception,):
        try:
            cm_rate = dict_all[2][component_name.split('.', 1)[0]]
        except (Exception,):
            cm_rate = 0

    try:
        cm_rate_sd = dict_all[14][component_name]
    except (Exception,):
        try:
            cm_rate_sd = dict_all[14][component_name.split('.', 1)[0]]
        except (Exception,):
            cm_rate_sd = 0

    try:
        cm_prob = dict_all[15][component_name]
    except (Exception,):
        try:
            cm_prob = dict_all[15][component_name.split('.', 1)[0]]
        except(Exception,):
            cm_prob = 0

    # obtain the detection time for a switch element, i.e., see if inoperable state can be occasionally detected or not
    if ttf_u == -1000:
        # just take the normal time of failure, nothing to do here
        detected_ttf = ttf
    else:
        # select one of the two times for a switch element
        # as the distribution is unknown, triangular distribution is considered
        fault_type_detection = random.triangular(0, 1)
        if fault_type_detection <= 0.9:
            # detected_ttf = min(ttf, ttf_u)
            detected_ttf = ttf
        else:
            list_of_failure_times = [ttf, ttf_u]
            detected_ttf = random.choice(list_of_failure_times)
            # print(f"Out of ttf: {ttf} and ttf_u {ttf_u}, {detected_ttf} is selected")

    # following code snipped shall work on obtaining probability of detection by condition monitoring
    prob_of_det = random.triangular(0, 1)
    if prob_of_det <= cm_prob:
        ttd = detected_ttf - np.random.normal(cm_rate, cm_rate_sd, 1)
        ttd = ttd.tolist()
        ttd = float(ttd[0])
        if ttd < 0:
            ttd = 1.0
    else:
        ttd = 50000  # just a high value to avoid detection

    return ttd


# function to assign time to repair for a component
def ind_ttr(component_name, dict_all, hour, ttd_flag=0):
    # try to see if the component has a repair rate specified to the particular component

    try:
        travel_distance = dict_all[6][component_name]
    except (Exception,):
        travel_distance = dict_all[6]['Speed (Unit/hour)'] * 1

    if ttd_flag == 1:
        travel_time = 0
        prep_time = 0
        op_delay = 0
    else:
        travel_time = travel_distance / dict_all[6]['Speed (Unit/hour)']
        op_delay = np.random.normal(dict_all[8][hour], 0.5, 1)
        prep_time = 1.5

        # calculate the preparation time based on the daytime as maintenance is carried out during daytime only
        dict_daytime = pd.DataFrame.from_dict(dict_all[11], orient='index')
        daytime_list = dict_daytime[0].to_list()
        for i in range(hour, len(daytime_list)):
            if daytime_list[i] == 1:
                prep_time = np.random.normal(i - hour, 2, 1)
                break

    try:
        r_mu = dict_all[1][component_name]
        try:
            r_sd = dict_all[17][component_name]
        except (Exception,):
            r_sd = dict_all[17][component_name.split('.', 1)[0]]
        # obtain the repair time from the repair rate assigned above multiplied by a normal distribution
        ttr = np.random.normal(1 / r_mu, r_sd, 1) + travel_time + prep_time + op_delay
        # print(component_name, ttr)
        return ttr
    # if rate is not provided assign a high value to repair the component as quick as possible
    except (Exception,):
        # if the particular specific component (say like Line632) is not available, assign a generic rate (say Line)
        r_mu = dict_all[1][component_name.split('.', 1)[0]]
        try:
            r_sd = dict_all[17][component_name]
        except (Exception,):
            r_sd = dict_all[17][component_name.split('.', 1)[0]]

        # obtain the repair time from the repair rate assigned above multiplied by a normal distribution
        ttr = np.random.normal(1 / r_mu, r_sd, 1) + travel_time + prep_time + op_delay
        return ttr


# function to assign updated time to failure after condition monitoring triggers repair for a monitored component
def ttf_cm(maintenance_model, component_name, dict_all, ttf, hour, df_loads_kW):
    ttd_flag = 0
    ttf_upd = ttf
    # find the preparation time required
    # try and exception just to avoid any possible error
    try:
        travel_distance = dict_all[6][component_name]
    except (Exception,):
        travel_distance = dict_all[6]['Speed (Unit/hour)'] * 1

    # now estimate a time for preparation works
    travel_time = travel_distance / dict_all[6]['Speed (Unit/hour)']
    prep_time = 1.5
    total_prep_time = travel_time + prep_time

    # cushion = ttf - hour
    # previously cushion was considered ttf-hour; however, ttf is around 1, 2, or 10 or 50; hence, ttf itself is the
    # cushion not the difference of ttf and hour; the difference will always be negative, leading to no use of CM at all
    # As an update, the total_prep_time is added that would occur when the component fails without prior detection
    cushion = ttf - total_prep_time

    # find the feasible failure time
    dict_weekend = pd.DataFrame.from_dict(dict_all[9], orient='index')
    dict_holiday = pd.DataFrame.from_dict(dict_all[10], orient='index')
    # dict_daytime = pd.DataFrame.from_dict(dict_all[11], orient='index')
    # dict_nighttime = pd.DataFrame.from_dict(dict_all[18], orient='index')

    weekend_list = dict_weekend[0].to_list()
    holiday_list = dict_holiday[0].to_list()
    # daytime_list = dict_daytime[0].to_list()
    # nighttime_list = dict_nighttime[0].to_list()

    first_hour = 10000
    second_hour = 10000
    third_hour = 10000
    # fourth_hour = 10000

    if maintenance_model == 0:
        # weekend based maintenance
        for i in range(hour, len(weekend_list)):
            if weekend_list[i] == 1:
                first_hour = i - hour
                break
        for i in range(hour, len(holiday_list)):
            if holiday_list[i] == 1:
                second_hour = i - hour
                break
        # for i in range(hour, len(daytime_list)):
        #     if daytime_list[i] == 1:
        #         third_hour = i - hour
        #         break

        # check if holiday comes before weekend or not
        # first priority holiday if before weekend
        # second priority weekend
        # third priority holiday after weekend
        # fourth priority daytime
        if cushion >= first_hour >= second_hour:
            ttf_upd = second_hour
            ttd_flag = 1
        elif first_hour <= cushion:
            ttf_upd = first_hour
            ttd_flag = 1
        elif second_hour <= cushion:
            ttf_upd = second_hour
            ttd_flag = 1
        # elif third_hour <= cushion:
        #     ttf_upd = third_hour
        #     ttd_flag = 1
        else:
            ttf_upd = ttf
            ttd_flag = 0

    elif maintenance_model == 1:

        # estimate the time for maintenance activity for the particular component
        # ttd flag is 1 as the preparation time is considered elsewhere
        number_of_maintenance_hours = int(ind_ttr(component_name, dict_all, hour, ttd_flag=1))
        if number_of_maintenance_hours < 1:
            number_of_maintenance_hours = 1

        # take the data of next 7 days; to include the weekend in between
        # df_loads_kW_slice = df_loads_kW.iloc[hour:hour+24*7, :].copy(deep=True)
        # this has been updated to see more into the future, which is true for power transformers and ckt breakers
        # CM is also expected to identify the estimated time of failure as well
        if np.isscalar(hour):
            year_hour = np.floor(hour).astype(int)
        else:
            year_hour = np.floor(hour[0]).astype(int)

        if np.isscalar(ttf):
            time_to_see = np.floor(ttf + hour).astype(int)

        else:
            time_to_see = np.floor(ttf[0] + hour).astype(int)

        if time_to_see > 8759 - hour:
            time_to_see = np.floor(8759 - hour).astype(int)

        df_loads_kW_slice = df_loads_kW.iloc[year_hour:time_to_see, :].copy(deep=True)

        # sometimes this dataframe couleb be empty, hence, need to chec kand provide appropriate value for first hour

        if not df_loads_kW_slice.empty:
            # sum the total expected load
            df_loads_kW_slice.loc[:, "sum"] = df_loads_kW_slice.sum(axis=1)
            # take the rolling sum for the number of maintenance hours
            df_loads_sum = df_loads_kW_slice.rolling(number_of_maintenance_hours).sum()
            df_loads_sum.reset_index(drop=True, inplace=True)

            # get the value of minimum index, this starts from 0 as we have reset index already
            minimum_index = df_loads_sum['sum'].idxmin(axis=0)

        else:
            minimum_index = 10000000 ### a large value

            # minimum load estimate based maintenance
        first_hour = minimum_index - (number_of_maintenance_hours - 1)

        for i in range(hour, len(weekend_list)):
            if weekend_list[i] == 1:
                second_hour = i - hour
                break
        for i in range(hour, len(holiday_list)):
            if holiday_list[i] == 1:
                third_hour = i - hour
                break
        # for i in range(hour, len(daytime_list)):
        #     if daytime_list[i] == 1:
        #         fourth_hour = i - hour
        #         break

        # check if weekend and holiday comes before nighttime or not
        # first priority express_time and then holiday if before weekend
        # second priority holiday before weekend
        # third priority weekend
        # fourth priority holiday after weekend
        # fifth priority daytime
        if 360 < first_hour <= 5000000:
            print(f" ------------- First hour of lowest energy is: {first_hour}--------------")
        if 360 < first_hour <= 5000000:  # after fiften days and a less than a large number to avoid the empty dataframe case above
            ttf_upd = first_hour
            ttd_flag = 1
            print(f"--------------Time to fail is updated as {first_hour}")
        elif first_hour <= cushion and first_hour <= second_hour and first_hour <= third_hour:
            ttf_upd = first_hour
            ttd_flag = 1
        elif second_hour <= cushion and second_hour <= third_hour:
            ttf_upd = second_hour
            ttd_flag = 1
        elif third_hour <= cushion:
            ttf_upd = third_hour
            ttd_flag = 1
        # elif fourth_hour <= cushion:
        #     ttf_upd = fourth_hour
        #     ttd_flag = 1
        else:
            ttf_upd = ttf
            ttd_flag = 0
    else:
        print("Maintenance Modeling not set correctly, Set 0 for weekend based and 1 for express based maintenance")

    # print(f"---For {component_name}, ttf is {ttf}, cushion is {cushion}, and updated ttf is {ttf_upd}")
    # if maintenance_model == 0:
    #     print(f"----Weekend hour was {first_hour}, Holiday hour was {second_hour}")
    # else:
    #     print(f"-Express {first_hour}, Weekend {second_hour}, Holiday {third_hour}, ttf {ttf_upd}, ttd flag {ttd_flag}")
    would_not_fail = 0
    if ttf > 10000:
        print(f"---- Component {component_name} that would not fail has been failed--------")
        would_not_fail = 1
    return would_not_fail, ttd_flag, ttf_upd
