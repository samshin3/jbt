class UserNotInGroupError(Exception):
    def __init__(self, users: list[str], group_id: int):
        self.users = users
        self.group_id = group_id
        super().__init__(f"The following users: {users} are not members of group {group_id}")