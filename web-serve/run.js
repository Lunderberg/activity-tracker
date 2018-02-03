var activity_log = [];
var categories = [{activity: 'home',
                   color: 'DarkGreen'},
                  {activity: 'work',
                   color: 'Tomato'},
                  {activity: 'travel',
                   color: 'DarkOrange'},
                  {activity: 'sleep',
                   color: 'DarkSlateBlue'},
                 ];

NodeList.prototype.forEach = Array.prototype.forEach;


function main() {
    generate_buttons();
    download_history();
}

function generate_buttons() {
    var div = document.getElementById('button-container');
    div.innerHTML = categories.map(function(cat) {
        return ('<button class=submit-activity ' +
                'id=submit-activity-ACT ' +
                'value="ACT">ACT</button>').replace(/ACT/g,cat.activity);
    }).join('');

    console.log(div.innerHTML);

    categories.forEach(function(cat) {
        var button = document.querySelector('#submit-activity-'+cat.activity);
        button.style.backgroundColor = cat.color;


        var argument = button.value;

        function callback() {
            var req = new XMLHttpRequest();
            req.open('POST', 'cgi-bin/record-value.py', true);

            req.setRequestHeader('Content-type',
                                 'application/x-www-form-urlencoded');

            req.onload = function() {
                if(req.status === 200) {
                    var text = req.responseText;
                } else {
                    var text = 'Could not submit, please retry';
                }
                document.getElementById('result').innerHTML = text
            };

            req.send('activity='+argument);
        }

        button.addEventListener('click', callback);
    });
}

function download_history() {
    var req = new XMLHttpRequest();
    req.open('GET', 'record.txt', true);

    req.onload = function() {
        if(req.status === 200) {
            load_history(req.responseText);
        }
        setTimeout(download_history, 600*1000);
    }

    req.send();
}

function load_history(text) {
    activity_log = text.split('\n').filter(function(line) {
        return line.indexOf('\t') !== -1;
    }).map(function(line) {
        var split = line.split('\t');
        return {time: new Date(split[0]),
                activity: split[1]};
    });

    generate_text();
    update_plots();
}

function generate_text() {
    activity_log.forEach(function(entry, i) {
        let start_time = entry.time;
        let end_time = (i<activity_log.length-1) ? activity_log[i+1].time : new Date();
        entry.text = (format_time(start_time) +
                      " - " +
                      format_time(end_time) +
                      ": " + entry.activity);
    });
}

function update_plots() {
    var n_days = 8;

    var now = new Date();
    var range_start = new Date(now);
    range_start.setDate(range_start.getDate() - n_days);

    plot_day_by_day('plot', range_start, now);
}

function format_time(time) {
    var hours = time.getHours();
    var minutes = time.getMinutes() + '';
    if(minutes.length == 1) {
        minutes = '0' + minutes;
    }
    return hours + ':' + minutes;
}

function plot_day_by_day(div, first_day, last_day) {
    first_day.setHours(0,0,0,0);
    last_day.setHours(0,0,0,0);

    var day_of_period = [];
    for(let date=new Date(first_day.getTime());
        date<=last_day;
        date.setDate(date.getDate()+1)) {

        day_of_period.push(new Date(date.getTime()));
    }

    var minute_of_day = Array(24*60).fill(null).map(function(_,i) {
        return i;
    });

    var text = minute_of_day.map(function() {
        return day_of_period.map(function() {
            return null;
        });
    });

    var data_map = {};
    var data = categories.map(function(cat,i) {
        var data_set = {type: 'heatmap',
                        x: day_of_period,
                        y: minute_of_day,
                        z: minute_of_day.map(function() {
                            return day_of_period.map(function() {
                                return null;
                            });
                        }),
                        colorscale: [[0, cat.color], [1, cat.color]],
                        title: cat.activity,
                        showscale: false,
                        hoverinfo: (i===0) ? 'text' : 'none',
                        text: text,
                       };
        data_map[cat.activity] = data_set;
        return data_set;
    });

    var i_entry = 0;
    let now = new Date();
    day_of_period.forEach(function(day,i) {
        let date = new Date(day.getTime());
        minute_of_day.forEach(function(minute, j) {
            date.setHours(0, minute);

            if(date > now) {
                return;
            }

            while(i_entry+1 < activity_log.length &&
                  activity_log[i_entry+1].time < date) {
                i_entry++;
            }
            var entry = activity_log[i_entry];
            var data_set = data_map[entry.activity];
            data_set.z[j][i] = 1;
            text[j][i] = entry.text;
        });
    });

    var layout = {
        yaxis: {tickvals: Array(9).fill(null).map(function(_,i) { return 3*60*i; }),
                ticktext: Array(9).fill(null).map(function(_,i) {
                    return (3*i) + ':00';
                }),
                range:[0,24*60],
               },
        width: 600,
    };

    Plotly.newPlot(div, data, layout);
}

main();
