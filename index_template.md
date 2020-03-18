---
layout: default
---

Because tests for COVID-19 are lagging in the US, confirmed cases provide only a loose lower bound on the number of infected people. This page uses a model to estimate the total number of COVID-19 infections in each state, based on the number of deaths.

Data collected from [covidtracking.com](https://covidtracking.com/). Model inspired by [Jombart et al.](https://www.medrxiv.org/content/10.1101/2020.03.10.20033761v1.full.pdf) (details below).

<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

<script>
    var R0s = [1.5, 2, 2.5, 3];
    var CFRs = [0.005, 0.01, 0.02, 0.03];
</script>

<div style="text-align:center">
<div id="chart" style="width:800px;height:400px;display:inline-block;"></div><br/>

<input type="checkbox" id="chooseR0" checked> Reproduction Number (R<sub>0</sub>) <input type="range" min="0" max="3" value="1" id="R0">
<div id="R0text" style="width:90px; text-align:center; margin-right:20px; display:inline-block; background:lightgray; padding:3px;">None</div>
<input type="checkbox" id="chooseCFR" checked> Case Fatality Ratio (CFR) <input type="range" min="0" max="3" value="1" id="CFR">
<div id="CFRtext" style="width:90px; text-align:center; margin-right:20px; display:inline-block; background:lightgray; padding:3px;"></div>

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

    var allstats = {{ stats }};
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
        console.log("R0=", R0, "CFR=", CFR)
        var data = [
            {
                name: 'Cases estimated from deaths',
                x: Array(stats.length).fill(1).map((v, j) => j+1),
                y: Array(stats.length).fill(1).map((v, j) => stats[j][1]['median']),
                marker: {
                    color: 'blue',
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
                    {layer:'below', type:'line', line:{width:3, color:'blue'}, 
                    x0: j+1, x1: j+1, y0: stats[j][1]['lower50'], y1: stats[j][1]['upper50'] });
                shapes.push(
                    {layer:'below', type:'line', line:{width:1, color:'blue'}, 
                    x0: j+1, x1: j+1, y0: stats[j][1]['lower95'], y1: stats[j][1]['upper95'] });
            }
        }
        layout = {
            hovermode: 'closest',
            title: 'Estimated cases by US state <i>(updated {{ date }})</i>',
            xaxis: {
                tickvals: Array(stats.length).fill(1).map((v, j) => j+1),
                ticktext: Array(stats.length).fill(1).map((v, j) => stats[j][0]),
                range: [0, stats.length+1],
                showgrid: false,
                ticklen: 10,
                showline: true,
                showzero: false
            },
            margin: {t:50, l:50, r:0, b:50},
            yaxis: {
                type: 'log',
                range: [-0.1, 5.2],
                showgrid: false,
                showline: false,
                showzero: false,
                ticklen: 10,
            },
            legend: {
                x: 1,
                xanchor: 'right',
                y: 1
            },
            shapes: shapes
        };
        Plotly.newPlot('chart', data, layout);
    }
    refresh();
    

</script>

## Model
To estimate the number of infections in a state, we run 200 stochastic simulations starting from a single infected individual, and stop each simulation when it reaches the number of deaths currently recorded in that state.

Infections are simulated using a poisson branching process, where the serial interval (time for one individual to infect another) is drawn from a Log-Normal distribution (mean: 4.7 days, std: 2.9 days). The onset-to-death interval for each individual is drawn from a Gamma distribution (mean: 15 days, std: 6.9 days). When R<sub>0</sub> and CFR and not provided above, we marginalise over possible values.