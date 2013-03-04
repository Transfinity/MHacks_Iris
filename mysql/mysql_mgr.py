#!/usr/bin/python

import MySQLdb as mdb
import sys

SERVER_IP = 'iris.cbktya2t5svb.us-east-1.rds.amazonaws.com'
USER_NAME = 'iris_ocr'
PASSWORD  = 'blueballoon'
DATABASE  = 'irisdb'
INSERT_QUERY = "INSERT INTO Snapshots(Filename, Text, Date, Time)  \
        VALUES('%s','%s','%s', '%s')"

class MySQL_Mgr :

    def __init__ (self) :
        self.con = mdb.connect(SERVER_IP, USER_NAME, PASSWORD, DATABASE)
        with self.con :
            self.cur = self.con.cursor()

    def create_table (self) :
        create_query = """
            CREATE TABLE IF NOT EXISTS Snapshots(
                Id          INT PRIMARY KEY AUTO_INCREMENT,
                Filename    VARCHAR(256),
                Text        VARCHAR(1024),
                Date        DATE,
                Time        TIME
            )"""
        self.cur.execute(create_query)

    def add_image (self, filename, text='', date='', time='') :
        # TODO: add some sanity checks
        self.cur.execute(INSERT_QUERY %(filename, text, date, time))

    def view_table (self) :
        self.cur.execute("SELECT * FROM Snapshots");
        rows = self.cur.fetchall()
        for row in rows :
            print row

    def drop_table (self) :
        self.cur.execute("DROP TABLE IF EXISTS Snapshots");

    def commit (self) :
        self.con.commit()

if __name__ == '__main__' :
    mgr = MySQL_Mgr()
    mgr.drop_table()
    mgr.create_table()
    mgr.add_image('https://s3.amazonaws.com/mhacks_iris/raw/11.17.png', 'MHacks is the most epic hackathon. Ever. We are team IRIS, the future of vision.', '2013-02-03', '05:34:52')
    mgr.add_image('https://s3.amazonaws.com/mhacks_iris/raw/402.41.png', 'Share your hack on Seelio. Win $500! And also, a chance to interview with: Create an account at seelio.com Add your hack Tag it w "mhacks2013"', '2013-02-03', '08:54:24')
    mgr.add_image('https://s3.amazonaws.com/mhacks_iris/raw/42.36.png', 'MHACKS CHECK-IN', '2013-02-03', '08:54:24')
    mgr.add_image('https://s3.amazonaws.com/mhacks_iris/raw/84.96.png', 'Coleman: ACLU, unions Laws hinder 'U' tuition equality', '2013-02-03', '09:04:53')
    mgr.commit()
    mgr.view_table()
