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

        # db.updateUserOwedAmounts(group_id = group_id, paid_by = paid_by, owed_by = ower,
        #                         amount = amount_per_person)

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
    
    old_data = db.getEventDetails(event_id = event_id, as_json = False)

    db.updateEvent(event_id = event_id, event_updates = event_edits)
    for transaction in transaction_edits:

        match transaction["action"]:
            case "new":
                print("submit transaction called")
                submitTransaction(db = db, transaction = transaction["transaction_data"],
                                  group_id = group_id, event_id = event_id, paid_by = event_edits["paid_by"] if "paid_by" in event_edits.keys() else old_data["paid_by"][0])

            # "delete" action is separate from removing an owed_by member    
            case "delete":
                db.deleteTransaction(by = "subgroup_id", id_value = transaction["subgroup_id"])

            case "update":
                old_transaction = old_data[old_data["subgroup_id"] == transaction["subgroup_id"]]
                old_transaction_data = old_transaction.loc[0, ["owed_by", "amount_due", "item_name", "category"]].to_dict()
                updateOwerRecords(db = db, old_data = old_transaction_data, new_data = transaction["transaction_data"], 
                                  group_id = group_id, event_id = event_id, subgroup_id = transaction["subgroup_id"])

# Helper function, compares transaction data and updates, or inserts new transaction record
def updateOwerRecords(db: DatabaseManager, old_data: TransactionData, new_data: TransactionData,
                      group_id: int, event_id: int, subgroup_id: int) -> None:

    new_count = len(new_data["owed_by"])
    new_amount = round(new_data["amount_due"] / new_count, 2)
    new_data["amount_due"] = new_amount

    # Delete old owed_by
    for member in old_data["owed_by"]:
        if member not in new_data["owed_by"]:
            db.deleteTransaction(by = "subgroup_id", id_value = subgroup_id, owed_by = member)

    # Update / add details for owed_by
    for member in new_data["owed_by"]:

        if member not in old_data["owed_by"]:
            print("add transaction called")
            db.addTransaction(group_id = group_id, event_id = event_id, item_name = new_data["item_name"],
                              amount_due = new_amount, owed_by = member, category = new_data["category"], subgroup = subgroup_id)
        else:
            update_info = new_data
            update_info["owed_by"] = member
            print(update_info)
            db.updateTransaction(subgroup_id = subgroup_id, update_info = update_info)
                
# Updates users owed amounts as well
def deleteEvent(db: DatabaseManager, event_id: int) -> None:
    transactions = db.getTransactions(by = 'event_id', id_value = event_id)
    paid_by = db.getEvent(event_id = event_id)["paid_by"][0]
    recon = transactions.groupby("owed_by")["amount_due"].sum().reset_index()
    recon["amount_due"] = recon["amount_due"].apply(lambda x: x * -1)

    db.deleteEvent(event_id = event_id)
    db.deleteTransaction(by = 'event_id', id_value = event_id)
    
    # for index, row in recon.iterrows():
    #     db.updateUserOwedAmounts(group_id = group_id, paid_by = paid_by, owed_by = row["owed_by"], amount = row["amount_due"])


if __name__ == "__main__":

    db = DatabaseManager()
    test_console = False

    event_edits = {
        # "event_name": "new_name",
        # "description": "new_description",
        # "currency": "SGD",
        # "paid_by": "Michelle"
    }

    transaction_updates = [
        # {
        #     "subgroup_id": 57,
        #     "action": "delete"
        # },
        {
            "subgroup_id": 75,
            "action": "update",
            "transaction_data": {
                "item_name": "New Edit",
                "category": "Testing",
                "amount_due": 3300,
                "owed_by": ["Sam", "Tristan", "Michelle"]
            }
        }
    ]


    updateEventFull(db = db, group_id = 6, event_id = 19, event_edits=event_edits, transaction_edits=transaction_updates)

    print(db.getEventDetails(19, as_json = False))

    if test_console:
        while True:
            query = input("Query: ")
            print(db.runCustomQuery(query))
