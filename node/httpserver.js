// Import the http module, make accessable via http
var http = require("http");
var url  = require("url");

function start() {
    function onRequest(request, response) {
        var pathname = url.parse(request.url).pathname;
        console.log("Handling request for " + pathname);
        response.writeHead(200, {"Content-Type": "text/plain"});
        response.write("Hello, World, from a notorious function");
        response.end();
    }

    http.createServer(onRequest).listen(8888);
    console.log("Server started");
}

exports.start = start;
