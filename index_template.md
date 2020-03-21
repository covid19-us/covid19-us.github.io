---
layout: default
---

Because tests for COVID-19 are lagging in the US, confirmed cases provide only a loose lower bound on the number of infected people. This page estimates the total number of infections in each state, based on the number of deaths. _Updates every two hours._

The model is inspired by the paper _Inferring the number of COVID-19 cases from recently reported deaths_ ([Jombart et al.](https://www.medrxiv.org/content/10.1101/2020.03.10.20033761v1.full.pdf), [interactive](https://cmmid.github.io/visualisations/inferring-covid19-cases-from-deaths)) which estimates that, by the time a death occurs,
roughly "hundreds to thousands" of cases are likely to be present in a population.

Data from [covidtracking.com](https://covidtracking.com/). Source code is on [GitHub](https://github.com/covid19-us/covid19-us.github.io). Best viewed on desktop.

<div style="text-align:center; font-weight: bold; padding-bottom:15px">
WARNING: I am not an epidemiologist, please do not use this model to make precise predictions!
</div>

<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style type="text/css">
.stat {
    font-weight: bold;
}
</style>
<script>
    var R0s = [1.5, 2, 2.5, 3];
    var CFRs = [0.005, 0.01, 0.02, 0.03];
    var regions = {
        west: ["WA", "OR", "MT", "ID", "WY", "NV", "UT", "CO", "CA", "AZ", "NM"],
        midwest: ["ND", "MN", "SD", "IA", "NE", "KS", "MO", "WI", "IL", "IN", "MI", "OH"],
        south: ["TX", "OK", "AR", "LA", "MS", "TN", "KY", "AL", "FL", "GA", "SC", "NC", "VA", "WV", "DC", "MD", "DE"],
        northeast: ["PA", "NJ", "NY", "CT", "RI", "MA", "VT", "NH", "ME"]
    }
</script>


<div style="text-align:center">
<!-- <input type="checkbox" id="chooseR0"> Reproduction Number (R<sub>0</sub>) <input type="range" min="0" max="3" value="1" id="R0" disabled> -->

<div id="chart" style="width:100%;max-width:600px;height:22rem;display:inline-block;"></div><br/>

<!-- <div style="display:inline-block; padding-top:10px; padding-bottom:10px; text-align:left; padding-right:20px">
    <input type="checkbox" id="onlydeaths"/> <label for="onlydeaths">Hide states with no deaths</label>
</div> -->
<div style="display:inline-block; padding-top:10px; padding-bottom:10px; text-align:left; padding-right:20px">
    Filter states: 
    <select id="region">
    <option value="all">All states</option>
    <option value="most" selected>Most affected</option>
    <option value="midwest">Midwest</option>
    <option value="northeast">Northeast</option>
    <option value="south">South</option>
    <option value="west">West</option>
    </select>
</div>
<div style="display:inline-block; padding-top:10px; padding-bottom:10px; text-align:left; padding-right:20px">
    <input type="checkbox" id="normbypopulation" /> <label for="normbypopulation">Scale by population</label>
</div>
<div style="display:inline-block; padding-top:10px; padding-bottom:10px; text-align:left; padding-right:20px">
    <input type="checkbox" id="logscale" checked/> <label for="logscale">Log scale</label>
</div><br/>
<div style="display:inline-block; padding-top:10px; padding-bottom:10px; text-align:left;">
    <input type="checkbox" id="chooseR0"> <label for="chooseR0">R<sub>0</sub></label> <input type="range" min="0" max="3" value="1" id="R0" style="width:80px" disabled>
    <div id="R0text" style="width:80px; text-align:center; margin-right:20px; display:inline-block; background:lightgray; padding:3px;"></div>
</div>
<div style="display:inline-block; padding-top:10px; padding-bottom:10px; text-align:left;">
    <input type="checkbox" id="chooseCFR"> <label for="chooseCFR">CFR</label> <input type="range" min="0" max="3" value="1" id="CFR" style="width:80px" disabled>
    <div id="CFRtext" style="width:80px; text-align:center; margin-right:20px; display:inline-block; background:lightgray; padding:3px;"></div>
</div>
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
    // document.getElementById("onlydeaths").addEventListener('change', (event) => {refresh()})
    document.getElementById("region").addEventListener('change', (event) => {refresh()})
    document.getElementById("normbypopulation").addEventListener('change', (event) => {refresh()})
    document.getElementById("logscale").addEventListener('change', (event) => {refresh()})

    var allstats = {{ stats }};
    col = '#1f77b4';
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
        normbypopulation = document.getElementById("normbypopulation").checked
        logscale = document.getElementById("logscale").checked

        var stats = allstats[R0 + "," + CFR + "," + (normbypopulation ? "True" : "False")];
        region = document.getElementById("region").value;
        if(region == "all") {
            
        } else if(region=="most") {
            stats = stats.slice(0, 15)
        } else {
            _stats = []
            for(var i=0; i<stats.length; i++) {
                if(regions[region].indexOf(stats[i][0])!=-1) {
                    _stats.push(stats[i])
                }
            }
            stats = _stats
        }
        // if(document.getElementById("onlydeaths").checked) {
        //     _stats = []
        //     for(var i=0; i<stats.length; i++) {
        //         if(stats[i][1]['deaths']>0) {
        //             _stats.push(stats[i])
        //         }
        //     }
        //     stats = _stats
        // }
        
        console.log("R0=", R0, "CFR=", CFR, "normbypopulation=", normbypopulation)
        var data = [
            {
                name: 'Estimated cases',
                x: Array(stats.length).fill(1).map((v, j) => j+1),
                y: Array(stats.length).fill(1).map((v, j) => stats[j][1]['median']),
                hoverinfo:'text',
                text: Array(stats.length).fill(1).map((v, j) => stats[j][0] + "<br>" + (
                    (stats[j][1]['lower50'] > 1000 ?
                        (parseFloat((stats[j][1]['lower50']).toPrecision(2))/1000 + "k-" + parseFloat((stats[j][1]['upper50']).toPrecision(2))/1000 + "k") :
                        (parseFloat((stats[j][1]['lower50']).toPrecision(2)) + "-" + parseFloat((stats[j][1]['upper50']).toPrecision(2)) + "")
                    ) + " (50%)<br>" + 
                    (stats[j][1]['lower95'] > 1000 ?
                        (parseFloat((stats[j][1]['lower95']).toPrecision(2))/1000 + "k-" + parseFloat((stats[j][1]['upper95']).toPrecision(2))/1000 + "k") :
                        (parseFloat((stats[j][1]['lower95']).toPrecision(2)) + "-" + parseFloat((stats[j][1]['upper95']).toPrecision(2)) + "")
                    ) + " (95%)"
                )),
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
                    {layer:'below', type:'line', line:{width:1, color:col, opacity:0.3}, 
                    x0: j+1, x1: j+1, y0: stats[j][1]['lower95'], y1: stats[j][1]['upper95'] });
            }
        }
        layout = {
            hovermode: 'closest',
            title: 'COVID-19 by state <i>(updated {{ date }})</i>',
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
            margin: {t:50, l:40, r:0, b:50},
            yaxis: {
                // type: 'log',
                showgrid: false,
                showline: false,
                showzero: false,
                ticklen: 10,
                fixedrange: true, 
                // range: [...],
                // hoverformat: '.2s',
                // tickformat: 's',
            },
            legend: {
                x: 1,
                xanchor: 'right',
                y: 1,
                bordercolor: 'black',
                borderwidth: 1
            },
            shapes: shapes
        };
        if(normbypopulation) {
            layout.yaxis.title = "Cases per 100,000 people";
            layout.margin.l += 40;
            layout.yaxis.titlefont = {size:'0.8em'};
            if(logscale) {
                layout.yaxis.type = "log";
                layout.yaxis.range = [-2.5, 4.5];
                layout.yaxis.hoverformat = '.2r';
                layout.yaxis.tickformat = '.1r';
                layout.yaxis.title += " (Log scale)"
            } else {
                // layout.yaxis.range = [0, 30];
                // layout.yaxis.range = [0, 1e4];
                layout.yaxis.range = [0, stats[1][1]['upper50']*1.1];
                layout.yaxis.hoverformat = '.2r';
                layout.yaxis.tickformat = '.1r';
            }
            
        } else {
            layout.yaxis.title = "Cases";
            layout.margin.l += 40;
            if(logscale) {
                layout.yaxis.type = "log";
                layout.yaxis.range = [-0.2, 6.5];
                layout.yaxis.hoverformat = '.2s';
                layout.yaxis.tickformat = 's';
                layout.yaxis.title += " (Log scale)"
            } else {
                // layout.yaxis.range = [0, 5005];
                // layout.yaxis.range = [0, 1e5];
                layout.yaxis.range = [0, stats[1][1]['upper50']*1.1];
                layout.yaxis.hoverformat = 'd';
                layout.yaxis.tickformat = 'd';
            }

            
        }

        Plotly.newPlot('chart', data, layout/*,  {staticPlot: true}*/);
    }

    // if(window.screen.width<1000) {
        // document.getElementById("onlydeaths").checked = true
        // document.getElementById("region").value = "west";
    // }
    
    refresh();

</script>
<div style="padding-top:15px; padding-bottom:15px;">
<i>You can hover or click any point on the graph above to see its value (confidence interval for estimates)</i>
</div>

The model is fairly sensitive to the choice of CFR (_Case Fataility Rate_: the proportion of cases which are fatal) and R<sub>0</sub> (_Reproduction Number_: the average number of people each person infects):
- When the CFR is high, we expect _fewer_ infections by the time of the first death (because deaths are more frequent)
- When the R<sub>0</sub> is high, we expect _more_ infections by the time of the first death (because the virus spreads more quickly)

By default, if R<sub>0</sub> and CFR are not provided, we marginalise over all values to avoid making predictions which are over-confident. 

## Estimation from confirmed cases vs. deaths
<p>
This chart highlights the large difference between using <i>confirmed cases</i> vs. <i>deaths</i> to estimate the prevalence of COVID-19 in a state.
</p>

<p>For example, Louisiana (population ~5 million) has so far suffered <span id="louisianadeaths" class="stat"></span> deaths with only <span id="louisianacases" class="stat"></span> confirmed cases (total tested: <span id="louisianatotal" class="stat"></span>).<br/> By comparison, New York state (population ~20 million) has suffered <span id="newyorkdeaths" class="stat"></span> deaths with <span id="newyorkcases" class="stat"></span> confirmed cases (total tested: <span id="newyorktotal" class="stat"></span>).
</p>

<p>Comparing only the number of confirmed cases, it would be easy to assume that the prevalence of COVID-19 is
<span id="newyorklouisianafraction"></span>x
larger in New York than in Louisiana. However, when estimated by fatailities, this model suggests that the prevalence could well be similar in these states, with an estimate of roughly <span id="louisianapopulationlower" class="stat"></span>-<span id="louisianapopulationupper" class="stat"></span> cases per 100,000 people in Louisiana, and  <span id="newyorkpopulationlower" class="stat"></span>-<span id="newyorkpopulationupper" class="stat"></span> cases per 100,000 people in New York.
</p>

<script>
    var stats = allstats["None,None,False"];
    var stats_by_state = {};
    for(var i=0; i<stats.length; i++) {
        stats_by_state[stats[i][0]] = stats[i][1];
    }
    var stats_population = allstats["None,None,True"];
    var stats_population_by_state = {};
    for(var i=0; i<stats_population.length; i++) {
        stats_population_by_state[stats_population[i][0]] = stats_population[i][1];
    }
    document.getElementById("louisianacases").innerHTML=stats_by_state["LA"]["positive"];
    document.getElementById("louisianadeaths").innerHTML=stats_by_state["LA"]["deaths"];
    document.getElementById("louisianatotal").innerHTML=stats_by_state["LA"]["positive"] + stats_by_state["LA"]["negative"];
    document.getElementById("newyorkcases").innerHTML=stats_by_state["NY"]["positive"];
    document.getElementById("newyorkdeaths").innerHTML=stats_by_state["NY"]["deaths"];
    document.getElementById("newyorktotal").innerHTML=stats_by_state["NY"]["positive"] + stats_by_state["NY"]["negative"];

    document.getElementById("newyorklouisianafraction").innerHTML=Math.round(stats_population_by_state["NY"]["positive"]/stats_population_by_state["LA"]["positive"]);

    document.getElementById("louisianapopulationlower").innerHTML=parseFloat((stats_population_by_state["LA"]["lower50"]).toPrecision(2));
    document.getElementById("louisianapopulationupper").innerHTML=parseFloat((stats_population_by_state["LA"]["upper50"]).toPrecision(2));
    document.getElementById("newyorkpopulationlower").innerHTML=parseFloat((stats_population_by_state["NY"]["lower50"]).toPrecision(2));
    document.getElementById("newyorkpopulationupper").innerHTML=parseFloat((stats_population_by_state["NY"]["upper50"]).toPrecision(2));
    
</script>

## Model
To estimate the number of infections in a state, we run 500 stochastic simulations starting from a single infected individual, and stop each simulation when it reaches the number of deaths currently recorded in that state. Simulations are discarded if they predict fewer infections than the number of confirmed cases.

Infections are simulated using a poisson branching process, where the serial interval (time for one individual to infect another) is drawn from a Log-Normal distribution (mean: 4.7 days, std: 2.9 days). The onset-to-death interval for each individual is drawn from a Gamma distribution (mean: 15 days, std: 6.9 days).

_Note, this model differs from Jombart et al. in two ways: (1) whereas Jombart et al. sample backwards from each death, using the onset-to-death distribution to estimate when an individual was infected, this model simulates forwards from a single infection. The specific date of each death is ***ignored***, and instead each simulation runs until it reaches the total number of observed deaths (or is discarded if it does not). (2) Unlike Jombart et al., this model incorporates testing information by discarding simulations which do not reach the total number of confirmed cases. This significantly increases the estimated prevalence in states with a large number of confirmed cases._

Contact: _lbh (at) mit (dot) edu_