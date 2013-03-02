var fs   = require("fs");
function load_start_page () {
    var start_page;
    fs.readFile('./start.html', function (err, data) {
        console.log("reading file");
        if (err) {
            throw err;
        }
        exports.start_page = data;
        start_page = data;
        console.log(start_page);
    });
    console.log("start.html file read");
    console.log("contents:");
    console.log(start_page);
    return start_page;
}

console.log("foo");
var sp = load_start_page();
