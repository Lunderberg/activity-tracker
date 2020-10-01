NodeList.prototype.forEach = Array.prototype.forEach;
NodeList.prototype.map = Array.prototype.map;
NodeList.prototype.filter = Array.prototype.filter;

// From https://stackoverflow.com/a/10865042/2689797
Array.prototype.flatten = function() {
    return [].concat.apply([], this);
};

// From https://codereview.stackexchange.com/a/37132/44749
Array.prototype.groupBy = function(f) {
    var groups = {};
    this.forEach(function(obj) {
        var group = JSON.stringify( f(obj) );
        groups[group] = groups[group] || [];
        groups[group].push(obj);
    });
    return Object.keys(groups).map(function(group) {
        return groups[group];
    });
};

function connect_callbacks() {
    document
        .getElementById('button-login')
        .addEventListener('click', log_in);

    document
        .getElementById('button-logout')
        .addEventListener('click', log_out);

    document
        .getElementById('button-main-tab')
        .addEventListener('click', () => show_tab('activity-info-tab'));

    document
        .getElementById('button-edit-activities-tab')
        .addEventListener('click', () => show_tab('edit-activities-tab'));

    document
        .getElementById('button-edit-data-tab')
        .addEventListener('click', () => show_tab('edit-data-tab'));

    document
        .getElementById('add-new-activity-row')
        .addEventListener('click', add_new_activity_row);

    document
        .getElementById('submit-activity-settings')
        .addEventListener('click', submit_activity_settings);
}

// From https://stackoverflow.com/a/1714899/2689797
function encode_query_string(obj) {
    var params = [];
    for(var p in obj) {
        if(obj.hasOwnProperty(p)) {
            params.push(encodeURIComponent(p) +
                        '=' +
                        encodeURIComponent(obj[p]));
        }
    }
    return params.join('&');
}

function show_class(selector) {
    document
        .querySelectorAll(selector)
        .forEach( node => node.classList.remove('hidden') )
    ;
}

function hide_class(selector) {
    document
        .querySelectorAll(selector)
        .forEach( node => node.classList.add('hidden') )
    ;
}

function log_in() {
    var params = {'username': document.getElementById('username').value,
                  'password': document.getElementById('password').value};

    document.getElementById('password').value = '';

    var req = new XMLHttpRequest();

    function on_results() {
        var success = false;

        if((req.status >= 200) && (req.status < 300)) {
            var params = JSON.parse(req.response);
            if(params['session_id'] !== null) {
                show_activity_info();
                success = true;
            }
        }

        if(!success) {
            var span = document.getElementById('span-login-failed');
            span.classList.remove('fade-out');
            window.setTimeout( () => span.classList.add('fade-out'), 0 );
        }
    }

    req.addEventListener('load', on_results);
    req.open('POST', '/log_in');
    req.send(JSON.stringify(params));
}

function refresh_session() {
    var req = new XMLHttpRequest();

    function on_results() {
        if((req.status >= 200) && (req.status < 300)) {
            show_activity_info();
        }
    }

    req.addEventListener('load', on_results);
    req.open('GET', '/refresh');
    req.send();
}

function log_out() {
    var req = new XMLHttpRequest();

    function on_results() {
        if((req.status >= 200) && (req.status < 300)) {
            hide_activity_info();
        }
    }

    req.addEventListener('load', on_results);
    req.open('POST', '/log_out');
    req.send();
}

function show_activity_info() {
    show_class('.verified-login');
    hide_class('.unverified-login');
}

function hide_activity_info() {
    hide_class('.verified-login');
    show_class('.unverified-login');
}

function show_tab(div_id) {
    hide_class('.tab');
    show_class('#' + div_id);
}

function add_new_activity_row() {
    var new_row = `
        <td><button class='close-button'>&times;</button></td>
        <td><input class='edit-activity-name' type='text' value="Activity Name"></td>
        <td><input class='edit-activity-color' type='color'></td>
        <td><input class='edit-activity-hide' type='checkbox'></td>
        `;
    var table = document.getElementById('edit-activity-table');
    var row = table.insertRow(-1);
    row.innerHTML = new_row;

    row
        .querySelector('.close-button')
        .addEventListener('click', function() {
            this.parentElement.parentElement.outerHTML = '';
        });
}


// From https://stackoverflow.com/a/47355187/2689797
function standardize_color(str){
    var ctx = document.createElement('canvas').getContext('2d');
    ctx.fillStyle = str;
    return ctx.fillStyle;
}

function init_activity_display() {
    var table = document.getElementById('edit-activity-table');

    cache.activities.forEach( (row) => {
        var color = standardize_color(row.activity_color);

        var new_row = table.insertRow(-1);
        new_row.innerHTML = [
            "<td></td>",
            "<td>",
            `<input class='edit-activity-name' type='text' value="${row.activity_name}">`,
            "</td>",

            "<td>",
            `<input class='edit-activity-color' type='color' value="${color}">`,
            "</td>",

            "<td>",
            "<input class='edit-activity-hide' type='checkbox' ",
            (row.display ? '' : 'checked'),
            ">",
            "</td>",
        ].join('');
    });
}

function read_activity_settings() {
    return document
        .getElementById('edit-activity-table')
        .querySelectorAll('tr')
        .filter( row => row.querySelector('th')===null )
        .map(
            (row,i) => ({
                activity_id: i,
                activity_name: row.querySelector('.edit-activity-name').value,
                activity_color: row.querySelector('.edit-activity-color').value,
                display: !row.querySelector('.edit-activity-hide').checked,
            })
        );
}

