var activity_log = [];
var categories = [{activity: 'home',
                   color: 'DarkGreen'},
                  {activity: 'work',
                   color: 'Tomato'},
                  {activity: 'travel',
                   color: 'DarkOrange'},
                  {activity: 'sleep',
                   color: 'DarkSlateBlue'},
                  {activity: 'errands',
                   color: 'Cyan'},
                 ];

NodeList.prototype.forEach = Array.prototype.forEach;

var color_map = {};
categories.forEach(function(cat) {
    color_map[cat.activity] = cat.color;
});

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
                var text = '';
                if(req.status === 200) {
                    load_history(req.responseText);
                } else {
                    text = 'Could not submit, please retry';
                }
                document.getElementById('result').innerHTML = text;
            };

            req.send('activity='+argument);
        }

        button.addEventListener('click', callback);
    });
}

function download_history() {
    var req = new XMLHttpRequest();
    var url = 'record.txt?_=' + new Date().getTime();
    req.open('GET', url, true);

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
    }).map(function(entry, i, arr) {
        var end_time = (i < arr.length-1) ? arr[i+1].time : new Date();
        var text = (format_time(entry.time) +
                    " - " +
                    format_time(end_time) +
                    ": " + entry.activity);
        return {time: entry.time,
                activity: entry.activity,
                end_time: end_time,
                text: text};
    });

    update_current_activity();
    update_plots();
    update_recent_activity_table();
}

function update_current_activity() {
    var span = document.getElementById('current-activity');
    var current = (activity_log.length===0
                   ? ''
                   : activity_log[activity_log.length-1].activity);
    span.innerHTML = current;
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

function format_span(span) {
    var hours = Math.floor(span/(60*60*1000));
    var minutes = Math.floor( (span%(60*60*1000)) / (60*1000) );
    var seconds = Math.floor( (span%(60*1000)) / 1000 );

    return ((hours===0 ? '' : hours+'h') +
            (minutes===0 ? '' : minutes+'m') +
            (seconds+'s'));
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

            if(date < entry.end_time) {
                var data_set = data_map[entry.activity];
                data_set.z[j][i] = 1;
                text[j][i] = entry.text;
            }
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

function summary_between(start_time, end_time) {
    var output = {};
    categories.forEach(function(cat) {
        output[cat.activity] = 0;
    });

    activity_log.filter(function(entry) {
        return (entry.end_time > start_time ||
                entry.start_time < end_time);
    }).forEach(function(entry,i,arr) {
        output[entry.activity] += (Math.min(end_time, entry.end_time) -
                                   Math.max(start_time, entry.time));
    });

    return output;
}

function update_recent_activity_table() {
    var now = activity_log[activity_log.length-1].end_time;

    var time_periods = [
        {desc: 'Last 24 Hours',
         time_diff_ms: 24*60*60*1000},
        {desc: 'Last 7 Days',
         time_diff_ms: 7*24*60*60*1000},
    ];

    var table_header = ('<tr>' +
                        '<th></th>' +
                        categories.map(function(cat) {
                            return '<th>' + cat.activity + '</th>';
                        }).join('') +
                        '</tr>');

    var table_rows = time_periods.map(function(period) {
        var start = new Date(now.getTime() - period.time_diff_ms);
        var summary = summary_between(start, now);

        return ('<tr>' +
                '<th>' + period.desc + '</th>' +
                categories.map(function(cat) {
                    return ('<td class=time-span-entry>' +
                            format_span(summary[cat.activity]) +
                            '</td>');
                }).join('') +
                '</tr>');
    }).join('');

    var table =  ('<table border="1">' +
                  table_header +
                  table_rows +
                  '</table>');

    document.getElementById('recent-activity-tables').innerHTML = table;
}

main();
