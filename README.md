# covid19-us.github.io

See webpage: http://covid19-us.github.io

This model estimates the total number of COVID-19 infections in each US state, based on the number of deaths (as reported on covidtracking.com). The simulation model is the same as [Jombart et al.](https://www.medrxiv.org/content/10.1101/2020.03.10.20033761v1.full.pdf), but for prediction we use a different strategy. 

Whereas Jombart et al. estimates the date-of-infection for each death separately (sampling backwards from the date of death using the onset-to-death distribution), we run 500 stochastic simulations starting from a single infected individual, and stop each simulation when it reaches the number of deaths currently recorded in that state.

Infections are simulated using a poisson branching process, where the serial interval (time for one individual to infect another) is drawn from a Log-Normal distribution (mean: 4.7 days, std: 2.9 days). The onset-to-death interval for each individual is drawn from a Gamma distribution (mean: 15 days, std: 6.9 days). When R0 and CFR are not provided, we marginalise over possible values.
