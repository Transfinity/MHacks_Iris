#!/usr/bin/python

import MySQLdb as mdb
import sys

SERVER_IP = 'localhost'
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
        self.cur.execute("DROP TABLE Snapshots");

    def commit (self) :
        self.con.commit()

if __name__ == '__main__' :
    mgr = MySQL_Mgr()
    mgr.add_image('images/fake.png', 'fake text', '2013-02-28', '12:00:00')
    mgr.add_image('images/poop.png', 'fake text', '2013-02-28', '12:30:00')
    mgr.add_image('images/test.png', 'fake text', '2013-02-28', '14:00:00')
    mgr.commit()
    mgr.view_table()
