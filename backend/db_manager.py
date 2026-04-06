import libsql_experimental as libsql_client
import pandas as pd
from typing import Literal
from data_validation import GroupUpdates, TransactionUpdates, EventUpdates, validActions, inviteStatus
import os

class DatabaseManager():

    IdCategories = Literal["group_id", "event_id", "transaction_id", "subgroup_id"]

    def __init__(self):
        url = os.getenv("JBT_DATABASE_TURSO_DATABASE_URL")

        url.replace("libsql://", "https://")

        auth_token = os.getenv("JBT_DATABASE_TURSO_AUTH_TOKEN")
        self.client = libsql_client.create_client_sync(
            url=url,
            auth_token=auth_token
        )

    def close(self):
        self.client.close()

    # ─── Internal helpers ─────────────────────────────────────────────────────

    def _execute(self, query: str, params: tuple = ()) -> libsql_client.ResultSet:
        """Execute a single statement and return the ResultSet."""
        if params:
            return self.client.execute(libsql_client.Statement(query, list(params)))
        return self.client.execute(query)

    def _convertToDataFrame(self, result: libsql_client.ResultSet) -> pd.DataFrame | bool:
        """Convert a libsql ResultSet into a Pandas DataFrame."""
        if not result.columns:
            return False
        rows = [list(row) for row in result.rows]
        df = pd.DataFrame(rows, columns=list(result.columns))
        return df

    def runCustomQuery(self, query: str) -> pd.DataFrame:
        result = self._execute(query)
        return self._convertToDataFrame(result)

    # ─── Users ────────────────────────────────────────────────────────────────

    def addUser(self, username: str, email: str, pfp: str) -> None:
        self._execute(
            "INSERT INTO users (username, email, profile_picture, verified) VALUES (?, ?, ?, FALSE)",
            (username, email, pfp)
        )

    def getUserData(self, username: str) -> pd.DataFrame:
        result = self._execute(
            "SELECT username, email, profile_picture, verified FROM users WHERE username = ?",
            (username,)
        )
        return self._convertToDataFrame(result)

    def userExists(self, username: str) -> bool:
        result = self._execute(
            "SELECT username FROM users WHERE username = ?",
            (username,)
        )
        return len(result.rows) > 0

    # ─── Group Info ───────────────────────────────────────────────────────────

    def addGroupInfo(self, group_name: str, created_by: str,
                     start_date: str, end_date: str, location: str, description: str = None) -> int:
        result = self._execute(
            """INSERT INTO group_info (
                group_name, created_by, creation_date, modified_date,
                start_date, end_date, location, description, status_flag
            ) VALUES (?, ?, date('now'), date('now'), ?, ?, ?, ?, 'inactive')""",
            (group_name, created_by, start_date, end_date, location, description)
        )
        return result.last_insert_rowid

    def updateGroupInfo(self, group_id: int, field_updates: GroupUpdates) -> None:
        allowed_fields = ("group_name", "description", "start_date", "end_date", "location")
        updates = []
        values = []

        for field, value in field_updates.items():
            if field in allowed_fields and value is not None:
                updates.append(f"{field} = ?")
                values.append(value)

        if not updates:
            return

        values.append(group_id)
        query = f"UPDATE group_info SET {', '.join(updates)}, modified_date = date('now') WHERE group_id = ?"
        self._execute(query, tuple(values))

    def getGroupData(self, group_id: int) -> pd.DataFrame:
        result = self._execute(
            """SELECT group_name, description, status_flag, modified_date,
               created_by, creation_date, start_date, end_date, location
               FROM group_info WHERE group_id = ?""",
            (group_id,)
        )
        return self._convertToDataFrame(result)

    def groupExists(self, group_id: int) -> bool:
        result = self._execute(
            "SELECT COUNT(*) FROM group_info WHERE group_id = ?",
            (group_id,)
        )
        return result.rows[0][0] > 0

    def deleteGroup(self, group_id: int) -> None:
        self._execute(
            "UPDATE group_info SET status_flag = 'deleted', modified_date = date('now') WHERE group_id = ?",
            (group_id,)
        )

    # ─── Group Members ────────────────────────────────────────────────────────

    def userIsMember(self, group_id: int, username: str) -> bool:
        result = self._execute(
            "SELECT COUNT(*) FROM group_members WHERE group_id = ? AND username = ? AND status_flag = 'active'",
            (group_id, username)
        )
        return result.rows[0][0] > 0

    def userIsGroupOwner(self, group_id: int, username: str) -> bool:
        result = self._execute(
            "SELECT is_owner FROM group_members WHERE group_id = ? AND username = ?",
            (group_id, username)
        )
        if len(result.rows) == 0:
            return False
        return bool(result.rows[0][0])

    def userWasFormerGroupMember(self, group_id: int, username: str) -> bool:
        result = self._execute(
            "SELECT username FROM group_members WHERE group_id = ? AND username = ?",
            (group_id, username)
        )
        return len(result.rows) > 0

    def addMemberToGroup(self, group_id: int, username: str, is_owner: bool = False) -> None:
        if self.userWasFormerGroupMember(group_id=group_id, username=username):
            self._execute(
                "UPDATE group_members SET status_flag = 'active' WHERE group_id = ? AND username = ?",
                (group_id, username)
            )
        else:
            self._execute(
                "INSERT INTO group_members (group_id, username, date_joined, is_owner) VALUES (?, ?, date('now'), ?)",
                (group_id, username, int(is_owner))
            )

    def getGroupMembers(self, group_id: int) -> pd.DataFrame:
        result = self._execute(
            """SELECT u.username, u.email, u.profile_picture, u.verified, g.is_owner
               FROM group_members g
               LEFT JOIN users u ON u.username = g.username
               WHERE g.group_id = ?""",
            (group_id,)
        )
        return self._convertToDataFrame(result)

    def removeMember(self, group_id: int, username: str) -> None:
        self._execute(
            "UPDATE group_members SET status_flag = 'inactive' WHERE group_id = ? AND username = ?",
            (group_id, username)
        )

    def changeGroupOwner(self, group_id: int, new_owner: str = None) -> None:
        if new_owner is not None and not self.userIsMember(group_id=group_id, username=new_owner):
            return

        # Remove current owner flag
        self._execute(
            "UPDATE group_members SET is_owner = FALSE WHERE group_id = ? AND is_owner = TRUE",
            (group_id,)
        )

        if new_owner is None:
            # Automatically assign oldest member (alphabetical tiebreak) as new owner
            self._execute(
                """UPDATE group_members SET is_owner = TRUE
                   WHERE username = (
                       SELECT username FROM group_members
                       WHERE group_id = ? AND status_flag = 'active'
                       ORDER BY date_joined ASC, username ASC
                       LIMIT 1
                   )""",
                (group_id,)
            )
        else:
            self._execute(
                "UPDATE group_members SET is_owner = TRUE WHERE group_id = ? AND username = ?",
                (group_id, new_owner)
            )

    def getUsersGroups(self, username: str) -> pd.DataFrame:
        result = self._execute(
            """SELECT g.group_name, g.group_id, g.description, g.status_flag,
                      g.created_by, g.modified_date, g.creation_date,
                      g.start_date, g.end_date, g.location
               FROM group_info g
               JOIN group_members m ON g.group_id = m.group_id
               WHERE m.username = ?
               AND NOT (g.status_flag = 'deleted' OR g.status_flag = 'removed')""",
            (username,)
        )
        return self._convertToDataFrame(result)

    # ─── Events ───────────────────────────────────────────────────────────────

    def addEvent(self, event_name: str, description: str, group_id: int,
                 uploaded_by: str, currency: str, paid_by: str) -> int:
        result = self._execute(
            """INSERT INTO events (event_name, description, group_id, uploaded_by,
               upload_date, currency, paid_by)
               VALUES (?, ?, ?, ?, date('now'), ?, ?)""",
            (event_name, description, group_id, uploaded_by, currency, paid_by)
        )
        return result.last_insert_rowid

    def getEventDetails(self, event_id: int, as_json: bool = False) -> pd.DataFrame | dict:
        result = self._execute(
            """SELECT e.event_name, e.description, e.paid_by, e.currency, e.event_id,
                      t.transaction_id, t.item_name, SUM(t.amount_due) AS amount_due,
                      t.category, GROUP_CONCAT(t.owed_by) AS owed_by, t.subgroup_id
               FROM transactions t
               INNER JOIN events e ON e.event_id = t.event_id
               WHERE e.event_id = ?
               AND (t.status_flag != 'deleted' OR t.status_flag IS NULL)
               GROUP BY t.subgroup_id""",
            (event_id,)
        )
        data = self._convertToDataFrame(result)
        if data is False:
            return {} if as_json else data

        data["owed_by"] = data["owed_by"].apply(lambda x: x.split(",") if x else [])

        if as_json:
            json_data = data.loc[0, ["event_name", "description", "paid_by", "currency", "event_id"]].to_dict()
            transaction_data = data.loc[:, ["transaction_id", "subgroup_id", "owed_by", "amount_due", "item_name", "category"]].to_dict(orient="records")
            json_data["transactions"] = transaction_data
            return json_data

        return data

    def getEvent(self, event_id: int) -> pd.DataFrame:
        result = self._execute(
            """SELECT event_name, description, event_id, group_id, uploaded_by,
                      upload_date, modified_date, currency, status_flag, paid_by
               FROM events
               WHERE event_id = ? AND (status_flag != 'deleted' OR status_flag IS NULL)""",
            (event_id,)
        )
        return self._convertToDataFrame(result)

    def getEventSummary(self, group_id: int) -> pd.DataFrame:
        result = self._execute(
            """SELECT e.event_id, e.event_name, e.upload_date,
                      SUM(t.amount_due) AS total, e.paid_by
               FROM events e
               LEFT JOIN transactions t ON e.event_id = t.event_id
               WHERE e.group_id = ?
               AND (e.status_flag != 'deleted' OR e.status_flag IS NULL)
               AND (t.status_flag != 'deleted' OR t.status_flag IS NULL)
               GROUP BY e.event_id""",
            (group_id,)
        )
        return self._convertToDataFrame(result)

    def updateEvent(self, event_id: int, event_updates: EventUpdates) -> None:
        allowed_fields = ("event_name", "description", "currency", "paid_by")
        updates = []
        values = []

        if len(event_updates) == 0:
            return

        for field, value in event_updates.items():
            if field in allowed_fields and value is not None:
                updates.append(f"{field} = ?")
                values.append(value)

        if not updates:
            return

        values.append(event_id)
        query = f"UPDATE events SET {', '.join(updates)}, modified_date = date('now') WHERE event_id = ?"
        self._execute(query, tuple(values))

    def deleteEvent(self, event_id: int) -> None:
        self._execute(
            "UPDATE events SET status_flag = 'deleted', modified_date = date('now') WHERE event_id = ?",
            (event_id,)
        )

    # ─── Transactions ─────────────────────────────────────────────────────────

    def addTransaction(self, group_id: int, event_id: int, item_name: str,
                       amount_due: float, owed_by: str, category: str, subgroup: int = None) -> int:
        result = self._execute(
            """INSERT INTO transactions (group_id, event_id, item_name, amount_due, owed_by, category, modified_date)
               VALUES (?, ?, ?, ?, ?, ?, date('now'))""",
            (group_id, event_id, item_name, amount_due, owed_by, category)
        )
        new_id = result.last_insert_rowid
        id = subgroup if subgroup is not None else new_id

        self._execute(
            "UPDATE transactions SET subgroup_id = ? WHERE transaction_id = ?",
            (id, new_id)
        )
        return new_id

    def getTransactions(self, by: IdCategories, id_value: int, aggr: bool = False) -> pd.DataFrame:
        if aggr:
            query = f"""SELECT transaction_id, subgroup_id, modified_date, item_name,
                               category, amount_due, GROUP_CONCAT(owed_by) AS owed_by
                        FROM transactions
                        WHERE {by} = ?
                        AND (status_flag != 'deleted' OR status_flag IS NULL)
                        GROUP BY subgroup_id"""
        else:
            query = f"""SELECT transaction_id, subgroup_id, modified_date, item_name,
                               category, amount_due, owed_by
                        FROM transactions
                        WHERE {by} = ?
                        AND (status_flag != 'deleted' OR status_flag IS NULL)"""

        result = self._execute(query, (id_value,))
        return self._convertToDataFrame(result)

    def updateTransaction(self, subgroup_id: int, update_info: TransactionUpdates) -> None:
        allowed_fields = ("item_name", "amount_due", "category")
        updates = []
        values = []

        for field, value in update_info.items():
            if field in allowed_fields and value is not None:
                updates.append(f"{field} = ?")
                values.append(value)

        if not updates:
            return

        values.extend([subgroup_id, update_info["owed_by"]])
        query = f"""UPDATE transactions
                    SET {', '.join(updates)}, modified_date = date('now')
                    WHERE subgroup_id = ? AND owed_by = ?"""
        self._execute(query, tuple(values))

    def deleteTransaction(self, by: IdCategories, id_value: int, owed_by: str = None) -> None:
        if owed_by is not None:
            self._execute(
                f"UPDATE transactions SET status_flag = 'deleted', modified_date = date('now') WHERE {by} = ? AND owed_by = ?",
                (id_value, owed_by)
            )
        else:
            self._execute(
                f"UPDATE transactions SET status_flag = 'deleted', modified_date = date('now') WHERE {by} = ?",
                (id_value,)
            )

    def getTotalSpent(self, group_id: int) -> int:
        result = self._execute(
            "SELECT SUM(amount_due) AS total FROM transactions WHERE group_id = ?",
            (group_id,)
        )
        return result.rows[0][0]

    def getGroupOwedSummary(self, group_id: int) -> pd.DataFrame:
        result = self._execute(
            """SELECT e.paid_by, t.owed_by, SUM(t.amount_due) AS amount_due
               FROM transactions t
               INNER JOIN events e ON e.event_id = t.event_id
               WHERE e.group_id = ?
               AND (t.status_flag != 'deleted' OR t.status_flag IS NULL)
               GROUP BY t.owed_by, e.paid_by""",
            (group_id,)
        )
        return self._convertToDataFrame(result)

    # ─── Invites ──────────────────────────────────────────────────────────────

    def alreadyInvited(self, group_id: int, invitee: str) -> bool:
        result = self._execute(
            "SELECT group_id FROM pending_invites WHERE group_id = ? AND invitee = ? AND status_flag IN ('accepted', 'pending')",
            (group_id, invitee)
        )
        return len(result.rows) > 0

    def createInvite(self, invitee: str, invited_by: str, group_id: int) -> None:
        self._execute(
            """INSERT INTO pending_invites (invitee, invited_by, group_id, status_flag, created_date)
               VALUES (?, ?, ?, 'pending', date('now'))""",
            (invitee, invited_by, group_id)
        )

    def updateInvite(self, group_id: int, invitee: str, status: inviteStatus) -> None:
        self._execute(
            "UPDATE pending_invites SET status_flag = ? WHERE group_id = ? AND invitee = ?",
            (status, group_id, invitee)
        )

    def deleteInvite(self, invitee: str, group_id: int, revoked_by: str) -> None:
        self._execute(
            "UPDATE pending_invites SET status_flag = 'revoked', revoked_by = ? WHERE invitee = ? AND group_id = ?",
            (revoked_by, invitee, group_id)
        )

    def getPendingInvitesByGroup(self, group_id: int) -> pd.DataFrame:
        result = self._execute(
            "SELECT invite_id, invitee, invited_by, created_date FROM pending_invites WHERE status_flag = 'pending' AND group_id = ?",
            (group_id,)
        )
        return self._convertToDataFrame(result)

    def getPendingInvitesByUser(self, username: str) -> pd.DataFrame:
        result = self._execute(
            """SELECT i.invite_id, i.invited_by, i.created_date,
                      g.group_name, g.description, g.status_flag,
                      g.start_date, g.end_date, g.location
               FROM pending_invites i
               LEFT JOIN group_info g ON i.group_id = g.group_id
               WHERE invitee = ?""",
            (username,)
        )
        return self._convertToDataFrame(result)


if __name__ == "__main__":
    session = DatabaseManager()
    print(session.getGroupMembers(group_id=6))
