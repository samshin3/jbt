from db_manager import DatabaseManager
import pandas as pd
from datetime import date
from typing import List
from data_validation import TransactionData, EventUpdates, GroupUpdates, TransactionEdits

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
        submitTransaction(db = db, transaction = transaction, group_id = group_id, event_id = event_id, paid_by = paid_by)
        
def submitTransaction(db: DatabaseManager, transaction: TransactionData, group_id: int, event_id: int, paid_by: str) -> None:

    split_num = len(transaction["owed_by"])
    amount_per_person = round(transaction["amount_due"] / split_num, 2)
    isFirstEntry = True
    subgroupID = None

    for ower in transaction["owed_by"]:
        trans_id = db.addTransaction(group_id = group_id, event_id = event_id, item_name = transaction["item_name"],
                          amount_due = amount_per_person, owed_by = ower, category = transaction["category"], subgroup = subgroupID)
        if isFirstEntry:
            subgroupID = trans_id
            isFirstEntry = False

        db.updateUserOwedAmounts(group_id = group_id, paid_by = paid_by, owed_by = ower,
                                amount = amount_per_person)

def summarizeAmountDue(db: DatabaseManager, group_id: int) -> dict[str, float]:
    members = db.getGroupMembers(group_id = group_id)
    owed_df = db.getGroupOwedSummary(group_id = group_id)

    for payer in members["username"]:
        for ower in members["username"]:
            filtered_owed_df = owed_df[(owed_df["owed_by"] == ower) & (owed_df["paid_by"] == payer)]

            if filtered_owed_df.empty:
                row = pd.DataFrame([{
                    "owed_by": ower,
                    "paid_by": payer,
                    "amount_due": 0
                }])

                owed_df = pd.concat([owed_df, row])

    owed_df = owed_df[owed_df["owed_by"] != owed_df["paid_by"]]
    group_owed = []
    for member in members["username"]:

        debits = owed_df[owed_df["paid_by"] == member].groupby("owed_by")["amount_due"].sum()
        credits = owed_df[owed_df["owed_by"] == member].groupby("paid_by")["amount_due"].sum()

        summary = debits.sub(credits, fill_value = 0)
        df = summary.to_frame().reset_index()
        df.columns = ["paid_by", "amount"]
        df.insert(0, 'owed_by', member)

        group_owed.append(df)

    amount_due = pd.concat(group_owed).reset_index(drop = True)

    return amount_due.to_dict(orient = "records")

def updateEventFull(db: DatabaseManager, group_id: int, event_id: int, event_edits: EventUpdates, transaction_edits: List[TransactionEdits]):
    
    old_data = db.getEventDetails(event_id = event_id)

    db.updateEvent(event_id = event_id, event_updates = event_edits)

    for transaction in transaction_edits:
        old_transaction = old_data[old_data["subgroup_id"] == transaction["subgroup_id"]]
        ower_list = old_transaction["owed_by"][0].split(",")
        owed_amount = old_transaction["amount_due"][0]
        paid_by = old_transaction["paid_by"][0]

        match transaction["action"]:
            case "new":
                submitTransaction(db = db, transaction = transaction["transaction_data"],
                                  group_id = group_id, event_id = event_id, paid_by = event_edits["paid_by"])

            # "delete" action is separate from removing an owed_by member    
            case "delete":
                db.deleteTransaction(by = "subgroup_id", id_value = transaction["subgroup_id"])

                for ower in ower_list:
                    db.updateUserOwedAmounts(group_id = group_id, paid_by = paid_by, owed_by = ower, amount = owed_amount * -1)

            case "update":
                pass

def compare(old):
    pass


                
# Updates users owed amounts as well
def deleteEvent(db: DatabaseManager, event_id: int, group_id: int) -> None:
    transactions = db.getTransactions(by = 'event_id', id_value = event_id)
    paid_by = db.getEvent(event_id = event_id)["paid_by"][0]
    recon = transactions.groupby("owed_by")["amount_due"].sum().reset_index()
    recon["amount_due"] = recon["amount_due"].apply(lambda x: x * -1)

    db.deleteEvent(event_id = event_id)
    db.deleteTransaction(by = 'event_id', id_value = event_id)
    
    for index, row in recon.iterrows():
        db.updateUserOwedAmounts(group_id = group_id, paid_by = paid_by, owed_by = row["owed_by"], amount = row["amount_due"])


if __name__ == "__main__":
    db = DatabaseManager()
    test_console = False

    updateEventFull(db = db, group_id = 6, event_id = 14)

    table_name = "events"
    group_id = 6

    print(None)

    if test_console:
        while True:
            query = input("Query: ")
            print(db.runCustomQuery(query))
