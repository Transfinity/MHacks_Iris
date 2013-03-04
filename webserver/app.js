/*
 * Module dependencies
 */
var express = require('express')
  , stylus = require('stylus')
  , nib = require('nib')


var app = express();

var mysql = require('mysql');
var client = mysql.createConnection({
    host     : 'iris.cbktya2t5svb.us-east-1.rds.amazonaws.com',
    user     : 'iris_webapp',
    password : 'redeagle',
    database : 'irisdb'
});

client.connect();


function compile(str, path) {
  return stylus(str)
    .set('filename', path)
    .use(nib());
}

app.set('views', __dirname + '/views')
app.set('view engine', 'jade')
app.use(express.logger('dev'))
app.use(stylus.middleware(
  { src: __dirname + '/public'
  , compile: compile
  }
))
app.use(express.static(__dirname + '/public'))

app.get('/', function (req, res) {
  res.render('index',
  { title : 'Home' , imagesrc : 'images/fastfood.gif', arr : ['red', 'blue', 'green']}
  )
})

app.get('/gallery', function(req, res) {
    console.log('Processing SQL query')
    client.query('SELECT * FROM Snapshots WHERE DATE_SUB(CURDATE(), INTERVAL 40 DAY) <= Date', function(err, rows, fields) {
        if (err) throw err;

        // Retrieve urls from the database query
        var urls = new Array();
        var text = new Array();
        for (i in rows) {
            urls[i] = rows[i].Filename;
            text[i] = rows[i].Text;
        }
        console.log('URL list:')
        console.log(urls)
        console.log('Text list:')
        console.log(text)

        res.render('gallery', {
            title : 'Recent Images',
            images: urls,
            descriptions: text
        });
    });
});


app.listen(80)
