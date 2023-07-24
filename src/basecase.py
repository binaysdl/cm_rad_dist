# This is not a sample Python script.
# This script runs the basecase load flow in OpenDSS and returns nothing.
import opendssdirect as dss


def get_basecase_results(dss_file, loads_kW, loads_kVAR, df_loads_kW, df_loads_kVAR):
    print("--------------- Initiating load flow without any disconnections in the system -----------------------")
    # Run simulation without fault for one year
    casename = "01_Without_Fault"
    dss.Text.Command("Clear")
    dss.Text.Command(f"compile [{dss_file}]")
    dss.Text.Command("set hour=0 sec=0")
    dss.Text.Command(f"set case = {casename}")
    dss.Text.Command("Set Mode=Dutycycle Stepsize=3600s number=1")

    for i in range(0, 8760):
        for j in range(0, df_loads_kW.shape[1]):
            dss.Text.Command(f"{loads_kW[j]}.kW={df_loads_kW.iloc[i][j]}")
            dss.Text.Command(f"{loads_kVAR[j]}.kVAR={df_loads_kVAR.iloc[i][j]}")
        dss.Solution.Solve()

    dss.Basic.DataPath("../../outputs/monitor_files/")
    dss.Basic.AllowEditor(0)
    dss.Basic.AllowForms(0)
    # lst_monitors = dss.Monitors.AllNames()

    dss.Monitors.First()
    for i in range(dss.Monitors.Count()):
        dss.Monitors.Show()
        dss.Monitors.Next()
