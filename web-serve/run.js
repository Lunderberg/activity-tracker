NodeList.prototype.forEach = Array.prototype.forEach;

function main() {
    document.querySelectorAll('.submit-activity').forEach(function(button) {
        var argument = button.innerHTML;
        function callback() {
            var req = new XMLHttpRequest();
            req.open('POST', 'cgi-bin/record-value.py', true);

            req.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');

            req.onload = function() {
                if(req.status == 200) {
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

main();
