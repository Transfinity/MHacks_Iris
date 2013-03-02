// Import the http module, make accessable via http
var http = require("http"),
    url  = require("url");

function start(route, handle) {
    function onRequest(request, response) {
        var postData = "";
        var pathname = url.parse(request.url).pathname;
        console.log("Handling request for " + pathname);
        route(handle, pathname, request, response);
    }

    http.createServer(onRequest).listen(8888);
    console.log("Server started");
}

exports.start = start;
