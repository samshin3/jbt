import sqlite3
import pandas as pd
from typing import Literal
from data_validation import GroupUpdates, TransactionUpdates, EventUpdates, validActions

class DatabaseManager():

    IdCategories = Literal["group_id", "event_id", "transaction_id", "subgroup_id"]

    def __init__(self):
        self.connection = sqlite3.connect("jbt_database.db", check_same_thread = False)
        self.cursor = self.connection.cursor()

    def close(self):
        self.connection.close()

    def runCustomQuery(self, query: str) -> pd.DataFrame:
        self.cursor.execute(query)
        self.connection.commit()
        return self.convertToDataFrame()
    
    # Converts queries into Pandas DataFrame object for viewing
    def convertToDataFrame(self) -> pd.DataFrame | bool:
        if not self.cursor.description:
            return False
        
        headers = [description[0] for description in self.cursor.description]
        rows = self.cursor.fetchall()

        df = pd.DataFrame(rows, columns = headers)
        return df
    
    # Manage "users" table
    def addUser(self, username: str, email: str, pfp: str) -> None:
        query = f"INSERT INTO users (username, email, profile_picture, verified) VALUES ('{username}', '{email}', '{pfp}', FALSE)"
        self.cursor.execute(query)
        self.connection.commit()

    def getUserData(self, username: str) -> pd.DataFrame:
        query = f"""
            SELECT username, email, profile_picture, verified FROM users
            WHERE username = '{username}'
        """

        self.cursor.execute(query)
        user_data = self.convertToDataFrame()
        return user_data

    # Manage "group" table
    def addGroupInfo(self, group_name: str, created_by: str,
                     start_date: str, end_date: str, location: str, description: str = None) -> int:
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
    
    def updateGroupInfo(self, group_id: int, field_updates: GroupUpdates) -> None:
        allowed_fields = ("group_name", "description", "start_date", "end_date", "location")
        updates = []

        for field, value in field_updates.items():
            if field in allowed_fields and value is not None:
                updates.append(f"{field} = '{value}'")

        update_queries = ", ".join(updates)
        query = f"""
                UPDATE group_info
                SET {update_queries}, modified_date = date('now')
                WHERE group_id = {group_id}
                """
        self.cursor.execute(query)
        self.connection.commit()

    def getGroupData(self, group_id: int) -> list:
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

    def groupExists(self, group_id: int) -> bool:
        query = f"""
                SELECT COUNT(*) FROM group_info
                WHERE group_id = {group_id}
                """
        result = self.cursor.execute(query).fetchone()
        return result[0] > 0

    def deleteGroup(self, group_id: int) -> None:
        query = f"""
                UPDATE group_info 
                SET status_flag = 'deleted', modified_date = date('now')
                WHERE group_id = {group_id}
                """
        
        self.cursor.execute(query)
        self.connection.commit()

    # Manage "group_members" table
    def userIsMember(self, group_id: int, username: str) -> bool:
        query = f"""
                SELECT COUNT(*) FROM group_members
                WHERE group_id = {group_id} AND
                username = '{username}'
                """

        # Checks if entry exists
        result = self.cursor.execute(query).fetchone()
        return result[0] > 0

    def addMemberToGroup(self, group_id: int, username: str) -> None:
        query = f" INSERT INTO group_members (group_id, username, date_joined) VALUES ({group_id},'{username}', date('now'))"
        self.cursor.execute(query)

    def getGroupMembers(self, group_id: int) -> pd.DataFrame:
        query = f"""
                SELECT u.username, u.email, u.profile_picture, u.verified, g.is_owner FROM group_members g
                LEFT JOIN users u ON u.username = g.username
                WHERE g.group_id = {group_id}
                """
        self.cursor.execute(query)
        members = self.convertToDataFrame()

        return members

    def getUsersGroups(self, username: str) -> pd.DataFrame:
        
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
                WHERE m.username = '{username}' AND
                NOT g.status_flag = 'deleted'
                """
        
        self.cursor.execute(query)
        data = self.convertToDataFrame()

        return data

    # Manage "events" table
    def addEvent(self, event_name: str, description: str, group_id: int, uploaded_by: str, currency: str, paid_by: str) -> int:
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
    
    def getEventDetails(self, event_id: int) ->pd.DataFrame:
        query = f"""
                SELECT
                    e.event_name, e.description, e.paid_by, e.currency, e.event_id,
                    t.transaction_id, t.item_name, SUM(t.amount_due) AS amount_due, 
                    t.category, GROUP_CONCAT(t.owed_by) AS owed_by, t.subgroup_id
                FROM transactions t
                INNER JOIN events e ON e.event_id = t.event_id
                WHERE e.event_id = {event_id}
                GROUP BY t.subgroup_id
                """
        self.cursor.execute(query)
        data = self.convertToDataFrame()

        return data

    def getEvent(self, event_id: int) -> pd.DataFrame:
        query = f"""
                SELECT event_name, description, event_id, group_id, uploaded_by, upload_date, modified_date, currency, status_flag, paid_by FROM events
                WHERE event_id = {event_id} AND 
                (status_flag != 'deleted' OR status_flag IS NULL)
                """

        self.cursor.execute(query)
        event_data = self.convertToDataFrame()

        return event_data
    
    def getEventSummary(self, group_id: int) -> pd.DataFrame:
        query = f"""
                SELECT
                    e.event_id,
                    e.event_name,
                    e.upload_date,
                    SUM(t.amount_due) AS total,
                    e.paid_by
                FROM events e

                LEFT JOIN transactions t ON e.event_id = t.event_id
                WHERE e.group_id = {group_id} AND
                (e.status_flag != 'deleted' OR e.status_flag IS NULL) AND
                (t.status_flag != 'deleted' OR t.status_flag IS NULL)
                GROUP BY e.event_id
                """
        self.cursor.execute(query)
        event_summary = self.convertToDataFrame()

        return event_summary

    def updateEvent(self, event_id: int, event_updates: EventUpdates):
        allowed_fields = ("event_name", "description", "currency", "paid_by")
        updates = []

        for field, value in event_updates.items():
            if field in allowed_fields and value is not None:
                updates.append(f"{field} = '{value}'")

        update_queries = ", ".join(updates)
        query = f"""
                UPDATE events
                SET {update_queries}, modified_date = date('now')
                WHERE event_id = {event_id}
                """
        self.cursor.execute(query)
        self.connection.commit()

    def deleteEvent(self, event_id: int) -> None:
        query = f"""
                UPDATE events 
                SET status_flag = 'deleted', modified_date = date('now')
                WHERE event_id = {event_id}
                """

        self.cursor.execute(query)
        self.connection.commit()

    # Manage "transactions" table
    def addTransaction(self, group_id: int, event_id: int, item_name: str,
                       amount_due: float, owed_by: str, category: str, subgroup: int = None) -> int:
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
        id = subgroup if subgroup is not None else self.cursor.lastrowid

        subgroup_query = f"UPDATE transactions SET subgroup_id = {id} WHERE transaction_id = {self.cursor.lastrowid}"

        self.cursor.execute(subgroup_query)
        self.connection.commit()
        
        return self.cursor.lastrowid

    def getTransactions(self, by: IdCategories, id_value: int, aggr: bool = False) -> pd.DataFrame:
        if aggr:
            query = f"""
                    SELECT transaction_id, subgroup_id, modified_date, item_name, 
                    category, amount_due, GROUP_CONCAT(owed_by) AS owed_by FROM transactions 
                    WHERE {by} = {id_value} AND 
                    (status_flag != 'deleted' OR status_flag IS NULL)
                    GROUP BY subgroup_id
                    """
        else: 
            query = f"""
                    SELECT transaction_id, subgroup_id, modified_date, item_name, category, amount_due, owed_by FROM transactions 
                    WHERE {by} = {id_value} AND 
                    (status_flag != 'deleted' OR status_flag IS NULL)
                    """            

        self.cursor.execute(query)
        transactions = self.convertToDataFrame()

        return transactions

    # Assumes owed_by inside transaction_updates exists as an entry
    def updateTransaction(self, subgroup_id: int, update_info: TransactionUpdates) -> None:
        allowed_fields = ("item_name", "amount_due", "category")
        updates = []

        for field, value in update_info.items():
            if field in allowed_fields and value is not None:
                updates.append(f"{field} = '{value}'")

        update_queries = ", ".join(updates)
        query = f"""
                UPDATE transactions
                SET {update_queries}, modified_date = date('now')
                WHERE subgroup_id = {subgroup_id} AND
                owed_by = {update_info["owed_by"]}
                """
        self.cursor.execute(query)
        self.connection.commit()

    def deleteTransaction(self, by: IdCategories, id_value: int, owed_by: str = None) -> None:
        query = f"""
                UPDATE transactions 
                SET status_flag = 'deleted', modified_date = date('now')
                WHERE {by} = {id_value} 
                """
        
        if owed_by is not None:
            query += f"AND owed_by = '{owed_by}'" 

        self.cursor.execute(query)
        self.connection.commit()

    def getTotalSpent(self, group_id: int) -> int:
        query = f"""
                SELECT SUM(amount_due) AS total FROM transactions
                WHERE group_id = {group_id}
                """
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return result[0]

    def getGroupOwedSummary(self, group_id: int) -> pd.DataFrame:
        query = f"""
                SELECT
                    e.paid_by, t.owed_by, SUM(t.amount_due) AS amount_due
                FROM transactions t
                INNER JOIN events e ON e.event_id = t.event_id
                WHERE e.group_id = {group_id} AND
                    (t.status_flag != 'deleted' OR t.status_flag IS NULL)
                GROUP BY t.owed_by, e.paid_by
                """
        
        self.cursor.execute(query)
        summary = self.convertToDataFrame()

        return summary
    
    # user_paid_amounts table functions: deprecated since 28 March, 2026. Replaced with getGroupOwedSummary

    # def addUserPaidRelations(self, group_id: int, paid_by: str,
    #                          owed_by: str) -> None:
    #     initial_owed_amt = 0
    #     query = f"""
    #             INSERT INTO user_paid_amounts VALUES (
    #                 {group_id},
    #                 '{paid_by}',
    #                 '{owed_by}',
    #                 {initial_owed_amt}
    #             )
    #             """
        
    #     self.cursor.execute(query)
    #     self.connection.commit()


    # def getUserOwedAmounts(self, group_id: int, username: str) -> pd.DataFrame:
    #     query = f"""
    #             SELECT paid_by, owed_by, total_paid_for FROM user_paid_amounts 
    #             WHERE group_id = {group_id} AND
    #             (paid_by = '{username}' OR owed_by = '{username}')
    #             """
        
    #     self.cursor.execute(query)
    #     owed_amounts = self.convertToDataFrame()

    #     return owed_amounts


    # def getGroupOwedAmounts(self, group_id: int) -> pd.DataFrame:
    #     query = f"""
    #             SELECT paid_by, owed_by, total_paid_for FROM user_paid_amounts 
    #             WHERE group_id = {group_id}
    #             """
        
    #     self.cursor.execute(query)
    #     owed_amounts = self.convertToDataFrame()

    #     return owed_amounts

    # def updateUserOwedAmounts(self, group_id: int, paid_by: str, owed_by: str, amount: int) -> None:
    #     query = f"""
    #             UPDATE user_paid_amounts
    #             SET total_paid_for = total_paid_for + {amount}
    #             WHERE group_id = {group_id} AND
    #             paid_by = '{paid_by}' AND
    #             owed_by = '{owed_by}'
    #             """
    #     self.cursor.execute(query)
    #     self.connection.commit()


if __name__ == "__main__":
    session = DatabaseManager()
    print(session.runCustomQuery("""
                SELECT
                    e.paid_by, t.owed_by, SUM(t.amount_due) AS amount_due
                FROM transactions t
                INNER JOIN events e ON e.event_id = t.event_id
                WHERE t.status_flag != 'deleted' OR t.status_flag IS NULL
                GROUP BY t.owed_by, e.paid_by
                """))
    
    print(session.runCustomQuery("SELECT * FROM user_paid_amounts WHERE group_id = 6 ORDER BY paid_by ASC" ))
    #print(session.runCustomQuery("SELECT * FROM events"))
    #group_id = session.addGroupInfo("Test", "test", 'test', 'test', 'iowa')
    #session.addUser("sam", "sam@uwaterloo.ca")
    #print(session.getGroupMembers(3))
    # while True:
    #     query = input("Query: ")
    #     results, headers = session.runCustomQuery(query)
    #     if headers:
    #         df = pd.DataFrame(results,columns = headers)
    #         print(df)
        