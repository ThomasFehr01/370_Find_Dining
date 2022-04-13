import sqlite3
import os


class DBManager:
    def __init__(self, path="../../FindDining.db"):
        """
        Create a new db manager
        :param path: Path to the db
        """

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(BASE_DIR, path)

    def insert(self, query, data):
        """
        Insert a row into the database
        :param query: Str, the sql select statement to be used for the query
        :param data: Tuple, the arguments to be passed to the database along with the query
        :return: None
        """
        with sqlite3.connect(self.db_path) as con:

            cursor = con.cursor()
            cursor.execute(query, data)

            con.commit()

    def select_one(self, query, data):
        """
        Selects a single row from the database using the given query and data
        :param query: Str, the sql select statement to be used for the query
        :param data: Tuple, the arguments to be passed to the database along with the query
        :return: The first selected row from the database
        """
        with sqlite3.connect(self.db_path) as con:

            cursor = con.cursor()
            cursor.execute(query, data)

            selectVal = cursor.fetchone()

            if selectVal is not None:
                selectVal = selectVal[0]

            return selectVal

    def select_many(self, query, data : list):
        """
        Special select statement to be used exclusively in database to dict

        :param query: Sql query to be passed to the db
        :param data: list of all the different values to be passed to the db
        :return: None, but users will be updated
                        """

        queryData = []
        with sqlite3.connect(self.db_path) as con:

            cursor = con.cursor()

            for cID in data:
                cursor.execute(query, (cID,))

                selectVal = cursor.fetchone()

                if selectVal is None:
                    return None

                queryData.append(selectVal)

            return queryData
