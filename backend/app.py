from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv
from db_manager import DatabaseManager
from user_session import *
from data_validation import CreateGroupRequest, TransactionInput, CreateEventRequest, InviteRequest, GroupUpdates, TransactionUpdates, EventUpdateRequest
import os

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "login")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = [
        "https://jbt-cyan.vercel.app",   # your frontend
        "http://localhost:5173",          # local dev
    ],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
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
    expiry = datetime.now(UTC) + timedelta(hours = 24)
    return jwt.encode({"sub": username, "exp": expiry}, SECRET_KEY, algorithm = ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code = 401, detail = "Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code = 401, detail = "Invalid token")

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"url_set": "none"}

@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db = Depends(get_db)):
    user_df = db.getUserData(form.username)
    if user_df is None or len(user_df) == 0:
        raise HTTPException(status_code = 401, detail = "User not found")
    token = create_token(form.username)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/get_groups")
def get_groups_route(username: str = Depends(get_current_user), db = Depends(get_db)):
    return getGroups(db, username).to_dict(orient = "records")


@app.post("/create_group")
def create_group_route(req: CreateGroupRequest, username: str = Depends(get_current_user), db = Depends(get_db)):
    group_id = createGroup(db, username, req.group_name, req.start, req.end, req.location, req.description)
    if not group_id:
        raise HTTPException(status_code = 400, detail = "Invalid date range")
    return {"group_id": group_id}


@app.get("/get_members/{group_id}")
def get_members_route(group_id: int, username: str = Depends(get_current_user), db = Depends(get_db)):
    members = db.getGroupMembers(group_id)
    
    return members.to_dict(orient = "records")


@app.post("/invite_member/{group_id}")
def invite_member_route(group_id: int, req: InviteRequest, username: str = Depends(get_current_user), db = Depends(get_db)):
    user_df = db.getUserData(req.username)
    if user_df is None or len(user_df) == 0:
        raise HTTPException(status_code = 404, detail = "User not found")
    
    inviteMembersToGroup(db = db, group_id = group_id, inviter = username, invitee = req.username)

    return {"status": "ok"}

@app.get("/get_event_summary/{group_id}")
def get_event_summary_route(group_id: int, username: str = Depends(get_current_user), db = Depends(get_db)):
    event_summary = db.getEventSummary(group_id)
    if event_summary is False or event_summary is None:
        return []
    return event_summary.to_dict(orient = "records")


@app.get("/get_transactions/{event_id}")
def get_transactions_route(event_id: int, username: str = Depends(get_current_user), db = Depends(get_db)):
    df = db.getTransactions(by = "event_id", id_value = event_id)
    if df is False or df is None:
        return []
    return df.to_dict(orient = "records")


@app.get("/get_group_balance/{group_id}")
def get_group_balance_route(group_id: int, username: str = Depends(get_current_user), db = Depends(get_db)):
    return summarizeAmountDue(db = db, group_id = group_id)


@app.post("/create_event/{group_id}")
def create_event_route(group_id: int, req: CreateEventRequest, username: str = Depends(get_current_user), db = Depends(get_db)):
    transactions = [t.dict() for t in req.transactions]
    createEvent(
        db = db,
        username = username,
        group_id = group_id,
        event_name = req.event_name,
        event_desc = req.description,
        currency = req.currency,
        transactions = transactions,
        paid_by = req.paid_by
    )
    return {"status": "ok"}

@app.get("/get_total_spent/{group_id}")
def get_total_route(group_id: int, username: str = Depends(get_current_user), db = Depends(get_db)):
    results = db.getTotalSpent(group_id = group_id)
    if results is False or results is None:
        return 0
    return results

@app.patch("/update_group_info/{group_id}")
def update_group_info_route(group_id: int, req: GroupUpdates, username: str = Depends(get_current_user), db = Depends(get_db)):
    updateGroup(db = db, group_id = group_id, updates = req)
    return {"status": "ok"}

@app.delete("/delete_group/{group_id}")
def delete_group_route(group_id: int, username: str = Depends(get_current_user), db = Depends(get_db)):
    deleteGroup(db = db, group_id = group_id)
    return {"status": "ok"}

@app.get("/get_event_details/{event_id}")
def get_event_details_route(event_id: int, username: str = Depends(get_current_user), db = Depends(get_db)):
    results = db.getEventDetails(event_id = event_id, as_json = True)
    if results is False or results is None:
        return 0
    return results

@app.patch("/update_event/{event_id}")
def update_event_route(event_id: int, req: EventUpdateRequest, username: str = Depends(get_current_user), db = Depends(get_db)):
    updateEventFull(db = db, group_id = req["group_id"], event_id = event_id, event_edits = req["event_updates"], transaction_edits = req["transaction_updates"])
    return {"status": "ok"}

@app.delete("/delete_event/{event_id}")
def delete_event_route(event_id: int, username: str = Depends(get_current_user), db = Depends(get_db)):
    deleteEvent(db = db, event_id = event_id)
    return {"status": "ok"}
    
