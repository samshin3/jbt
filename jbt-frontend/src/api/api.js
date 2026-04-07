const DEV = false
const BASE_URL = DEV ? "http://127.0.0.1:8000" : "https://jbt-backend.vercel.app"

// ─── Auth helper ─────────────────────────────────────────────────────────────
function authHeaders() {
  const token = localStorage.getItem("token")
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  }
}

function handleUnauthorized(res) {
  if (res.status === 401) {
    localStorage.removeItem("token")
    window.location.href = "/"
  }
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export async function login(username) {
  const res = await fetch(`${BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `username=${username}&password=placeholder`
  })
  if (!res.ok) throw new Error("Login failed")
  const data = await res.json()
  localStorage.setItem("token", data.access_token)
}

export function logout() {
  localStorage.removeItem("token")
}

// ─── Groups ───────────────────────────────────────────────────────────────────

// Returns: [{ group_id, group_name, status_flag, start_date, end_date, location, description, created_by }, ...]
export async function getGroups() {
  const res = await fetch(`${BASE_URL}/get_groups`, {
    headers: authHeaders()
  })
  handleUnauthorized(res)
  if (!res.ok) throw new Error("Failed to fetch groups")
  return await res.json()
}

// Returns: { group_id }
export async function createGroup(groupName, start, end, location, description) {
  const res = await fetch(`${BASE_URL}/create_group`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ group_name: groupName, start, end, location, description })
  })
  handleUnauthorized(res)
  if (!res.ok) throw new Error("Failed to create group")
  return await res.json()
}

export async function deleteGroup(groupId) {
  const res = await fetch(`${BASE_URL}/delete_group/${groupId}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({})
  })
  handleUnauthorized(res)
  if (!res.ok) throw new Error("Failed to delete group")
  return await res.json()
}

export async function updateGroup(groupId, form) {
  console.log(form)
  const res = await fetch(`${BASE_URL}/update_group_info/${groupId}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(form)
  })
  handleUnauthorized(res)
  if (!res.ok) throw new Error("Failed to update group")
  return await res.json()
}

// ─── Members ──────────────────────────────────────────────────────────────────

// Returns: [{ username, email, is_owner }, ...]
export async function getGroupMembers(groupId) {
  const res = await fetch(`${BASE_URL}/get_members/${groupId}`, {
    headers: authHeaders()
  })
  handleUnauthorized(res)
  if (!res.ok) throw new Error("Failed to fetch members")
  return await res.json()
}

// Returns: { status: "ok" }
export async function inviteMember(groupId, username) {
  const res = await fetch(`${BASE_URL}/invite_member/${groupId}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ username })
  })
  handleUnauthorized(res)
  if (!res.ok) throw new Error("Failed to invite member")
  return await res.json()
}

// ─── Transactions ─────────────────────────────────────────────────────────────

// Returns: [{ transaction_id, item_name, category, amount_due, owed_by, modified_date }, ...]
export async function getGroupTransactions(eventId) {
  const res = await fetch(`${BASE_URL}/get_transactions/${eventId}`, {
    headers: authHeaders()
  })
  handleUnauthorized(res)
  if (!res.ok) throw new Error("Failed to fetch transactions")
  return await res.json()
}

// Returns: { status: "ok" }
// transactions: [{ item_name, amount_due, category, owed_by: [username, ...] }]
export async function createEvent(groupId, { event_name, description, currency, paid_by, transactions }) {
  const res = await fetch(`${BASE_URL}/create_event/${groupId}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ event_name, description, currency, paid_by, transactions })
  })
  handleUnauthorized(res)
  if (!res.ok) throw new Error("Failed to create event")
  return await res.json()
}

export async function getEventDetails(eventId) {
  const res = await fetch(`${BASE_URL}/get_event_details/${eventId}`, {
    headers: authHeaders()
  })
  handleUnauthorized(res)
  if (!res.ok) throw new Error("Failed to get Event Details")
    return await res.json()
}

export async function updateEvent(payload, event_id) {
  const res = await fetch(`${BASE_URL}/update_event/${event_id}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(payload)
  })
  handleUnauthorized(res)
  if (!res.ok) throw new Error("Failed to update event")
  return await res.json()
}

// ─── Balance ──────────────────────────────────────────────────────────────────

// Returns: { "Michelle": 300, "Joanna": -102, ... }
// Positive = they owe you, Negative = you owe them
export async function getGroupBalance(groupId) {
  const res = await fetch(`${BASE_URL}/get_group_balance/${groupId}`, {
    headers: authHeaders()
  })
  handleUnauthorized(res)
  if (!res.ok) throw new Error("Failed to fetch balance")
  return await res.json()
}


export async function getTotalSpent(groupId) {
  const res = await fetch(`${BASE_URL}/get_total_spent/${groupId}`, {
    headers: authHeaders()
  })
  handleUnauthorized(res)
  if (!res.ok) throw new Error("Failed to get total")
    return await res.json()
}

export async function getEventsSummary(groupId) {
  const res = await fetch(`${BASE_URL}/get_event_summary/${groupId}`, {
    headers: authHeaders()
  })
  handleUnauthorized(res)
  if (!res.ok) throw new Error("Failed to get Events Summary")
    return await res.json()
}

