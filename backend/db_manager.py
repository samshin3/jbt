import sqlite3
import pandas as pd
from typing import Literal

class DatabaseManager():

    SearchBy = Literal['group_id', 'event_id']

    def __init__(self):
        self.connection = sqlite3.connect("jbt_database.db", check_same_thread = False)
        self.cursor = self.connection.cursor()

    def close(self):
        self.connection.close()

    def runCustomQuery(self, query : str) -> pd.DataFrame:
        self.cursor.execute(query)
        self.connection.commit()
        return self.convertToDataFrame()
    
    # Converts queries into Pandas DataFrame object for viewing
    def convertToDataFrame(self) -> pd.DataFrame | bool:
        if not self.cursor.description:
            return False
        
        headers = [description[0] for description in self.cursor.description]
        rows = self.cursor.fetchall()

        df = pd.DataFrame(rows, columns=headers)
        return df
    
    # Manage "users" table
    def addUser(self, username : str, email : str, pfp : str) -> None:
        query = f"INSERT INTO users (username, email, profile_picture, verified) VALUES ('{username}', '{email}', '{pfp}', FALSE)"
        self.cursor.execute(query)
        self.connection.commit()

    def getUserData(self, username : str) -> pd.DataFrame:
        query = f"""
            SELECT username, email, profile_picture, verified FROM users
            WHERE username = '{username}'
        """

        self.cursor.execute(query)
        user_data = self.convertToDataFrame()
        return user_data

    # Manage "group" table
    def addGroupInfo(self, group_name : str, created_by : str,
                     start_date : str, end_date : str, location : str, description : str = None) -> int:
        query = f"""
                INSERT INTO group_info (
                    group_name,
                    created_by,
                    creation_date,
                    modified_date,
                    start_date,
                    end_date,
                    location,
                    description,
                    status_flag
                )
                VALUES (
                    '{group_name}',
                    '{created_by}',
                    date('now'),
                    date('now'),
                    '{start_date}',
                    '{end_date}',
                    '{location}',
                    '{description}',
                    'inactive'
                )
                """
        self.cursor.execute(query)
        self.connection.commit()

        return self.cursor.lastrowid
    
    def editGroupInfo(self, group_id : int):
        pass

    def getGroupData(self, group_id : int) -> list:
        query = f"""
                SELECT group_name, description,
                    status_flag, modified_date,
                    created_by, creation_date, 
                    start_date, end_date, location
                FROM group_info WHERE group_id = {group_id}
                """
        
        self.cursor.execute(query)
        self.connection.commit()

        group_data = self.convertToDataFrame()
        return group_data

    # Manage "group_members" table
    def userIsMember(self, group_id : int, username : str) -> bool:
        query = f"""
                SELECT COUNT(*) FROM group_members
                WHERE group_id = {group_id} AND
                username = '{username}'
                """

        # Checks if entry exists
        result = self.cursor.execute(query).fetchone()
        return result[0] > 0


    def addMemberToGroup(self, group_id : int, username : str) -> None:
        query = f" INSERT INTO group_members (group_id, username, date_joined) VALUES ({group_id},'{username}', date('now'))"
        self.cursor.execute(query)

    def getGroupMembers(self, group_id : int) -> list:
        query = f"SELECT username FROM group_members WHERE group_id = {group_id}"
        self.cursor.execute(query)
        members = self.convertToDataFrame()

        return members["username"].tolist()

    def getUsersGroups(self, username : str) -> pd.DataFrame:
        
        query = f"""
                SELECT 
                    g.group_name,
                    g.group_id,
                    g.description,
                    g.status_flag,
                    g.created_by,
                    g.modified_date,
                    g.creation_date,
                    g.start_date,
                    g.end_date,
                    g.location
                
                FROM group_info g
                JOIN group_members m ON g.group_id = m.group_id
                WHERE m.username = '{username}'
                """
        
        self.cursor.execute(query)
        data = self.convertToDataFrame()

        return data

    # Manage "events" table
    def addEvent(self, event_name : str, description : str, group_id : int, uploaded_by : str, currency : str, paid_by : str) -> int:
        query = f"""
                INSERT INTO events (
                    event_name,
                    description,
                    group_id,
                    uploaded_by,
                    upload_date,
                    currency,
                    paid_by
                )
                
                VALUES (
                    '{event_name}',
                    '{description}',
                    {group_id},
                    '{uploaded_by}',
                    date('now'),
                    '{currency}',
                    '{paid_by}'
                )
                """

        self.cursor.execute(query)
        self.connection.commit()
        return self.cursor.lastrowid
    
    def getEvent(self, event_id : int) -> pd.DataFrame:
        query = f"SELECT event_name, description, group_id, uploaded_by, upload_date, currency FROM event_id WHERE event_id = {event_id}"

        self.cursor.execute(query)
        event_data = self.convertToDataFrame()

        return event_data

    # Manage "transactions" table
    def addTransaction(self, group_id : int, event_id : int, item_name : str,
                       amount_due : float, owed_by : str, category : str) -> int:
        query = f"""
                INSERT INTO transactions (
                    group_id,
                    event_id,
                    item_name,
                    amount_due,
                    owed_by,
                    category,
                    modified_date
                )
                VALUES (
                    {group_id},
                    {event_id},
                    '{item_name}',
                    {amount_due},
                    '{owed_by}',
                    '{category}',
                    date('now')
                )
                """
        
        self.cursor.execute(query)
        self.connection.commit()
        
        return self.cursor.lastrowid

    def getTransactions(self, by : SearchBy, id_value : int) -> pd.DataFrame:
        query = f"SELECT transaction_id, modified_date, item_name, category, amount_due, owed_by FROM transactions WHERE {by} = {id_value}"

        self.cursor.execute(query)
        transactions = self.convertToDataFrame()

        return transactions.to_dict(orient="records")

    # Manage "user_paid_amounts" table
    def addUserPaidRelations(self, group_id : int, paid_by : str,
                             owed_by : str) -> None:
        initial_owed_amt = 0
        query = f"""
                INSERT INTO user_paid_amounts VALUES (
                    {group_id},
                    '{paid_by}',
                    '{owed_by}',
                    {initial_owed_amt}
                )
                """
        
        self.cursor.execute(query)
        self.connection.commit()
    
    def getUserOwedAmounts(self, group_id : int, username : str) -> pd.DataFrame:
        query = f"""
                SELECT paid_by, owed_by, total_paid_for FROM user_paid_amounts 
                WHERE group_id = {group_id} AND
                (paid_by = '{username}' OR owed_by = '{username}')
                """
        
        self.cursor.execute(query)
        owed_amounts = self.convertToDataFrame()

        return owed_amounts

    def updateUserOwedAmounts(self, group_id : int, paid_by : str, owed_by : str, amount : int) -> None:
        query = f"""
                UPDATE user_paid_amounts
                SET total_paid_for = total_paid_for + {amount}
                WHERE group_id = {group_id} AND
                paid_by = '{paid_by}' AND
                owed_by = '{owed_by}'
                """
        self.cursor.execute(query)
        self.connection.commit()

    def getTotalSpent(self, group_id : int) -> int:
        query = f"""
                SELECT SUM(amount_due) AS total FROM transactions
                WHERE group_id = {group_id}
                """
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return result[0]

if __name__ == "__main__":
    session = DatabaseManager()

    print(type(session.getTotalSpent(6)))
    #group_id = session.addGroupInfo("Test", "test", 'test', 'test', 'iowa')
    #session.addUser("sam", "sam@uwaterloo.ca")
    #print(session.getGroupMembers(3))
    # while True:
    #     query = input("Query: ")
    #     results, headers = session.runCustomQuery(query)
    #     if headers:
    #         df = pd.DataFrame(results,columns=headers)
    #         print(df)
        