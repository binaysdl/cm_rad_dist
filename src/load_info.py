# This is not a sample Python script.
# This script works on getting a couple of lists and dataframes for load of the network
import pathlib

import numpy as np
import pandas as pd


def get_load_details(script_path):

    # Importing load kW and kVAR files to the system
    load_kw_info_file = pathlib.Path(script_path).joinpath("data_files/load_info/loads_kW_info.csv")
    df_loads_kw = pd.read_csv(load_kw_info_file, sep=',')
    loads_kw = df_loads_kw.loc[0, :].values.tolist()
    # Drop first row
    df_loads_kw.drop(index=df_loads_kw.index[0], axis=0, inplace=True)
    # Multiply the loads_ratings with the multipliers
    df_loads_kw = df_loads_kw.multiply(np.array(loads_kw), axis='columns')
    loads_kw = list(df_loads_kw.columns.values)  # Name of loads as list for loops

    load_kvar_info_file = pathlib.Path(script_path).joinpath("data_files/load_info/loads_kVAR_info.csv")
    # assigning loads - either pf or kVAR, system dependent
    df_loads_kvar = pd.read_csv(load_kvar_info_file, sep=',')
    loads_kvar = df_loads_kvar.loc[0, :].values.tolist()
    df_loads_kvar.drop(index=df_loads_kvar.index[0], axis=0, inplace=True)
    df_loads_kvar = df_loads_kvar.multiply(np.array(loads_kvar), axis='columns')
    loads_kvar = list(df_loads_kvar.columns.values)

    return df_loads_kw, df_loads_kvar, loads_kw, loads_kvar
