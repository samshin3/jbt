from jbt import DatabaseManager
import pandas as pd
from datetime import date
from typing import TypedDict, List

class TransactionData(TypedDict):
    item_name: str
    category: str
    amount_due: float
    owed_by: List[str]

# sqlite db instance
db_session = DatabaseManager()

class UserSession():
    
    def __init__(self, username : str):
        df = db_session.getUserData(username)
        self.username = username
        self.email = df["email"][0]
        self.is_verified = df["verified"][0]

    # Date must be iso format string "YYYY-MM-dd"
    def createGroup(self, group_name : str, start : str, end : str, location : str, description : str = None) -> int:

        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)

        if start_date > end_date: # Validate date range
            return False
        
        group_id = db_session.addGroupInfo(group_name = group_name, created_by = self.username, 
                                           start_date = start, end_date = end, location = location, description = description)

        db_session.addMemberToGroup(group_id, self.username)
        db_session.addUserPaidRelations(group_id, self.username, self.username)

        return group_id
    
    def inviteMembersToGroup():
        pass

    def acceptInvite(self, group_id : int, new_member : str) -> None:
        if db_session.userIsMember(group_id, new_member):
            return 
        
        db_session.addMemberToGroup(group_id = group_id, username = new_member)
        members = db_session.getGroupMembers(group_id = group_id)

        # Add user paid relations for the new member of the group
        db_session.addUserPaidRelations(group_id = group_id, paid_by = new_member, owed_by = new_member)

        for member in members:
            if member == new_member:
                continue

            db_session.addUserPaidRelations(group_id = group_id, paid_by = new_member, owed_by = member)
            db_session.addUserPaidRelations(group_id = group_id, paid_by = member, owed_by = new_member)

    def leaveGroup():
        pass

    # transactions is a  list of dictionaries with the following keys: [item name, category, amount_due, owed_by]
    def createEvent(self, group_id : int, event_name : str, event_desc : str,
                    currency : str, transactions : List[TransactionData], paid_by : str = None) -> None:
        if paid_by is None:
            paid_by = self.username

        event_id = db_session.addEvent(event_name = event_name, description = event_desc, group_id = group_id,
                            uploaded_by = self.username, currency = currency, paid_by = paid_by)
        
        for transaction in transactions:
            # Add Transaction History
            split_num = len(transaction["owed_by"])
            amount_per_person = transaction["amount_due"] / split_num
            for ower in transaction["owed_by"]:
                db_session.addTransaction(group_id = group_id, event_id = event_id, item_name = transaction["item_name"],
                                        amount_due = amount_per_person, owed_by = ower,
                                        category = transaction["category"])
                   
                # Add user owed amounts
                db_session.updateUserOwedAmounts(group_id = group_id, paid_by = paid_by, owed_by = ower,
                                                amount = amount_per_person)
            
    def summarizeAmountDue(self, group_id : int, user : str = None) -> dict[str, float]:
        if user is None:
            user = self.username
        
        owed_df = db_session.getUserOwedAmounts(group_id = group_id, username = user)
        owed_df = owed_df[owed_df["paid_by"] != owed_df["owed_by"]]

        owed_to_user = owed_df[owed_df["paid_by"] == user].groupby("owed_by")["total_paid_for"].sum()
        owed_by_user = owed_df[owed_df["owed_by"] == user].groupby("paid_by")["total_paid_for"].sum()

        net_balance = owed_to_user.sub(owed_by_user, fill_value = 0)

        return net_balance.to_dict()


if __name__ == "__main__":
    #db_session.addUser("Michelle", "myn@gmail.com", "test")
    test_console = True

    user_session = UserSession("Sam")
    table_name = "events"
    group_id = 6
    #user_session.createEvent(6, "Day 1 Test", "Test event", "JPY", sample_transactions, "Joanna")
    #user_session.acceptInvite(6, "Michelle")
    #user_session.acceptInvite(6, "Joanna")
    #user_session.acceptInvite(6, "Tristan")

    #user_session.createGroup("Japan Trip 2026", "2026-04-29", "2026-05-09", "Japan", "Our Japan trip funds tracker")
    #print(db_session.runCustomQuery(f"SELECT * FROM {table_name}"))
    print(user_session.summarizeAmountDue(6, "Sam"))

    if test_console:
        while True:
            query = input("Query: ")
            print(db_session.runCustomQuery(query))
