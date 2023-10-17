from pyomo.environ import AbstractModel, Set, Param, Var, Expression, \
    Constraint, Objective, PositiveIntegers, NonNegativeReals

m = AbstractModel()

m.TMPS = Set(
    domain=PositiveIntegers, ordered=True, initialize=[20301, 20302, 20401, 20402]
)

m.PERIODS = Set(domain=PositiveIntegers, ordered=True, initialize=[2030, 2040])

m.period = Param(
    m.TMPS,
    within=m.PERIODS,
    initialize={20301: 2030, 20302: 2030, 20401: 2040, 20402: 2040},
)

m.PROJECTS = Set(initialize=["Project1", "Project2"])

m.Build = Var(m.PROJECTS, m.PERIODS, domain=NonNegativeReals)


def total_build_rule(mod, prj, prd):
    return sum(mod.Build[prj, p] for p in mod.PERIODS if p <= prd)


m.Total_Build = Expression(m.PROJECTS, m.PERIODS, rule=total_build_rule)

m.build_cost = Param(
    m.PROJECTS,
    m.PERIODS,
    domain=NonNegativeReals,
    initialize={
        ("Project1", 2030): 10.0,
        ("Project1", 2040): 8.0,
        ("Project2", 2030): 12.0,
        ("Project2", 2040): 5.0,
    },
)

m.Power = Var(m.PROJECTS, m.TMPS, domain=NonNegativeReals)

m.power_cost = Param(
    m.PROJECTS,
    domain=NonNegativeReals,
    initialize={"Project1": 1.0, "Project2": 1.2},
)


def power_constraint_rule(mod, prj, tmp):
    return mod.Power[prj, tmp] <= mod.Total_Build[prj, mod.period[tmp]]


m.Power_Constraint = Constraint(m.PROJECTS, m.TMPS, rule=power_constraint_rule)

m.sys_load = Param(
    m.TMPS,
    domain=NonNegativeReals,
    initialize={20301: 100.0, 20302: 200.0, 20401: 200.0, 20402: 300.0},
)


def meet_load_constraint_rule(mod, tmp):
    return sum(mod.Power[prj, tmp] for prj in mod.PROJECTS) >= mod.sys_load[tmp]


m.Meet_Load_Constraint = Constraint(m.TMPS, rule=meet_load_constraint_rule)


def obj_expression(mod):
    return sum(
        mod.Build[prj, prd] * mod.build_cost[prj, prd]
        for prj in mod.PROJECTS
        for prd in mod.PERIODS
    ) + sum(
        mod.Power[prj, tmp] * mod.power_cost[prj]
        for prj in mod.PROJECTS
        for tmp in mod.TMPS
    )


m.Objective = Objective(rule=obj_expression)
