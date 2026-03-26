from db_manager import DatabaseManager
import pandas as pd
from datetime import date
from typing import List
from data_validation import TransactionData, EventUpdates, GroupUpdates, TransactionUpdates

# Date must be iso format string "YYYY-MM-dd"
def createGroup(db: DatabaseManager, username: str, group_name: str, start: str, end: str, location: str, description: str = None) -> int:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)

    if start_date > end_date:
        return False

    group_id = db.addGroupInfo(group_name = group_name, created_by = username,
                               start_date = start, end_date = end, location = location, description = description)
    db.addMemberToGroup(group_id, username)
    db.addUserPaidRelations(group_id, username, username)

    return group_id


def getGroups(db: DatabaseManager, username: str) -> pd.DataFrame:
    return db.getUsersGroups(username = username)

def updateGroup(db: DatabaseManager, group_id: str, updates: GroupUpdates) -> None:
    if not db.groupExists(group_id = group_id):
        return
    
    db.updateGroupInfo(group_id = group_id, field_updates = updates)

def deleteGroup(db: DatabaseManager, group_id: int) -> None:
    if not db.groupExists(group_id = group_id):
        return
    
    db.deleteGroup(group_id = group_id)


def inviteMembersToGroup():
    pass


def acceptInvite(db: DatabaseManager, username: str, group_id: int, new_member: str) -> None:
    if db.userIsMember(group_id, new_member):
        return

    db.addMemberToGroup(group_id = group_id, username = new_member)
    members = db.getGroupMembers(group_id = group_id)

    db.addUserPaidRelations(group_id = group_id, paid_by = new_member, owed_by = new_member)

    for member in members:
        if member == new_member:
            continue
        db.addUserPaidRelations(group_id = group_id, paid_by = new_member, owed_by = member)
        db.addUserPaidRelations(group_id = group_id, paid_by = member, owed_by = new_member)


def leaveGroup():
    pass


# transactions is a list of TransactionData dicts with keys: [item_name, category, amount_due, owed_by]
def createEvent(db: DatabaseManager, username: str, group_id: int, event_name: str,
                event_desc: str, currency: str, transactions: List[TransactionData], paid_by: str = None) -> None:
    if paid_by is None:
        paid_by = username

    event_id = db.addEvent(event_name = event_name, description = event_desc, group_id = group_id,
                           uploaded_by = username, currency = currency, paid_by = paid_by)

    for transaction in transactions:
        split_num = len(transaction["owed_by"])
        amount_per_person = round(transaction["amount_due"] / split_num, 2)

        for ower in transaction["owed_by"]:
            db.addTransaction(group_id = group_id, event_id = event_id, item_name = transaction["item_name"],
                              amount_due = amount_per_person, owed_by = ower, category = transaction["category"])
            db.updateUserOwedAmounts(group_id = group_id, paid_by = paid_by, owed_by = ower,
                                     amount = amount_per_person)


def summarizeAmountDue(db: DatabaseManager, group_id: int) -> dict[str, float]:
    owed_df = db.getGroupOwedAmounts(group_id = group_id)
    owed_df = owed_df[owed_df["owed_by"] != owed_df["paid_by"]]
    group_owed = []
    members = db.getGroupMembers(group_id = group_id)
    for member in members["username"]:

        debits = owed_df[owed_df["paid_by"] == member].groupby("owed_by")["total_paid_for"].sum()
        credits = owed_df[owed_df["owed_by"] == member].groupby("paid_by")["total_paid_for"].sum()

        summary = debits.sub(credits, fill_value = 0)
        df = summary.to_frame().reset_index()
        df.columns = ["paid_by", "amount"]
        df.insert(0, 'owed_by', member)

        group_owed.append(df)

    amount_due = pd.concat(group_owed).reset_index(drop = True)

    return amount_due.to_dict(orient = "records")

if __name__ == "__main__":
    db = DatabaseManager()
    test_console = False

    table_name = "events"
    group_id = 6

    print(summarizeAmountDue(db, group_id))

    if test_console:
        while True:
            query = input("Query: ")
            print(db.runCustomQuery(query))
