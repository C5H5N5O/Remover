from os import name
import sqlite3 as sql

class DB:


    def __init__(self, name):
        self.name = name

    def connect(self):
        con = sql.connect(self.name)
        self.cur = con.cursor()

    def get_all_data_from(self, table):
        self.cur.execute(f"SELECT * FROM '{table}'")
        rows = self.cur.fetchall()
        return rows



