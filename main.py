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

serial_interval = sp.stats.lognorm(s=0.5680, scale=math.exp(1.3868))
onset_to_death = sp.stats.gamma(4.726, 0, 1/(0.3151))

step = 1  # days

try:
    with open("sims.json", "r") as f:
        sims = {float(k1): {float(k2): v2 for k2, v2 in v1.items()}
                for k1, v1 in json.load(f).items()}
    print("loaded")
except FileNotFoundError:
    def sim_days(R0=2.5, CFR=0.02):
        print("simulating R0={} CFR={}".format(R0, CFR))
        max_days = 100
        n_timesteps = int(max_days / step)
        new_cases = np.zeros(n_timesteps, dtype=np.int)
        new_deaths = np.zeros(n_timesteps, dtype=np.int)
        new_cases[0] = 1

        for t1 in range(n_timesteps):
            interval_next = serial_interval.rvs(new_cases[t1])
            add_cases = np.round(np.random.choice(
                t1+interval_next/step,
                size=np.random.poisson(R0 * new_cases[t1])))
            interval_death = onset_to_death.rvs(new_cases[t1])
            add_deaths = np.round(np.random.choice(
                t1+interval_death/step,
                size=np.random.poisson(CFR * new_cases[t1])))
            for t2 in range(t1+1, n_timesteps):
                new_cases[t2] += (add_cases == t2).sum()
                new_deaths[t2] += (add_deaths == t2).sum()

            if np.sum(new_deaths[:t1]) > 100:
                break

        return (np.cumsum(new_cases[:t1]).tolist(),
                np.cumsum(new_deaths[:t1]).tolist())

    sims = {}
    for R0 in [1.5, 2, 2.5, 3]:
        sims[R0] = {}
        for CFR in [0.005, 0.01, 0.02, 0.03]:
            sims[R0][CFR] = [sim_days(R0, CFR) for _ in range(200)]
    with open("sims.json", "w") as f:
        json.dump(sims, f)
    print("saved.")


try:
    with open("data.json", "r") as f:
        data = json.load(f)
    print("loaded data")
except FileNotFoundError:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
    url = 'http://covidtracking.com/api/states/daily'

    req = Request(url=url, headers=headers)
    output = urlopen(req).read()
    data = json.loads(output.decode('utf-8'))
    with open("data.json", "w") as f:
        json.dump(data, f)
    print("saved data")


states = list(set([d['state'] for d in data]))


def sample_n_infected(n_deaths, R0=None, CFR=None):
    samples = []
    R0s = [1.5, 2, 2.5, 3] if R0 is None else [R0]
    CFRs = [0.005, 0.01, 0.02, 0.03] if CFR is None else [CFR]
    for R0 in R0s:
        for CFR in CFRs:
            for cases, deaths in sims[R0][CFR]:
                try:
                    samples.append(cases[
                        next(i for i, v in enumerate(deaths) if v >= n_deaths)
                    ])
                except StopIteration:
                    pass

    return samples


def get_positive(d):
    if 'positive' in d and d['positive'] is not None:
        return d['positive']
    else:
        return 0


allstats = {}
for R0 in [1.5, 2, 2.5, 3, None]:
    for CFR in [0.005, 0.01, 0.02, 0.03, None]:
        stats = {}
        for state in states:
            allrecords = [d for d in data if d['state'] == state]
            allrecords = sorted(allrecords, key=get_positive)
            records = [d for d in allrecords
                       if d.get('death', None) is not None
                       and d.get('death', None) != 0]

            if len(records) > 0:
                predictions = sorted(sample_n_infected(
                    records[-1]['death'], R0=R0, CFR=CFR))
                # predictions = [p for p in predictions if p>=get_positive(allrecords[-1])]

                print("{}: [{}, {}, {}, {}]".format(
                    state,
                    predictions[int(len(predictions)*0.025)],
                    predictions[int(len(predictions)*0.25)],
                    predictions[int(len(predictions)*0.75)],
                    predictions[int(len(predictions)*0.975)]))

                stats[state] = {
                    'positive': get_positive(allrecords[-1]),
                    'deaths': records[-1]['death'],
                    'lower95': predictions[int(len(predictions)*0.025)],
                    'lower50': predictions[int(len(predictions)*0.25)],
                    'median': predictions[int(len(predictions)*0.50)],
                    'upper50': predictions[int(len(predictions)*0.75)],
                    'upper95': predictions[int(len(predictions)*0.975)]
                }
            else:
                stats[state] = {
                    'positive': get_positive(allrecords[-1]),
                }
        stats_sorted = sorted(stats.items(), key=lambda x: (
            x[1]['positive'], x[0]), reverse=True)
        allstats["{},{}".format(R0, CFR)] = stats_sorted

dateint = max(x['date'] for x in allrecords)
datestr = "{}-{}-{}".format(str(dateint)
                            [:4], str(dateint)[4:6], str(dateint)[6:8])

with open("index_template.md", "r") as f:
    template = f.read()

with open("index.md", 'w') as f:
    f.write(template.replace("{{ stats }}", json.dumps(
        allstats)).replace("{{ date }}", datestr))
