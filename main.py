from urllib.request import urlopen, Request
import json
import os
import numpy as np
import scipy as sp
import scipy.stats
import datetime
import random
import math

n_simulations = 500
step = 1  # timestep (days)

US_STATE_POPULATIONS = {"AL": 4903185, "AK": 731545, "AZ": 7278717, "AR": 3017804, "CA": 39512223, "CO": 5758736, "CT": 3565287, "DE": 973764, "DC": 705749, "FL": 21477737, "GA": 10617423, "HI": 1415872, "ID": 1787065, "IL": 12671821, "IN": 6732219, "IA": 3155070, "KS": 2913314, "KY": 4467673, "LA": 4648794, "ME": 1344212, "MD": 6045680, "MA": 6892503, "MI": 9986857, "MN": 5639632, "MS": 2976149,
                        "MO": 6137428, "MT": 1068778, "NE": 1934408, "NV": 3080156, "NH": 1359711, "NJ": 8882190, "NM": 2096829, "NY": 19453561, "NC": 10488084, "ND": 762062, "OH": 11689100, "OK": 3956971, "OR": 4217737, "PA": 12801989, "RI": 1059361, "SC": 5148714, "SD": 884659, "TN": 6829174, "TX": 28995881, "UT": 3205958, "VT": 623989, "VA": 8535519, "WA": 7614893, "WV": 1792147, "WI": 5822434, "WY": 578759}


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

    def get_negative(d):
        """
        Gets the number of negative tests for a given record from the covidtracking data
        """
        if 'negative' in d and d['negative'] is not None:
            return d['negative']
        else:
            return 0

    # Make predictions on the covidtracking data
    allstats = {}
    for R0 in [None, 1.5, 2, 2.5, 3, ]:
        for CFR in [None, 0.005, 0.01, 0.02, 0.03]:
            for norm_by_population in [False, True]:
                stats = {}
                for state in US_STATE_POPULATIONS.keys():
                    pop = US_STATE_POPULATIONS[state]
                    denom = pop/100000 if norm_by_population else 1

                    allrecords = [d for d in data if d['state'] == state]
                    allrecords = sorted(allrecords, key=lambda x: x['date'])

                    if get_positive(allrecords[-1]) > 0:
                        if 'death' in allrecords[-1] and allrecords[-1]['death'] is not None:
                            deaths = allrecords[-1]['death']
                        else:
                            deaths = 0
                        predictions = sorted(
                            sample_n_infected(deaths, R0=R0, CFR=CFR))
                        predictions = [p for p in predictions if p >=
                                       get_positive(allrecords[-1])]

                        if len(predictions) == 0:  # All simulations returned not enough cases
                            stats[state] = {
                                # 'sortorder': (-get_positive(allrecords[-1])/denom, -deaths/denom, state),
                                'positive': get_positive(allrecords[-1])/denom,
                                'negative': get_negative(allrecords[-1])/denom,
                                'deaths': deaths/denom
                            }
                        else:
                            print("{}: [{}, {}, {}, {}]".format(
                                state,
                                predictions[int(len(predictions)*0.025)],
                                predictions[int(len(predictions)*0.25)],
                                predictions[int(len(predictions)*0.75)],
                                predictions[int(len(predictions)*0.975)]))

                            stats[state] = {
                                # 'sortorder': (-get_positive(allrecords[-1])/denom, -deaths/denom, state),
                                'positive': get_positive(allrecords[-1])/denom,
                                'negative': get_negative(allrecords[-1])/denom,
                                'deaths': deaths/denom,
                                'lower95': predictions[int(len(predictions)*0.025)]/denom,
                                'lower90': predictions[int(len(predictions)*0.05)]/denom,
                                'lower50': predictions[int(len(predictions)*0.25)]/denom,
                                'median': predictions[int(len(predictions)*0.50)]/denom,
                                'upper50': predictions[int(len(predictions)*0.75)]/denom,
                                'upper90': predictions[int(len(predictions)*0.95)]/denom,
                                'upper95': predictions[int(len(predictions)*0.975)]/denom
                            }
                    else:
                        stats[state] = {
                            # 'sortorder': 0,
                            'positive': 0,
                            'negative': 0,
                        }
                if R0 is None and CFR is None:
                    stats_sorted = sorted(stats.items(), key=lambda x: -x[1].get('median', 0))
                else:
                    state_order = [x[0] for x in allstats["None,None,{}".format(norm_by_population)]]
                    stats_sorted = sorted(stats.items(), key=lambda x: state_order.index(x[0]))

                allstats["{},{},{}".format(R0, CFR, norm_by_population)] = stats_sorted

    # Update webpage
    dateint = max(d['date'] for d in data)
    datestr = "{}-{}-{}".format(str(dateint)
                                [:4], str(dateint)[4:6], str(dateint)[6:8])

    with open("index_template.md", "r") as f:
        template = f.read()

    with open("index.md", 'w') as f:
        f.write(template.replace("{{ stats }}", json.dumps(
            allstats)).replace("{{ date }}", datestr))
