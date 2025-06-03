import pybamm
import numpy as np
import pandas as pd
from multiprocessing import Pool
from pybamm import Parameter, constants, exp
import os


pybamm.set_logging_level("NOTICE")

option={
"SEI":"solvent-diffusion limited",
"particle mechanics": ("swelling and cracking", "swelling only"),
"particle" : "Fickian diffusion",
"loss of active material": "stress and reaction-driven",
"thermal": "lumped",
"SEI film resistance": "distributed",
"SEI porosity change" : "true", 
"lithium plating": "partially reversible",
"x-average side reactions": "true"
}
 

model = pybamm.lithium_ion.SPMe(options=option)
param1 = pybamm.ParameterValues("OKane2022")


cycle_drive = 1095

N = list(range(1, 1095, 50))


def get_experiment_drive_crate(drive_cycle):
    drive_crate_dict = {
        "Panskura": , #insert the drive cycle path from the file 
        "Hyderabad": , #insert the drive cycle path from the file 
        "Delhi": , #insert the drive cycle path from the file 
        "WLTC": , #insert the drive cycle path from the file 
    }

    drive_duration_dict = {

        "Panskura": , #insert the drive cycle duration 
        "Hyderabad": , #insert the drive cycle duration
        "Delhi": , #insert the drive cycle duration
        "WLTC": , #insert the drive cycle duration
    }

    drive_rest_dict = {
        "Panskura": , #insert the drive cycle rest duration 
        "Hyderabad": , #insert the drive cycle rest duration
        "Delhi": , #insert the drive cycle rest duration
        "WLTC": , #insert the drive cycle rest duration
    }

    discharge_c_rate = drive_crate_dict[drive_cycle]
    duration = drive_duration_dict[drive_cycle]
    rest = drive_rest_dict[drive_cycle]
    experiment = pybamm.Experiment(
        [
            (
                f"Discharge at {discharge_c_rate}C for {duration} seconds",
                "Rest for 9 hours (1 hour period)",
                f"Discharge at {discharge_c_rate}C for {duration} seconds",
                "Rest for 20 minutes",
                "Charge at 0.1C until 4.2V",
                "Hold at 4.2V until 10mA",
                f"Rest for {rest} hours (1 hour period)"
            )
        ] * cycle_drive
    )
    return experiment


solver = pybamm.CasadiSolver("safe", return_solution_if_failed_early=True, dt_max=200, max_step_decrease_count=20)
var_pts={"x_n": 40, "x_s":20, "x_p": 40, "r_n": 40, "r_p":40}

