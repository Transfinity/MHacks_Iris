var exec = require("child_process").exec,
    fs   = require("fs"),
    querystring = require("querystring"),
    formidable  = require("formidable"),
    start_page;

fs.readFile('./start.html', function (err, data) {
    if (err) {
        throw err;
    }
    start_page = data;
});
console.log("index file read");

function start(request, response) {
    console.log("Request handler 'start' was called.");
    response.writeHead(200, {"Content-Type": "text/html"});
    response.write(start_page);
    response.end();
}

function upload(request, response) {
    console.log("Request handler 'upload' was called.");

    var form = new formidable.IncomingForm();
    console.log("about to parse");

    form.parse(request, function(error, fields, files) {
        console.log("parsing done");

        fs.rename(files.upload.path, "/tmp/test.png", function(err) {
            if (err) {
                fs.unlink("/tmp/test.png");
                fs.rename(files.upload.path, "/tmp/test/png");
            }
        });

        response.writeHead(200, {"Content-Type": "text/html"});
        response.write("recieved image:<br/>");
        response.write("<img src='/show' />");
        response.end();
    });
}

function show(request, response) {
    console.log("Request handler 'show' was called.");
    fs.readFile("/tmp/test.png", "binary", function(error, image) {
        if (error) {
            response.writeHead(500, {"Content-Type": "text/plain"});
            response.write(err + "\n");
            response.end();
        } else {
            response.writeHead(200, {"Content-Type": "image/png"});
            response.write(image, "binary");
            response.end();
        }
    });
}

exports.start = start;
exports.upload = upload;
exports.show = show;
