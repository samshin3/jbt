from jbt import DatabaseManager
import pandas as pd
from datetime import date, datetime

# sqlite db instance
db_session = DatabaseManager()

class UserSession():
    
    def __init__(self, username : str):
        df = db_session.getUserData(username)
        self.username = username
        self.email = df["email"][0]
        self.is_verified = df["verified"][0]

    # Date must be iso format string "YYYY-MM-dd"
    def createGroup(self, group_name : str, start : str, end : str, location : str, description : str = None) -> bool:

        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)

        if start_date > end_date: # Validate date range
            return False
        
        group_id = db_session.addGroupInfo(group_name = group_name, created_by = self.username, 
                                           start_date = start, end_date = end, location = location, description = description)

        db_session.addMemberToGroup(group_id, self.username)
        return True
    
    def inviteMembersToGroup():
        pass

    def acceptInvite():
        pass

    def getGroups():
        pass

    def getUserBalanceOwed():
        pass

    def leaveGroup():
        pass


if __name__ == "__main__":
    db_session.addUser("Sam", "cookiechomperiii@gmail.com")
    user_session = UserSession("Sam")
    table_name = "group_info"
    db_session.runCustomQuery(f"ALTER TABLE group_info ALTER COLUMN creation_date DATETIME")
    print(db_session.runCustomQuery(f"SELECT * FROM {table_name}"))