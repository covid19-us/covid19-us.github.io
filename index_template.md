---
layout: default
---

Because tests for COVID-19 are lagging in the US, confirmed cases provide only a loose lower bound on the number of infected people. We use a model to estimate the total number of COVID-19 infections in each state, based on the number of deaths.

Data collected from [covidtracking.com](https://covidtracking.com/). Model inspired by [Jombart et al.](https://wwwmedrxiv.org/content/10.1101/2020.03.10.20033761v1.full.pdf) (details below).

<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

<div id="chart" style="width:800px;height:400px;display:inline-block;"></div>
<script type='text/javascript'>
    var stats = {{ stats }};

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

</script>