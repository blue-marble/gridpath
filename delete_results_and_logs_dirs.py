import os
import shutil

for subproblem in range(1, 10400+1):
    print(subproblem)
    subproblem_dir = os.path.join(
        "/Volumes/Samsung_X5/ra/scenarios_REPORT",
        "ScenarioA_MonteCarlo_200_vm_test",
        str(subproblem)
    )

    for d in ["logs", "results"]:
        dir_to_remove = os.path.join(subproblem_dir, d)
        print(dir_to_remove)

        shutil.rmtree(dir_to_remove)
