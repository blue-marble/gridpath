import os

n = 0

for subproblem in range(1, 10400+1):
    print(subproblem)
    results_dir = os.path.join(
        os.getcwd(),
        str(subproblem), "results"
    )

    if os.path.exists(results_dir) :
        n += 1


print("Total results directories: ", n)
