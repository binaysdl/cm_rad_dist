# This is not a sample Python script.
# This script works on getting a couple of lists and dataframes for load of the network
import pandas as pd


def get_fault_able_elements(circuit_all_element_names):
    df = pd.DataFrame(circuit_all_element_names)

    # Include the Power Delivery and Power Conversion Elements at the moment The order for PDE is  Lines,
    # Transformers, Capacitors and Reactors The order for PCE is Loads, Generators, Vsource and Isource You will need
    # to add the Fuse, Recloser and Relay in the future in list of could fail components ---------------------Power
    # Delivery Elements--------------------------------------------------------------------------
    df_line = df[df[0].str.startswith('Line')]
    df_transformer = df[df[0].str.startswith('Transformer')]  # keep columns that starts with
    # This also brings along the RegControl element which shall need to be removed.
    df_transformer = df_transformer[~df_transformer[0].astype(str).str.startswith('Transformer.r')]  # remove columns
    df_load = df[df[0].str.startswith('Load')]

    # concatenate dataframes --- remember the order, which is same for the following loops now.
    ckt_fault_able_elements = pd.concat([df_line, df_transformer, df_load], ignore_index=True)

    return ckt_fault_able_elements


def get_switch_elements(ckt_fault_able_elements, dict_all):
    # obtains from the database of switch elements and sees whether a line is treated as a switch or not
    # initializing list of switch
    switch_elements = []

    # record the index of switch,
    for i in range(ckt_fault_able_elements.shape[0]):
        switch_elements.append(i * dict_all[12][ckt_fault_able_elements.iloc[i][0]])
    switch_elements = list(filter(lambda num: num != 0, switch_elements))

    if dict_all[12][ckt_fault_able_elements.iloc[0][0]] == 1:
        switch_elements.append(0)

    ckt_non_switch_elements = ckt_fault_able_elements.index.isin(switch_elements)

    df_ckt_switch_elements = ckt_fault_able_elements[ckt_non_switch_elements]

    return df_ckt_switch_elements


def get_cm_elements(ckt_fault_able_elements, dict_all):
    # obtains from the database of switch elements and sees whether a line is treated as a switch or not
    # initializing list of switch
    cm_elements = []

    # record the index of switch,
    for i in range(ckt_fault_able_elements.shape[0]):
        cm_elements.append(i * dict_all[12][ckt_fault_able_elements.iloc[i][0]])
    cm_elements = list(filter(lambda num: num != 0, cm_elements))

    if dict_all[12][ckt_fault_able_elements.iloc[0][0]] == 1:
        cm_elements.append(0)

    non_cm_elements = ckt_fault_able_elements.index.isin(cm_elements)

    df_ckt_cm_elements = ckt_fault_able_elements[non_cm_elements]

    return df_ckt_cm_elements