def run_simulation(args):
    drive_cycle, temp_amb_path = args
    experiment = get_experiment_drive_crate(drive_cycle)
    temp_amb = pd.read_excel(temp_amb_path, comment="#", header=None).to_numpy()
    timescale = param1.evaluate(model.timescale)
    temp_interpolant = pybamm.Interpolant(temp_amb[:, 0], temp_amb[:, 1] + 273.15, timescale * pybamm.t/(3600), interpolator="linear")
    param1["Ambient temperature [K]"] = temp_interpolant
    param1["Initial temperature [K]"] = temp_amb[0,1] + 273.15

    sim=pybamm.Simulation(model, experiment = experiment,parameter_values = param1,solver=solver,var_pts=var_pts)
    solution=sim.solve(calc_esoh=False,save_at_cycles= N)

    Tcarr = solution.summary_variables["Throughput capacity [A.h]"]
    mcaparr = solution.summary_variables["Measured capacity [A.h]"]
    cyclearr = solution.summary_variables["Cycle number"]
    L1 = solution.summary_variables["Loss of lithium inventory [%]"]
    L2 = solution.summary_variables["Loss of lithium inventory, including electrolyte [%]"]
    L3 = solution.summary_variables["Loss of capacity to lithium plating [A.h]"]
    L4 = solution.summary_variables["Loss of capacity to SEI [A.h]"]
    L5 = solution.summary_variables["Total capacity lost to side reactions [A.h]"]
    L6 = solution.summary_variables["Total lithium [mol]"]
    L7 = solution.summary_variables["Total lithium in electrolyte [mol]"]
    L8 = solution.summary_variables["Total lithium in positive electrode [mol]"]
    L9 = solution.summary_variables["Positive electrode capacity [A.h]"]
    L10 = solution.summary_variables["Loss of active material in positive electrode [%]"]
    L11 = solution.summary_variables["Total lithium in negative electrode [mol]"]
    L12 = solution.summary_variables["Negative electrode capacity [A.h]"]
    L13 = solution.summary_variables["Loss of active material in negative electrode [%]"]
    L14 = solution.summary_variables["Total lithium in particles [mol]"]
    L15 = solution.summary_variables["Total lithium lost [mol]"]
    L16 = solution.summary_variables["Total lithium lost from particles [mol]"]
    L17 = solution.summary_variables["Total lithium lost from electrolyte [mol]"]
    L18 = solution.summary_variables["Total lithium lost to side reactions [mol]"]
    L19 = solution.summary_variables["Loss of lithium to SEI [mol]"]
    L20 = solution.summary_variables["Loss of lithium to lithium plating [mol]"]
    L21 = solution.summary_variables["Loss of lithium to SEI on cracks [mol]"]

    df = pd.DataFrame({
                    "Cycle number":cyclearr,
                    "Throughput capacity [A.h]": Tcarr,
                    "Measured capacity [A.h]": mcaparr,
                    "Loss of lithium inventory [%]" : L1,
                    "Loss of lithium inventory, including electrolyte [%]": L2,
                    "Loss of capacity to lithium plating [A.h]": L3, 
                    "Loss of capacity to SEI [A.h]": L4, 
                    "Total capacity lost to side reactions [A.h]" : L5,
                    "Total lithium [mol]" : L6,
                    "Total lithium in electrolyte [mol]" : L7,
                    "Total lithium in positive electrode [mol]" : L8,
                    "Positive electrode capacity [A.h]" : L9,
                    "Loss of active material in positive electrode [%]" : L10,
                    "Total lithium in negative electrode [mol]" : L11,
                    "Negative electrode capacity [A.h]" : L12,
                    "Loss of active material in negative electrode [%]" : L13,
                    "Total lithium in particles [mol]" : L14,
                    "Total lithium lost [mol]" : L15,
                    "Total lithium lost from particles [mol]" : L16,
                    "Total lithium lost from electrolyte [mol]" : L17,
                    "Total lithium lost to side reactions[mol]" : L18,
                    "Loss of lithium to SEI [mol]" : L19,
                    "Loss of lithium to lithium plating [mol]" : L20,
                    "Loss of lithium to SEI on cracks [mol]" : L21

    })


    drive_cycle_name = drive_cycle.replace(" ", "_")
    temp_amb_name = os.path.splitext(os.path.basename(temp_amb_path))[0]


    df.to_csv(f"{drive_cycle_name}_{temp_amb_name}_summary.csv", index=False)
    solution.save_data(f"{drive_cycle_name}_{temp_amb_name}_data.csv",
                        [
                            "Time [h]",
                            "Current [A]",
                            "Terminal voltage [V]",
                            "X-averaged cell temperature [K]",  
                            "Ambient temperature [K]",
                            "X-averaged negative particle crack length [m]", 
                            "X-averaged total SEI thickness [m]",
                        ], to_format="csv" )

if __name__ == "__main__":
    drive_cycles = [
        "Panskura",
        "Hyderabad",
        "Delhi",
        "WLTC"
    ]

    temp_amb_path = [
        r"C:\Users\Sai\miniconda3\envs\crack\Lib\site-packages\pybamm\input\drive_cycles\Temperature\delhi_everyhour.xlsx",
        r"C:\Users\Sai\miniconda3\envs\crack\Lib\site-packages\pybamm\input\drive_cycles\Temperature\kolkata_everyhour.xlsx",
        r"C:\Users\Sai\miniconda3\envs\crack\Lib\site-packages\pybamm\input\drive_cycles\Temperature\churu_everyhour.xlsx"
    ]

    with Pool(4) as p:
        args_list = [(drive_cycle, temp_amb) for drive_cycle in drive_cycles for temp_amb in temp_amb_path]
        p.map(run_simulation, args_list)



