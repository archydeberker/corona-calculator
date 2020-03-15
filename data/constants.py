"""
Range estimates for various epidemiology constants.
Data gathered from https://github.com/midas-network/COVID-19/tree/master/parameter_estimates/2019_novel_coronavirus
and https://www.mdpi.com/2077-0383/9/2/462/htm
Parameter bounds were subjectively chosen from positively peer-reviewed estimates.
"""

import pandas as pd


class Countries:
    data = pd.read_csv("data/country_data.csv", index_col="Country").to_dict(
        orient="index"
    )
    countries = list(data.keys())


"""
SIR model constants
"""


class RemovalRate:
    min = 1 / 7
    default = 1 / 10  # Recovery period around 10 days
    max = 1 / 14


class TransmissionRatePerContact:
    # Probability of a contact between carrier and susceptible leading to infection
    min = 0.01
    default = (
        0.018
    )  # Found using binomial distribution in Wuhan scenario: 14 contacts per day, 10 infectious days, 2.5 average people infected.
    max = 0.022


class AverageDailyContacts:
    min = 0
    max = 100
    default = 20


"""
Health care constants
"""


class AscertainmentRate:
    # Proportion of true cases diagnosed
    min = 0.05
    max = 0.25
    default = 0.1


class MortalityRate:
    min = 0.005
    max = 0.05
    default = 0.01


class HospitalizationRate:
    # Cases requiring hospitalization
    min = 0.1
    max = 0.2
    default = 0.15


class VentilationRate:
    # Cases requiring ICU care
    # From chart 18 https://medium.com/@tomaspueyo/coronavirus-act-today-or-people-will-die-f4d3d9cd99ca
    min = 0.01
    max = 0.02
    default = 0.015
