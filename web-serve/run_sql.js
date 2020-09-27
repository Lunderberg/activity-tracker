NodeList.prototype.forEach = Array.prototype.forEach;
NodeList.prototype.map = Array.prototype.map;
NodeList.prototype.filter = Array.prototype.filter;

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

function read_activity_settings() {
    return document
        .getElementById('edit-activity-table')
        .querySelectorAll('tr')
        .filter( row => row.querySelector('th')===null )
        .map(
            row => ({name: row.querySelector('.edit-activity-name').value,
                     color: row.querySelector('.edit-activity-color').value,
                     display: !row.querySelector('.edit-activity-hide').checked,
                    })
        );
}


function main() {
    connect_callbacks();
    refresh_session();

    show_tab('edit-activities-tab');
    add_new_activity_row();
}

main();
