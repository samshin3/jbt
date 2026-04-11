import { useEffect, useState } from 'react'
import { getGroups, getGroupMembers, getGroupBalance, createGroup, getTotalSpent, getEventsSummary } from '../api/api'

// ─── API functions used in this file ───────────────────────────────────────
// getGroups()                          → returns array of group objects
// getGroupMembers(groupId)             → returns array of member objects
// getGroupBalance(groupId)             → returns dict { username: amount }
// createGroup(name, start, end, location, description) → returns { group_id }
// getTotalSpent(groupId)               → returns total spent amount
// getEventsSummary(groupId)            → returns array of event summary objects
// ───────────────────────────────────────────────────────────────────────────

function Avatar({ name, size = 32 }) {
  const colors = ['#FFB347', '#3199c2', '#DDA0DD', '#98FB98', '#F08080']
  const color = colors[name.charCodeAt(0) % colors.length]
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%', background: color,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: size * 0.38, fontWeight: '600', color: '#fff', flexShrink: 0
    }}>
      {name[0].toUpperCase()}
    </div>
  )
}

function Sidebar({ groups, selectedGroup, onSelectGroup, onGroupCreated }) {
  const [showCreate, setShowCreate] = useState(false)
  const [newGroup, setNewGroup] = useState({ name: '', start: '', end: '', location: '', description: '' })
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState(null)

  async function handleCreate() {
    if (!newGroup.name.trim()) return
    setCreating(true)
    setCreateError(null)
    try {
      await createGroup(newGroup.name, newGroup.start, newGroup.end, newGroup.location, newGroup.description)
      setNewGroup({ name: '', start: '', end: '', location: '', description: '' })
      setShowCreate(false)
      onGroupCreated()
    } catch (err) {
      setCreateError("Failed to create group")
    } finally {
      setCreating(false)
    }
  }

  return (
    <div style={{
      width: '200px', minHeight: '100vh', background: 'white',
      borderRight: '1px solid #ebebeb', padding: '24px 16px',
      display: 'flex', flexDirection: 'column', flexShrink: 0
    }}>
      <p style={{ fontSize: '11px', fontWeight: '700', color: '#aaa', letterSpacing: '1px', textTransform: 'uppercase', margin: '0 0 16px 8px' }}>
        Groups
      </p>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {groups.map(group => (
          <button
            key={group.group_id}
            onClick={() => onSelectGroup(group)}
            style={{
              display: 'flex', alignItems: 'center', gap: '10px',
              padding: '10px 12px', borderRadius: '10px', border: 'none',
              background: selectedGroup?.group_id === group.group_id ? '#f0f0f0' : 'transparent',
              cursor: 'pointer', textAlign: 'left', width: '100%', transition: 'background 0.15s'
            }}
            onMouseEnter={e => { if (selectedGroup?.group_id !== group.group_id) e.currentTarget.style.background = '#f8f8f8' }}
            onMouseLeave={e => { if (selectedGroup?.group_id !== group.group_id) e.currentTarget.style.background = 'transparent' }}
          >
            <div style={{
              width: '8px', height: '8px', borderRadius: '50%',
              background: group.status_flag === 'active' ? '#4CAF50' : '#ccc', flexShrink: 0
            }} />
            <span style={{
              fontSize: '13px', fontWeight: selectedGroup?.group_id === group.group_id ? '600' : '400',
              color: '#222', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
            }}>
              {group.group_name}
            </span>
          </button>
        ))}
      </div>

      <button
        onClick={() => setShowCreate(!showCreate)}
        style={{
          marginTop: '16px', padding: '10px 16px', border: '1.5px solid #e5e5e5',
          borderRadius: '10px', background: 'white', cursor: 'pointer',
          fontSize: '13px', fontWeight: '500', color: '#444', width: '100%', transition: 'all 0.15s'
        }}
        onMouseEnter={e => e.currentTarget.style.background = '#f5f5f5'}
        onMouseLeave={e => e.currentTarget.style.background = 'white'}
      >
        + Create Group
      </button>

      {showCreate && (
        <div style={{ marginTop: '12px', padding: '16px', background: '#f8f8f8', borderRadius: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {[
            { label: 'Group Name', key: 'name', type: 'text' },
            { label: 'Start Date', key: 'start', type: 'date' },
            { label: 'End Date', key: 'end', type: 'date' },
            { label: 'Location', key: 'location', type: 'text' },
            { label: 'Description', key: 'description', type: 'text' },
          ].map(field => (
            <div key={field.key}>
              <label style={{ fontSize: '11px', color: '#888', display: 'block', marginBottom: '3px' }}>{field.label}</label>
              <input
                type={field.type}
                value={newGroup[field.key]}
                onChange={e => setNewGroup({ ...newGroup, [field.key]: e.target.value })}
                style={{
                  width: '100%', padding: '7px 10px', border: '1px solid #e0e0e0',
                  borderRadius: '6px', fontSize: '12px', boxSizing: 'border-box', outline: 'none'
                }}
              />
            </div>
          ))}
          {createError && <p style={{ color: '#c62828', fontSize: '12px' }}>{createError}</p>}
          <button
            onClick={handleCreate}
            disabled={creating}
            style={{
              marginTop: '4px', padding: '8px', background: creating ? '#888' : '#111',
              color: 'white', border: 'none', borderRadius: '6px',
              fontSize: '12px', fontWeight: '600', cursor: creating ? 'not-allowed' : 'pointer'
            }}
          >
            {creating ? 'Creating...' : 'Create'}
          </button>
        </div>
      )}
    </div>
  )
}

export default function Dashboard({ currentUser, selectedGroup: initialGroup, onSelectGroup, onOpenSettings, onAddTransaction, onEditEvent, onCheckInvites, refreshKey }) {
  const [groups, setGroups] = useState([])
  const [selectedGroup, setSelectedGroup] = useState(null)
  const [members, setMembers] = useState([])
  const [events, setEvents] = useState([])
  const [balances, setBalances] = useState({})
  const [summaryUser, setSummaryUser] = useState(currentUser)
  const [loadingGroups, setLoadingGroups] = useState(true)
  const [loadingGroupData, setLoadingGroupData] = useState(false)
  const [error, setError] = useState(null)
  const [totalSpent, setTotal] = useState([])
  const [showCreate, setShowCreate] = useState(false)

  // Fetch groups on mount and when refreshKey changes
  useEffect(() => {
    fetchGroups()
  }, [refreshKey])

  // Fetch group detail whenever selected group changes
  useEffect(() => {
    if (!selectedGroup) return
    setSummaryUser(currentUser)
    fetchGroupData(selectedGroup.group_id)
  }, [selectedGroup?.group_id, refreshKey])

  async function fetchGroups() {
    setLoadingGroups(true)
    setError(null)
    try {
      const data = await getGroups()
      setGroups(data)
      if (data.length > 0) {
        setSelectedGroup(data[0])
        onSelectGroup(data[0])
      }
    } catch (err) {
      setError("Failed to load groups")
    } finally {
      setLoadingGroups(false)
    }
  }

  async function fetchGroupData(groupId) {
    setLoadingGroupData(true)
    try {
      const [memberData, txData, balanceData, totalData] = await Promise.all([
        getGroupMembers(groupId),
        getEventsSummary(groupId),
        getGroupBalance(groupId),
        getTotalSpent(groupId)
      ])
      setMembers(memberData)
      setEvents(txData)
      setBalances(balanceData)
      setTotal(totalData)
    } catch (err) {
      setError("Failed to load group data")
    } finally {
      setLoadingGroupData(false)
    }
  }

  const formatDate = (d) => {
    if (!d) return ''
    const [year, month, day] = d.split("-").map(Number)
    const date = new Date(year, month - 1, day)
    return date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
  }

  if (loadingGroups) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', fontFamily: "'DM Sans', sans-serif", color: '#888' }}>
      Loading...
    </div>
  )

  if (error) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', fontFamily: "'DM Sans', sans-serif", color: '#c62828' }}>
      {error}
    </div>
  )

  if (!selectedGroup) return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f5f4f0' }}>
      <Sidebar
        groups={groups}
        selectedGroup={selectedGroup}
        onSelectGroup={(group) => {
          setSelectedGroup(group)
          onSelectGroup(group)
        }}
        onGroupCreated={fetchGroups}
      />
      <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', fontFamily: "'DM Sans', sans-serif", color: '#888' }}>
        No groups found. Create one to get started.
      </span>
    </div>
    
  )
  

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f5f4f0' }}>
      <Sidebar
        groups={groups}
        selectedGroup={selectedGroup}
        onSelectGroup={(group) => {
          setSelectedGroup(group)
          onSelectGroup(group)
        }}
        onGroupCreated={fetchGroups}
      />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Top bar */}
        <div style={{
          background: 'white', borderBottom: '1px solid #ebebeb',
          padding: '14px 28px', display: 'flex', alignItems: 'center', justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ fontSize: '15px', fontWeight: '700', color: '#111' }}>Japan Budget Tracker</span>
            <span style={{ fontSize: '13px', color: '#aaa' }}>›</span>
            <span style={{ fontSize: '13px', color: '#888' }}>Groups</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button style={{
              padding: '8px 18px', background: '#111', color: 'white', border: 'none',
              borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer'
            }}>Pending Invites</button>

            <button style={{
              padding: '8px 18px', background: '#111', color: 'white', border: 'none',
              borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer'
            }}>Share</button>
            <Avatar name={currentUser} size={34} />
          </div>
        </div>

        <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '20px', opacity: loadingGroupData ? 0.5 : 1, transition: 'opacity 0.2s' }}>

          {/* Group header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
              <div style={{ width: '80px', height: '80px', borderRadius: '12px', background: '#e8e8e8', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '28px' }}>
                ✈️
              </div>
              <div>
                <h1 style={{ margin: 0, fontSize: '28px', fontWeight: '700', letterSpacing: '-0.5px' }}>{selectedGroup.group_name}</h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: selectedGroup.status_flag === 'active' ? '#4CAF50' : '#ccc' }} />
                  <span style={{ fontSize: '13px', color: '#555', textTransform: 'capitalize' }}>{selectedGroup.status_flag || 'Active'}</span>
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={onOpenSettings}
                style={{ padding: '10px 20px', border: '1.5px solid #e0e0e0', borderRadius: '10px', background: 'white', cursor: 'pointer', fontSize: '13px', fontWeight: '500', transition: 'all 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.background = '#f5f5f5'}
                onMouseLeave={e => e.currentTarget.style.background = 'white'}
              >
                Group Settings
              </button>
              <button
                onClick={onAddTransaction}
                style={{ padding: '10px 20px', border: '1.5px solid #e0e0e0', borderRadius: '10px', background: 'white', cursor: 'pointer', fontSize: '13px', fontWeight: '500', transition: 'all 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.background = '#f5f5f5'}
                onMouseLeave={e => e.currentTarget.style.background = 'white'}
              >
                Add Transaction
              </button>
            </div>
          </div>

          {/* Stats row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div style={{ background: 'white', borderRadius: '14px', padding: '24px', border: '1px solid #ebebeb' }}>
              <p style={{ margin: '0 0 8px', fontSize: '12px', fontWeight: '600', color: '#aaa', letterSpacing: '0.5px', textTransform: 'uppercase' }}>Total Spent</p>
              <p style={{ margin: 0, fontSize: '32px', fontWeight: '700', letterSpacing: '-1px' }}>
                ¥ {totalSpent.toLocaleString()}
              </p>
            </div>
            <div style={{ background: 'white', borderRadius: '14px', padding: '24px', border: '1px solid #ebebeb' }}>
              <p style={{ margin: '0 0 8px', fontSize: '12px', fontWeight: '600', color: '#aaa', letterSpacing: '0.5px', textTransform: 'uppercase' }}>Trip Period</p>
              <p style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>
                {formatDate(selectedGroup.start_date)} — {formatDate(selectedGroup.end_date)}
              </p>
            </div>
          </div>

          {/* Summary + Members row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '16px' }}>
            {/* Summary table */}
            <div style={{ background: 'white', borderRadius: '14px', padding: '24px', border: '1px solid #ebebeb' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
                <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '700' }}>Summary</h2>
                <select
                  value={summaryUser}
                  onChange={e => setSummaryUser(e.target.value)}
                  style={{ padding: '6px 12px', border: '1.5px solid #e0e0e0', borderRadius: '8px', fontSize: '13px', fontWeight: '500', background: 'white', cursor: 'pointer', outline: 'none' }}
                >
                  {members.map(m => (
                    <option key={m.username} value={m.username}>{m.username}</option>
                  ))}
                </select>
              </div>
              <div style={{ borderTop: '1px solid #f0f0f0' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
                  <span style={{ fontSize: '12px', fontWeight: '600', color: '#aaa' }}>MEMBER NAME</span>
                  <span style={{ fontSize: '12px', fontWeight: '600', color: '#aaa' }}>EMAIL</span>
                  <span style={{ fontSize: '12px', fontWeight: '600', color: '#aaa', textAlign: 'right' }}>AMOUNT DUE/OWED</span>
                </div>
                {members.filter(m => m.username !== summaryUser).map(member => {
                  const amount = balances.filter(bal => bal.owed_by === summaryUser && bal.paid_by === member.username)[0]?.amount || 0
                  return (
                    <div key={member.username} style={{
                      display: 'grid', gridTemplateColumns: '1fr 1fr auto',
                      padding: '16px 0', borderBottom: '1px solid #f8f8f8', alignItems: 'center'
                    }}>
                      <span style={{ fontSize: '14px', fontWeight: '500' }}>{member.username}</span>
                      <span style={{ fontSize: '13px', color: '#888' }}>{member.email}</span>
                      <span style={{ fontSize: '14px', fontWeight: '600', textAlign: 'right', color: amount >= 0 ? '#2e7d32' : '#c62828' }}>
                        {amount >= 0 ? '+' : ''}{amount}
                      </span>
                    </div>
                  )
                })}
                {members.length === 0 && (
                  <p style={{ padding: '20px 0', color: '#aaa', fontSize: '13px' }}>No members yet.</p>
                )}
              </div>
            </div>

            {/* Group Members */}
            <div style={{ background: 'white', borderRadius: '14px', padding: '24px', border: '1px solid #ebebeb' }}>
              <h2 style={{ margin: '0 0 20px', fontSize: '16px', fontWeight: '700' }}>Group Members</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {members.map(member => (
                  <div key={member.username} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <Avatar name={member.username} size={38} />
                    <div>
                      <p style={{ margin: 0, fontSize: '13px', fontWeight: '600' }}>
                        {member.username} {Boolean(member.is_owner) && <span style={{ color: '#888', fontWeight: '400' }}>(Owner)</span>}
                      </p>
                      <p style={{ margin: 0, fontSize: '12px', color: '#aaa' }}>{member.email}</p>
                    </div>
                  </div>
                ))}
              </div>
              <button style={{
                marginTop: '20px', width: '100%', padding: '10px', background: '#111',
                color: 'white', border: 'none', borderRadius: '10px',
                fontSize: '13px', fontWeight: '600', cursor: 'pointer'
              }}>
                Invite
              </button>
            </div>
          </div>

          {/* Recent Events */}
          <div style={{ background: 'white', borderRadius: '14px', padding: '24px', border: '1px solid #ebebeb' }}>
            <h2 style={{ margin: '0 0 20px', fontSize: '16px', fontWeight: '700' }}>Recent Events</h2>
            <div style={{ borderTop: '1px solid #f0f0f0' }}>
              {/* Table header */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr auto auto auto auto', padding: '10px 0', borderBottom: '1px solid #f0f0f0', gap: '16px' }}>
                <span style={{ fontSize: '12px', fontWeight: '600', color: '#aaa' }}>EVENT NAME</span>
                <span style={{ fontSize: '12px', fontWeight: '600', color: '#aaa', textAlign: 'right' }}>DATE ADDED</span>
                <span style={{ fontSize: '12px', fontWeight: '600', color: '#aaa', textAlign: 'right' }}>TOTAL</span>
                <span style={{ fontSize: '12px', fontWeight: '600', color: '#aaa', textAlign: 'right' }}>PAID BY</span>
                <span style={{ fontSize: '12px', fontWeight: '600', color: '#aaa', textAlign: 'right' }}></span>
              </div>

              {events.length === 0 && (
                <p style={{ padding: '20px 0', color: '#aaa', fontSize: '13px' }}>No events yet.</p>
              )}

              {events.map((tx, i) => (
                <div
                  key={tx.event_id || i}
                  style={{
                    display: 'grid', gridTemplateColumns: '1fr auto auto auto auto auto',
                    padding: '12px 0', borderBottom: '1px solid #f8f8f8',
                    gap: '16px', alignItems: 'center'
                  }}
                >
                  
                  <span style={{ fontSize: '14px', fontWeight: '500'}}>{tx.event_name}</span>
                  <div>
                    <button style={{
                        padding: '8px 18px', background: '#d9d9d9', color: '#444', border: '#b6b6b6',
                        borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: 'pointer'
                        }}      onClick = {()=>onEditEvent(tx, selectedGroup)}
                      onMouseEnter={e => { e.currentTarget.style.background = '#eaeaea'; e.currentTarget.style.color = 'black'; e.currentTarget.style.borderColor = '#bfbfbf' }}
                      onMouseLeave={e => { e.currentTarget.style.background = '#d9d9d9'; e.currentTarget.style.color = '#444'; e.currentTarget.style.borderColor = '#b6b6b6' }}
                      >Edit Event
                    </button>
                  </div>
                  <span style={{ fontSize: '13px', color: '#888', textAlign: 'right' }}>{tx.upload_date || tx.date}</span>
                  <span style={{ fontSize: '14px', fontWeight: '600', textAlign: 'right' }}>{tx.total}</span>
                  <span style={{ fontSize: '13px', color: '#555', textAlign: 'right' }}>{tx.paid_by}</span>
                  
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
