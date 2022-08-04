from subprocess import call

call(
    """
cplex -c read "./examples/test/logs/test.lp" optimize write "./examples/logs/test/test.sol"
""",
    shell=True,
)
