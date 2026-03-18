from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv
from db_manager import DatabaseManager
from user_session import getGroups, createGroup, acceptInvite, createEvent, summarizeAmountDue
from pydantic import BaseModel
from typing import List, Literal
import os

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── DB Dependency ───────────────────────────────────────────────────────────
def get_db():
    db = DatabaseManager()
    try:
        yield db
    finally:
        db.close()

# ─── Auth ────────────────────────────────────────────────────────────────────
def create_token(username: str) -> str:
    expiry = datetime.now(UTC) + timedelta(hours=24)
    return jwt.encode({"sub": username, "exp": expiry}, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ─── Pydantic Models ─────────────────────────────────────────────────────────
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

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    user_df = db.getUserData(form.username)
    if user_df is None or len(user_df) == 0:
        raise HTTPException(status_code=401, detail="User not found")
    token = create_token(form.username)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/get_groups")
def get_groups_route(username: str = Depends(get_current_user), db=Depends(get_db)):
    return getGroups(db, username).to_dict(orient="records")


@app.post("/create_group")
def create_group_route(req: CreateGroupRequest, username: str = Depends(get_current_user), db=Depends(get_db)):
    group_id = createGroup(db, username, req.group_name, req.start, req.end, req.location, req.description)
    if not group_id:
        raise HTTPException(status_code=400, detail="Invalid date range")
    return {"group_id": group_id}


@app.get("/get_members/{group_id}")
def get_members_route(group_id: int, username: str = Depends(get_current_user), db=Depends(get_db)):
    members = db.getGroupMembers(group_id)
    result = []
    for member in members:
        user_df = db.getUserData(member)
        if user_df is not None and len(user_df) > 0:
            result.append({
                "username": member,
                "email": user_df["email"][0],
                "is_owner": False
            })
    return result


@app.post("/invite_member/{group_id}")
def invite_member_route(group_id: int, req: InviteRequest, username: str = Depends(get_current_user), db=Depends(get_db)):
    user_df = db.getUserData(req.username)
    if user_df is None or len(user_df) == 0:
        raise HTTPException(status_code=404, detail="User not found")
    acceptInvite(db, username, group_id, req.username)
    return {"status": "ok"}


@app.get("/get_transactions/{group_id}")
def get_transactions_route(group_id: int, username: str = Depends(get_current_user), db=Depends(get_db)):
    test = db.getTransactions(by="group_id", id_value=group_id)
    if test is False or test is None:
        return []
    return test


@app.get("/get_group_balance/{group_id}")
def get_group_balance_route(group_id: int, username: str = Depends(get_current_user), db=Depends(get_db)):
    return summarizeAmountDue(db=db, group_id=group_id, username=username)


@app.post("/create_event/{group_id}")
def create_event_route(group_id: int, req: CreateEventRequest, username: str = Depends(get_current_user), db=Depends(get_db)):
    transactions = [t.dict() for t in req.transactions]
    createEvent(
        db=db,
        username=username,
        group_id=group_id,
        event_name=req.event_name,
        event_desc=req.description,
        currency=req.currency,
        transactions=transactions,
        paid_by=req.paid_by
    )
    return {"status": "ok"}

@app.get("/get_total_spent/{group_id}")
def get_total_route(group_id: int, username: str = Depends(get_current_user), db = Depends(get_db)):
    return db.getTotalSpent(group_id = group_id)