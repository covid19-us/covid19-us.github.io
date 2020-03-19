from urllib.request import urlopen, Request
import json
import os
import numpy as np
import scipy as sp
import scipy.stats
import datetime
import random
import math
from matplotlib import pyplot as plt

n_simulations = 500
step = 1  # timestep (days)


def sim_days(R0=2.5, CFR=0.02):
    """
    Run simulation with given reproduction number (R0) and case fatality
    ratio (CFR), starting from a single case.

    This function is called n_simulations times, and the same set of 500 
    simulations is then used to make predictions for each states.

    Returns: A list of cumulative cases, and a list of cumulative deaths.
    """
    print("simulating R0={} CFR={}".format(R0, CFR))

    serial_interval = sp.stats.lognorm(s=0.5680, scale=math.exp(1.3868))
    onset_to_death = sp.stats.gamma(4.726, 0, 1/(0.3151))

    max_days = 100  # maximum days to simulate
    n_timesteps = int(max_days / step)
    # new cases at each timestep
    new_cases = np.zeros(n_timesteps, dtype=np.int)
    # new deaths at each timestep
    new_deaths = np.zeros(n_timesteps, dtype=np.int)
    new_cases[0] = 1

    for t1 in range(n_timesteps):
        interval_next = serial_interval.rvs(new_cases[t1])
        add_cases = np.random.choice(
            np.round(t1+interval_next/step),
            size=np.random.poisson(R0 * new_cases[t1]))
        interval_death = onset_to_death.rvs(new_cases[t1])
        add_deaths = np.random.choice(
            np.round(t1+interval_death/step),
            size=np.random.poisson(CFR * new_cases[t1]))

        for t2 in range(t1+1, n_timesteps):
            new_cases[t2] += (add_cases == t2).sum()
            new_deaths[t2] += (add_deaths == t2).sum()

        if np.sum(new_deaths[:t1]) > 200:
            break

    return (np.cumsum(new_cases[:t1]).tolist(),
            np.cumsum(new_deaths[:t1]).tolist())


def sample_n_infected(n_deaths, R0=None, CFR=None):
    """
    Estimate the number of cases in a state with n recorded deaths.
    Returns a list of samples 

    If R0 or CFR are provided as lists, creates a concatenated list
    using simulations for every R0 and every CFR provided.
    """
    samples = []  # sampled number of cases for each simulation
    R0s = [1.5, 2, 2.5, 3] if R0 is None else [R0]
    CFRs = [0.005, 0.01, 0.02, 0.03] if CFR is None else [CFR]
    for R0 in R0s:
        for CFR in CFRs:
            for cases, deaths in sims[R0][CFR]:
                exact_match = [i for i, v in enumerate(
                    deaths) if v == n_deaths]
                if len(exact_match) >= 1:
                    # If the simulation contains multiple days with n_deaths,
                    # choose one at random
                    samples.append(cases[
                        random.choice(exact_match)
                    ])
                else:
                    # otherwise, find the first day on which the number of deaths
                    # exceeds n_deaths
                    try:
                        samples.append(cases[
                            next(i for i, v in enumerate(
                                deaths) if v >= n_deaths)
                        ])
                    except StopIteration:
                        pass

    return samples


if __name__ == "__main__":
    # Load simulations if already created, otherwise recreate and save
    try:
        with open("sims.json", "r") as f:
            sims = {float(k1): {float(k2): v2 for k2, v2 in v1.items()}
                    for k1, v1 in json.load(f).items()}
        print("loaded")
    except FileNotFoundError:
        sims = {}
        for R0 in [1.5, 2, 2.5, 3]:
            sims[R0] = {}
            for CFR in [0.005, 0.01, 0.02, 0.03]:
                sims[R0][CFR] = [sim_days(R0, CFR)
                                 for _ in range(n_simulations)]
        with open("sims.json", "w") as f:
            json.dump(sims, f)
        print("saved.")

    # Get up-to-date data from covidtracking
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
    url = 'http://covidtracking.com/api/states/daily'

    req = Request(url=url, headers=headers)
    output = urlopen(req).read()
    data = json.loads(output.decode('utf-8'))

    states = list(set([d['state'] for d in data]))

    def get_positive(d):
        """
        Gets the number of positive tests for a given record from the covidtracking data
        """
        if 'positive' in d and d['positive'] is not None:
            return d['positive']
        else:
            return 0

    # Make predictions on the covidtracking data
    allstats = {}
    for R0 in [1.5, 2, 2.5, 3, None]:
        for CFR in [0.005, 0.01, 0.02, 0.03, None]:
            stats = {}
            for state in states:
                allrecords = [d for d in data if d['state'] == state]
                allrecords = sorted(allrecords, key=get_positive)
                # records = [d for d in allrecords
                #            if d.get('death', None) is not None
                #            and d.get('death', None) != 0]

                # if len(records) > 0:
                if get_positive(allrecords[-1]) > 0:
                    if 'death' in allrecords[-1] and allrecords[-1]['death'] is not None:
                        deaths = allrecords[-1]['death']
                    else:
                        deaths = 0
                    predictions = sorted(
                        sample_n_infected(deaths, R0=R0, CFR=CFR))
                    predictions = [p for p in predictions if p >=
                                   get_positive(allrecords[-1])]

                    print("{}: [{}, {}, {}, {}]".format(
                        state,
                        predictions[int(len(predictions)*0.025)],
                        predictions[int(len(predictions)*0.25)],
                        predictions[int(len(predictions)*0.75)],
                        predictions[int(len(predictions)*0.975)]))

                    stats[state] = {
                        'positive': get_positive(allrecords[-1]),
                        'deaths': deaths,
                        'lower95': predictions[int(len(predictions)*0.025)],
                        'lower50': predictions[int(len(predictions)*0.25)],
                        'median': predictions[int(len(predictions)*0.50)],
                        'upper50': predictions[int(len(predictions)*0.75)],
                        'upper95': predictions[int(len(predictions)*0.975)]
                    }
                else:
                    stats[state] = {
                        'positive': 0,
                    }
            stats_sorted = sorted(stats.items(), key=lambda x: (
                x[1].get('median', 0), x[0]), reverse=True)
            allstats["{},{}".format(R0, CFR)] = stats_sorted

    # Update webpage
    dateint = max(x['date'] for x in allrecords)
    datestr = "{}-{}-{}".format(str(dateint)
                                [:4], str(dateint)[4:6], str(dateint)[6:8])

    with open("index_template.md", "r") as f:
        template = f.read()

    with open("index.md", 'w') as f:
        f.write(template.replace("{{ stats }}", json.dumps(
            allstats)).replace("{{ date }}", datestr))
