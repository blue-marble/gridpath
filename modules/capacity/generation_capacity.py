#!/usr/bin/env python

import os
import csv
from pyomo.environ import *


def determine_dynamic_components(m, inputs_directory):
    """
    Populate the lists of dynamic components
    :param m:
    :param inputs_directory:
    :return:
    """
    with open(os.path.join(inputs_directory, "generation_capacity.tab"), "rb") as generation_capacity_file:
        generation_capacity_reader = csv.reader(generation_capacity_file, delimiter="\t")
        generation_capacity_reader.next()  # skip header
        for row in generation_capacity_reader:
            generator = row[0]
            print generator
            m.generator_capabilities[generator] = ["Power"]

    with open(os.path.join(inputs_directory, "reserve_generators.tab"), "rb") as reserve_generators_file:
        reserve_generators_reader = csv.reader(reserve_generators_file, delimiter="\t")
        reserve_generators_reader.next()  # skip header
        for row in reserve_generators_reader:
            generator = row[0]
            m.generator_capabilities[generator].append("Upward_Reserve")


def add_model_components(m):
    m.GENERATORS = Set()
    m.RESERVE_GENERATORS = Set(within=m.GENERATORS)

    m.capacity = Param(m.GENERATORS)
    m.variable_cost = Param(m.GENERATORS)


def load_model_data(m, data_portal, inputs_directory):
    data_portal.load(filename=os.path.join(inputs_directory, "generation_capacity.tab"),
                     index=m.GENERATORS,
                     param=(m.capacity, m.variable_cost)
                     )

    data_portal.load(filename=os.path.join(inputs_directory, "reserve_generators.tab"),
                     set=m.RESERVE_GENERATORS
                     )


def view_loaded_data(instance):
    print "Viewing data"
    for g in instance.GENERATORS:
        print(g, instance.capacity[g])