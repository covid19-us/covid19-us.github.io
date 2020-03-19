---
layout: default
---

Because tests for COVID-19 are lagging in the US, confirmed cases provide only a loose lower bound on the number of infected people. This page uses a model to estimate the total number ofg infections in each state, based on the number of deaths. _Updates daily._

Data collected from [covidtracking.com](https://covidtracking.com/). Model inspired by Jombart et al. ([paper](https://www.medrxiv.org/content/10.1101/2020.03.10.20033761v1.full.pdf), [interactive](https://cmmid.github.io/visualisations/inferring-covid19-cases-from-deaths)). Source code is on [GitHub](https://github.com/covid19-us/covid19-us.github.io).

**WARNING: I am not an epidemiologist! Please do not use this model to make important decisions.**<br/>

<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

<script>
    var R0s = [1.5, 2, 2.5, 3];
    var CFRs = [0.005, 0.01, 0.02, 0.03];
</script>

<div style="text-align:center">
<!-- <input type="checkbox" id="chooseR0"> Reproduction Number (R<sub>0</sub>) <input type="range" min="0" max="3" value="1" id="R0" disabled> -->

<div id="chart" style="width:100%;height:22rem;display:inline-block;"></div><br/>

<div style="display:inline-block; padding-top:10px; padding-bottom:10px; text-align:left; padding-right:20px">
    <input type="checkbox" id="onlydeaths"/> <label for="onlydeaths">Hide states with no recorded deaths</label>
</div>
<div style="display:inline-block; padding-top:10px; padding-bottom:10px; text-align:left;">
    <input type="checkbox" id="chooseR0"> R<sub>0</sub> <input type="range" min="0" max="3" value="1" id="R0" disabled>
    <div id="R0text" style="width:80px; text-align:center; margin-right:20px; display:inline-block; background:lightgray; padding:3px;"></div>
</div>
<div style="display:inline-block; padding-top:10px; padding-bottom:10px; text-align:left;">
    <input type="checkbox" id="chooseCFR"> CFR <input type="range" min="0" max="3" value="1" id="CFR" disabled>
    <div id="CFRtext" style="width:80px; text-align:center; margin-right:20px; display:inline-block; background:lightgray; padding:3px;"></div>
</div>
<br/><i>(hover cursor over graph for numerical values)</i>
</div>

<script>
    document.getElementById("chooseR0").addEventListener('change', (event) => {
        document.getElementById("R0").disabled = !event.target.checked;
        refresh()
    })
    document.getElementById("R0").addEventListener('input', (event) => {refresh()})
    document.getElementById("chooseCFR").addEventListener('change', (event) => {
        document.getElementById("CFR").disabled = !event.target.checked;
        refresh()
    })
    document.getElementById("CFR").addEventListener('input', (event) => {refresh()})
    document.getElementById("onlydeaths").addEventListener('change', (event) => {refresh()})

    var allstats = {{ stats }};
    col = 'blue';
    function refresh(){
        if(document.getElementById("R0").disabled) {
            R0="None"
            document.getElementById("R0text").innerHTML="unknown"
        } else {
            R0=R0s[document.getElementById("R0").value];
            document.getElementById("R0text").innerHTML=R0
        }
        if(document.getElementById("CFR").disabled) {
            CFR="None"
            document.getElementById("CFRtext").innerHTML="unknown"
        } else {
            CFR=CFRs[document.getElementById("CFR").value];
            document.getElementById("CFRtext").innerHTML=CFR*100 + "%"
        }
        
        var stats = allstats[R0 + "," + CFR];
        if(document.getElementById("onlydeaths").checked) {
            _stats = []
            for(var i=0; i<stats.length; i++) {
                if(stats[i][1]['deaths']>0) {
                    _stats.push(stats[i])
                }
            }
            stats = _stats
        }
        console.log("R0=", R0, "CFR=", CFR)
        var data = [
            {
                name: 'Estimated cases',
                x: Array(stats.length).fill(1).map((v, j) => j+1),
                y: Array(stats.length).fill(1).map((v, j) => stats[j][1]['median']),
                marker: {
                    color: col,
                    opacity: 0
                },
                type: 'scatter',
                mode: 'markers',
            },
            {
                name: 'Confirmed cases',
                x: Array(stats.length).fill(1).map((v, j) => j+1),
                y: Array(stats.length).fill(1).map((v, j) => stats[j][1]['positive']),
                type: 'scatter',
                mode: 'markers',
            },
            {
                name: 'Deaths',
                x: Array(stats.length).fill(1).map((v, j) => j+1),
                y: Array(stats.length).fill(1).map((v, j) => stats[j][1]['deaths']),
                type: 'scatter',
                mode: 'markers',
            },
        ];
        shapes = []
        for(var j=0; j<stats.length; j++) {
            if(stats[j][1]['lower50'] != undefined) {
                shapes.push(
                    {layer:'below', type:'line', line:{width:3, color:col}, 
                    x0: j+1, x1: j+1, y0: stats[j][1]['lower50'], y1: stats[j][1]['upper50'] });
                shapes.push(
                    {layer:'below', type:'line', line:{width:1, color:col}, 
                    x0: j+1, x1: j+1, y0: stats[j][1]['lower95'], y1: stats[j][1]['upper95'] });
            }
        }
        layout = {
            hovermode: 'closest',
            title: 'Infections by state <i>({{ date }})</i>',
            xaxis: {
                tickvals: Array(stats.length).fill(1).map((v, j) => j+1),
                ticktext: Array(stats.length).fill(1).map((v, j) => stats[j][0]),
                range: [0, stats.length+1],
                showgrid: false,
                ticklen: 10,
                showline: true,
                showzero: false,
                fixedrange: true
            },
            margin: {t:50, l:50, r:0, b:50},
            yaxis: {
                type: 'log',
                range: [-0.1, 5.2],
                showgrid: false,
                showline: false,
                showzero: false,
                ticklen: 10,
                fixedrange: true
            },
            legend: {
                x: 1,
                xanchor: 'right',
                y: 1
            },
            shapes: shapes
        };
        Plotly.newPlot('chart', data, layout/*,  {staticPlot: true}*/);
    }

    document.getElementById("onlydeaths").checked = window.screen.width<1000;
    refresh();

</script>

## Model
To estimate the number of infections in a state, we run 500 stochastic simulations starting from a single infected individual, and stop each simulation when it reaches the number of deaths currently recorded in that state. Simulations are discarded if they predict fewer infections than the true number of confirmed cases.

Infections are simulated using a poisson branching process, where the serial interval (time for one individual to infect another) is drawn from a Log-Normal distribution (mean: 4.7 days, std: 2.9 days). The onset-to-death interval for each individual is drawn from a Gamma distribution (mean: 15 days, std: 6.9 days). When R<sub>0</sub> and CFR are not provided, we marginalise over possible values.

Contact: _lbh (at) mit (dot) edu_