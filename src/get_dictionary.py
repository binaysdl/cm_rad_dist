import pathlib

import pandas as pd


# function to obtain the dictionary of files with just two columns
def get_2d_dict(filename):
    # read data of the files
    df = pd.read_csv(filename)
    # dropping null value columns to avoid errors
    df.dropna(inplace=True)
    # convert the dataframe into a dictionary of failure rates
    # dict_df = df.set_index('Component')['failure_rate_lambda'].to_dict()
    dict_df = dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
    # dict_df = df.to_dict()
    # return dictionary to the calling function
    return dict_df


def get_dictionary_file(script_path, condition_monitoring):
    # rate files
    failure_rate_file = pathlib.Path(script_path).joinpath("data_files/rate_info/failure_rates.csv")
    failure_rate_u_file = pathlib.Path(script_path).joinpath("data_files/rate_info/failure_rates_u.csv")
    repair_rate_file = pathlib.Path(script_path).joinpath("data_files/rate_info/repair_rates.csv")
    repair_sd_file = pathlib.Path(script_path).joinpath("data_files/rate_info/repair_rates_sd.csv")

    if condition_monitoring:
        cm_file = pathlib.Path(script_path).joinpath("data_files/rate_info/cm_rates.csv")
    else:
        cm_file = pathlib.Path(script_path).joinpath("data_files/rate_info/zero_cm_rates.csv")
    cm_sd_file = pathlib.Path(script_path).joinpath("data_files/rate_info/cm_rates_sd.csv")
    cm_det_prob_file = pathlib.Path(script_path).joinpath("data_files/rate_info/cm_det_prob.csv")

    # circuit breaker/opener data
    ckt_breaker_file = pathlib.Path(script_path).joinpath("data_files/system_info/ckt_breaker_database.csv")
    distance_data_file = pathlib.Path(script_path).joinpath("data_files/system_info/distance.csv")
    is_breaker_file = pathlib.Path(script_path).joinpath("data_files/system_info/is_breaker.csv")
    is_cm_file = pathlib.Path(script_path).joinpath("data_files/system_info/is_cm.csv")

    # weather file
    lightning_data_file = pathlib.Path(script_path).joinpath("data_files/weather_info/lightning.csv")
    temperature_data_file = pathlib.Path(script_path).joinpath("data_files/weather_info/temperature.csv")

    # The line length should be same as the failure rate unit
    line_length_file = pathlib.Path(script_path).joinpath("data_files/system_info/line_parameters.csv")
    op_delay_data_file = pathlib.Path(script_path).joinpath("data_files/operation_calendar_info/op_delay.csv")
    weekend_info = pathlib.Path(script_path).joinpath("data_files/operation_calendar_info/weekend_info.csv")
    holiday_info = pathlib.Path(script_path).joinpath("data_files/operation_calendar_info/holiday_info.csv")
    daytime_work_info = pathlib.Path(script_path).joinpath("data_files/operation_calendar_info/daytime_work_info.csv")
    # nighttime_work_info = pathlib.Path(script_path).joinpath(
    #     "data_files/operation_calendar_info/nighttime_work_info.csv")

    dict_failure_rate = get_2d_dict(failure_rate_file)
    dict_repair_rate = get_2d_dict(repair_rate_file)
    dict_cm_rate = get_2d_dict(cm_file)
    dict_ckt_bkr = get_2d_dict(ckt_breaker_file)
    dict_lightning = get_2d_dict(lightning_data_file)
    dict_temperature = get_2d_dict(temperature_data_file)
    dict_distance = get_2d_dict(distance_data_file)
    dict_line_length = get_2d_dict(line_length_file)
    dict_op_delay = get_2d_dict(op_delay_data_file)
    dict_weekend = get_2d_dict(weekend_info)
    dict_holiday = get_2d_dict(holiday_info)
    dict_daytime_work = get_2d_dict(daytime_work_info)
    dict_is_breaker = get_2d_dict(is_breaker_file)
    dict_is_cm = get_2d_dict(is_cm_file)
    dict_cm_sd = get_2d_dict(cm_sd_file)
    dict_cm_det = get_2d_dict(cm_det_prob_file)
    dict_failure_u_rate = get_2d_dict(failure_rate_u_file)
    dict_repair_sd = get_2d_dict(repair_sd_file)
    # dict_nighttime_work_info = get_2d_dict(nighttime_work_info)

    dict_all = [dict_failure_rate, dict_repair_rate, dict_cm_rate, dict_ckt_bkr, dict_lightning, dict_temperature,
                dict_distance, dict_line_length, dict_op_delay, dict_weekend, dict_holiday, dict_daytime_work,
                dict_is_breaker, dict_is_cm, dict_cm_sd, dict_cm_det, dict_failure_u_rate, dict_repair_sd]

    return dict_all
