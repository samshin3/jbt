from db_manager import DatabaseManager
import pandas as pd
from datetime import date
from typing import TypedDict, List

class TransactionData(TypedDict):
    item_name: str
    category: str
    amount_due: float
    owed_by: List[str]


# Date must be iso format string "YYYY-MM-dd"
def createGroup(db: DatabaseManager, username: str, group_name: str, start: str, end: str, location: str, description: str = None) -> int:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)

    if start_date > end_date:
        return False

    group_id = db.addGroupInfo(group_name=group_name, created_by=username,
                               start_date=start, end_date=end, location=location, description=description)
    db.addMemberToGroup(group_id, username)
    db.addUserPaidRelations(group_id, username, username)

    return group_id


def getGroups(db: DatabaseManager, username: str):
    return db.getUsersGroups(username=username)


def inviteMembersToGroup():
    pass


def acceptInvite(db: DatabaseManager, username: str, group_id: int, new_member: str) -> None:
    if db.userIsMember(group_id, new_member):
        return

    db.addMemberToGroup(group_id=group_id, username=new_member)
    members = db.getGroupMembers(group_id=group_id)

    db.addUserPaidRelations(group_id=group_id, paid_by=new_member, owed_by=new_member)

    for member in members:
        if member == new_member:
            continue
        db.addUserPaidRelations(group_id=group_id, paid_by=new_member, owed_by=member)
        db.addUserPaidRelations(group_id=group_id, paid_by=member, owed_by=new_member)


def leaveGroup():
    pass


# transactions is a list of TransactionData dicts with keys: [item_name, category, amount_due, owed_by]
def createEvent(db: DatabaseManager, username: str, group_id: int, event_name: str,
                event_desc: str, currency: str, transactions: List[TransactionData], paid_by: str = None) -> None:
    if paid_by is None:
        paid_by = username

    event_id = db.addEvent(event_name=event_name, description=event_desc, group_id=group_id,
                           uploaded_by=username, currency=currency, paid_by=paid_by)

    for transaction in transactions:
        split_num = len(transaction["owed_by"])
        amount_per_person = transaction["amount_due"] / split_num

        for ower in transaction["owed_by"]:
            db.addTransaction(group_id=group_id, event_id=event_id, item_name=transaction["item_name"],
                              amount_due=amount_per_person, owed_by=ower, category=transaction["category"])
            db.updateUserOwedAmounts(group_id=group_id, paid_by=paid_by, owed_by=ower,
                                     amount=amount_per_person)


def summarizeAmountDue(db: DatabaseManager, group_id: int, username: str) -> dict[str, float]:
    owed_df = db.getUserOwedAmounts(group_id=group_id, username=username)
    owed_df = owed_df[owed_df["paid_by"] != owed_df["owed_by"]]

    owed_to_user = owed_df[owed_df["paid_by"] == username].groupby("owed_by")["total_paid_for"].sum()
    owed_by_user = owed_df[owed_df["owed_by"] == username].groupby("paid_by")["total_paid_for"].sum()

    net_balance = owed_to_user.sub(owed_by_user, fill_value=0)

    return net_balance.to_dict()


if __name__ == "__main__":
    db = DatabaseManager()
    test_console = True

    table_name = "events"
    group_id = 6

    print(summarizeAmountDue(db, group_id, "Sam"))

    if test_console:
        while True:
            query = input("Query: ")
            print(db.runCustomQuery(query))
