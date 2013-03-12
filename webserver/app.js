/*
 * Module dependencies
 */
var express = require('express')
  , stylus = require('stylus')
  , nib = require('nib')


var app = express();
app.listen(80)

var mysql = require('mysql');
var client = mysql.createConnection({
    host     : 'iris.cbktya2t5svb.us-east-1.rds.amazonaws.com',
    user     : 'iris_webapp',
    password : 'redeagle',
    database : 'irisdb'
});

client.connect();

var topbar_links = [
{title: 'Home', link: '/'}, 
{title: 'About', link: '/about'}, 
{title: 'Gallery', link: '/gallery'}
]

function compile(str, path) {
    return stylus(str)
      .set('filename', path)
      .use(nib());
}

//Set up our views with jade
app.set('views', __dirname + '/views')
app.set('view engine', 'jade')
app.use(express.logger('dev'))
app.use(stylus.middleware(
  { src: __dirname + '/public'
  , compile: compile
  }
))
app.use(express.static(__dirname + '/public'))

//Route for the home page
app.get('/', function (req, res) {
  res.render('index',
  { title : 'Home' , topbar_links : topbar_links}
  )
})

app.get('/about', function(req, res) {
    res.render('about',
    { title : 'About' , topbar_links : topbar_links}
    )
})

//Route for the gallery
app.get('/gallery', function(req, res) {
    client.query('SELECT * FROM Snapshots WHERE DATE_SUB(CURDATE(), INTERVAL 40 DAY) <= Date', function(err, rows, fields) {
        if (err) throw err;

        // Retrieve urls from the database query
        var urls = new Array();
        var text = new Array();
        var dates = new Array();
        for (i in rows) {
            urls[i] = rows[i].Filename;
            text[i] = rows[i].Text;
            dates[i] = rows[i].Date
        }

        res.render('gallery', {
            title : 'Gallery',
            images: urls,
            descriptions: text,
            dates: dates,
            topbar_links : topbar_links
        });
    });
});