function submit_activity_settings() {
    var params = read_activity_settings();
    var status_div = document.getElementById('activity-update-status');

    var req = new XMLHttpRequest();

    function on_results() {
        if((req.status >= 200) && (req.status < 300)) {
            status_div.innerHTML = 'Update success.';
            cache.activities = params;
        } else {
            status_div.innerHTML = 'Update failed, ' + req.status + '.';
        }
    }

    status_div.innerHTML = 'Sending update.'

    req.addEventListener('load', on_results);
    req.open('POST', '/update_settings');
    req.send(JSON.stringify(params));
}


function generate_buttons() {
    var div = document.getElementById('button-container');

    var displayed_activities = cache.activities.filter( act => act.display );

    div.innerHTML = displayed_activities
        .map(function(act) {
            return ['<button class=submit-activity ',
                    'id=submit-activity-', act.activity_id,
                    ' ',
                    'value="', act.activity_id, '"',
                    '>',
                    act.activity_name,
                    '</button>',
                   ].join('');
        })
        .join('')
    ;

    displayed_activities.forEach(function(act) {
        var button = document.querySelector('#submit-activity-'+act.activity_id);
        button.style.backgroundColor = act.activity_color;

        var argument = button.value;

        // function callback() {
        //     var req = new XMLHttpRequest();
        //     req.open('POST', 'cgi-bin/record-value.py', true);

        //     req.setRequestHeader('Content-type',
        //                          'application/x-www-form-urlencoded');

        //     req.onload = function() {
        //         var text = '';
        //         if(req.status === 200) {
        //             load_history(req.responseText);
        //         } else {
        //             text = 'Could not submit, please retry';
        //         }
        //         document.getElementById('result').innerHTML = text;
        //     };

        //     req.send('activity='+argument);
        // }

        // button.addEventListener('click', callback);
    });
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

function load_history() {
    update_cache_log_details();

    update_current_activity();
    update_weekly_view();
    update_recent_activity_table();
    // update_daily_chart();
}

function update_cache_log_details() {
    var activity_map = {}
    cache.activities.forEach(function(a) {
        activity_map[a.activity_id] = {name: a.activity_name,
                                       color: a.activity_color};
    });

    // Add extra info to the logs, for ease of use later.
    cache.logs = cache.logs
        .map(function(entry, i, arr) {
            var id = entry.activity_id;
            var activity_name = activity_map[id].name;
            var activity_color = activity_map[id].color;

            var txn_date = new Date(entry.txn_date);
            if (i < arr.length-1) {
                var end_time = new Date(arr[i+1].txn_date);
            } else {
                var end_time = new Date();
            }

            var text = (format_time(txn_date) +
                        " - " +
                        format_time(end_time) +
                        ": " + name);

            return {txn_date: txn_date,
                    end_time: end_time,
                    activity_id: id,
                    activity_name: activity_name,
                    activity_color: activity_color,
                    text: text,
                   };
        });
}

function update_current_activity() {
    var span = document.getElementById('current-activity');
    var current = (cache.logs.length===0
                   ? ''
                   : cache.logs[cache.logs.length-1].activity_name);
    span.innerHTML = current;
}

function update_weekly_view() {
    var n_days = 7;

    var now = new Date();
    var range_start = new Date(now);
    range_start.setDate(range_start.getDate() - n_days);

    plot_weekly_view('weekly-view', range_start, now);
}

function plot_weekly_view(div, first_day, last_day) {
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
    var data = cache.activities.map(function(act,i) {
        var data_set = {type: 'heatmap',
                        x: day_of_period,
                        y: minute_of_day,
                        z: minute_of_day.map(function() {
                            return day_of_period.map(function() {
                                return null;
                            });
                        }),
                        colorscale: [[0, act.activity_color],
                                     [1, act.activity_color]],
                        title: act.activity_name,
                        showscale: false,
                        hoverinfo: (i===0) ? 'text' : 'none',
                        text: text,
                       };
        data_map[act.activity_name] = data_set;
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

            while(i_entry+1 < cache.logs.length &&
                  cache.logs[i_entry+1].txn_date < date) {
                i_entry++;
            }
            var entry = cache.logs[i_entry];

            if(date < entry.end_time) {
                var data_set = data_map[entry.activity_name];
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

function update_recent_activity_table() {
    var activity_map = {}
    cache.activities.forEach(function(a) {
        activity_map[a.activity_id] = {name: a.activity_name,
                                       color: a.activity_color};
    });

    var displayed_activities = cache.activities.filter(a => a.display);

    var table_header = ('<tr>' +
                        '<th></th>' +
                        displayed_activities.map(function(a) {
                            return '<th>' + a.activity_name + '</th>';
                        }).join('') +
                        '</tr>');

    var table_rows = cache.summary
        .groupBy(row => row.summary_window)
        .map(function(rows) {
            var summary_window = rows[0].summary_window;

            return ('<tr>' +
                    '<th>' + summary_window + '</th>' +
                    displayed_activities
                    .map(function(a) {
                        var activity_rows = rows.filter(row => a.activity_id == row.activity_id);
                        if(activity_rows.length==1) {
                            var desc = activity_rows[0].time_spent;
                        } else {
                            var desc = '';
                        }
                        return ('<td class=time-span-entry>' +
                                desc +
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

function main() {
    connect_callbacks();

    if(cache.signed_in) {
        // TODO: Group these into behavior to be done on login, not
        // just on page load.
        show_activity_info();
        generate_buttons();
        init_activity_display();

        load_history();
    }
}

main();