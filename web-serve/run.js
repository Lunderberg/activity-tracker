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
    connect_callbacks();
    set_button_colors();
    download_history();
}

function connect_callbacks() {
    document.querySelectorAll('.submit-activity').forEach(function(button) {
        var argument = button.innerHTML;
        function callback() {
            var req = new XMLHttpRequest();
            req.open('POST', 'cgi-bin/record-value.py', true);

            req.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');

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

function set_button_colors() {
    document.querySelectorAll('.submit-activity').forEach(function(button) {
        let color = categories.filter(function(cat) {
            return cat.activity === button.innerHTML;
        })[0].color;
        if(color !== null) {
            button.style.backgroundColor = color;
        }
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

    update_plots();
}

function update_plots() {
    var n_days = 8;

    var now = new Date();
    var range_start = new Date(now);
    range_start.setDate(range_start.getDate() - n_days);

    var last_week = plot_day_by_day(range_start, now);
    Plotly.newPlot('plot', last_week);
}

function plot_day_by_day(first_day, last_day) {
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

    var data_map = {};
    var data = categories.map(function(cat) {
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
                       };
        data_map[cat.activity] = data_set;
        return data_set;
    });

    activity_log.forEach(function(entry, i) {
        let data_set = data_map[entry.activity];
        let start_time = entry.time;
        let end_time = (i<activity_log.length-1) ? activity_log[i+1].time : new Date();
        day_of_period.forEach(function(day,i) {
            minute_of_day.forEach(function(minute, j) {
                let date = new Date(day.getTime());
                date.setMinutes(minute);
                if(start_time <= date && date < end_time) {
                    data_set.z[j][i] = 1;
                }
            });
        });
    });


    return data;
}

main();
