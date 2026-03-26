from typing import Literal, TypedDict, List
from pydantic import BaseModel

class GroupUpdates(TypedDict, total=False):
    group_name: str
    description: str
    start_date: str
    end_date: str
    location: str
    status_flag: str

class TransactionUpdates(TypedDict, total=False):
    item_name: str
    amount_due: float
    category: str
    owed_by: str

class EventUpdates(TypedDict, total=False):
    event_name: str
    description: str
    currency: str
    paid_by: str

class TransactionData(TypedDict):
    item_name: str
    category: str
    amount_due: float
    owed_by: List[str]

class CreateGroupRequest(BaseModel):
    group_name: str
    start: str
    end: str
    location: str
    description: str = None

class TransactionInput(BaseModel):
    item_name: str
    amount_due: float
    category: str
    owed_by: List[str]

class CreateEventRequest(BaseModel):
    event_name: str
    description: str
    currency: str
    paid_by: str = None
    transactions: List[TransactionInput]

class InviteRequest(BaseModel):
    username: str