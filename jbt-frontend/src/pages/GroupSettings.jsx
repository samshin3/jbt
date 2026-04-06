import { useEffect, useState } from 'react'
import { getGroupMembers, updateGroup, deleteGroup, inviteMember } from '../api/api'

// ─── API functions used in this file ───────────────────────────────────────
// getGroupMembers(groupId)                         → returns array of member objects
// updateGroup(groupId, { description, start, end, location }) → returns updated group
// deleteGroup(groupId)                             → deletes the group
// inviteMember(groupId, username)                  → invites a user to the group
// ───────────────────────────────────────────────────────────────────────────

function Avatar({ name, size = 32 }) {
  const colors = ['#FFB347', '#87CEEB', '#DDA0DD', '#98FB98', '#F08080']
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

export default function GroupSettings({ group, currentUser, onBack }) {
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [inviting, setInviting] = useState(false)
  const [inviteUsername, setInviteUsername] = useState('')
  const [showInvite, setShowInvite] = useState(false)
  const [error, setError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)

  const [form, setForm] = useState({
    description: group?.description || '',
    start: group?.start_date || '',
    end: group?.end_date || '',
    location: group?.location || '',
  })

  useEffect(() => {
    if (!group) return
    fetchMembers()
  }, [group?.group_id])

  async function fetchMembers() {
    setLoading(true)
    try {
      const data = await getGroupMembers(group.group_id)
      setMembers(data)
    } catch (err) {
      setError("Failed to load members")
    } finally {
      setLoading(false)
    }
  }

  async function handleSave() {
    setSaving(true)
    setError(null)
    setSuccessMsg(null)
    try {
      await updateGroup(group.group_id, form)
      setSuccessMsg("Changes saved!")
      setTimeout(() => setSuccessMsg(null), 3000)
    } catch (err) {
      setError("Failed to save changes")
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm(`Are you sure you want to delete "${group.group_name}"?`)) return
    try {
      await deleteGroup(group.group_id)
      onBack()
    } catch (err) {
      setError("Failed to delete group")
    }
  }

  async function handleInvite() {
    if (!inviteUsername.trim()) return
    setInviting(true)
    setError(null)
    try {
      await inviteMember(group.group_id, inviteUsername.trim())
      setInviteUsername('')
      setShowInvite(false)
      fetchMembers()  // re-fetch members after invite
    } catch (err) {
      setError("Failed to invite member. Check the username and try again.")
    } finally {
      setInviting(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f5f4f0', padding: '32px', fontFamily: "'DM Sans', sans-serif" }}>
      <button
        onClick={onBack}
        style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '13px', color: '#888', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '6px', padding: 0 }}
      >
        ← Back to Dashboard
      </button>

      <div style={{ maxWidth: '560px', background: 'white', borderRadius: '16px', padding: '32px', border: '1px solid #ebebeb' }}>
        {/* Tab label */}
        <div style={{ display: 'inline-block', padding: '8px 16px', background: '#f0f0f0', borderRadius: '8px', fontSize: '13px', fontWeight: '500', marginBottom: '24px' }}>
          {group?.group_name}
        </div>

        {/* Group header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '28px' }}>
          <div style={{ width: '80px', height: '80px', borderRadius: '12px', background: '#e8e8e8', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '28px' }}>
            ✈️
          </div>
          <div style={{ flex: 1 }}>
            <h2 style={{ margin: '0 0 12px', fontSize: '20px', fontWeight: '700' }}>{group?.group_name}</h2>
            <button
              onClick={handleDelete}
              style={{ padding: '8px 16px', border: '1.5px solid #ffcdd2', borderRadius: '8px', background: 'white', color: '#c62828', fontSize: '13px', fontWeight: '500', cursor: 'pointer' }}
            >
              Delete Group
            </button>
          </div>
        </div>

        {/* Form fields */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '28px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '110px 1fr', alignItems: 'center', gap: '12px' }}>
            <label style={{ fontSize: '14px', fontWeight: '600' }}>Description:</label>
            <input
              type="text"
              value={form.description}
              onChange={e => setForm({ ...form, description: e.target.value })}
              style={{ padding: '10px 14px', border: '1.5px solid #e5e5e5', borderRadius: '8px', fontSize: '13px', outline: 'none', background: '#fafafa' }}
              onFocus={e => e.target.style.borderColor = '#111'}
              onBlur={e => e.target.style.borderColor = '#e5e5e5'}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '110px 1fr', alignItems: 'center', gap: '12px' }}>
            <label style={{ fontSize: '14px', fontWeight: '600' }}>Trip Length:</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <input
                type="date"
                value={form.start}
                onChange={e => setForm({ ...form, start: e.target.value })}
                style={{ flex: 1, padding: '10px 12px', border: '1.5px solid #e5e5e5', borderRadius: '8px', fontSize: '13px', outline: 'none', background: '#fafafa' }}
              />
              <span style={{ color: '#888', fontWeight: '500', flexShrink: 0 }}>To</span>
              <input
                type="date"
                value={form.end}
                onChange={e => setForm({ ...form, end: e.target.value })}
                style={{ flex: 1, padding: '10px 12px', border: '1.5px solid #e5e5e5', borderRadius: '8px', fontSize: '13px', outline: 'none', background: '#fafafa' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '110px 1fr', alignItems: 'center', gap: '12px' }}>
            <label style={{ fontSize: '14px', fontWeight: '600' }}>Location:</label>
            <input
              type="text"
              value={form.location}
              onChange={e => setForm({ ...form, location: e.target.value })}
              style={{ padding: '10px 14px', border: '1.5px solid #e5e5e5', borderRadius: '8px', fontSize: '13px', outline: 'none', background: '#fafafa' }}
              onFocus={e => e.target.style.borderColor = '#111'}
              onBlur={e => e.target.style.borderColor = '#e5e5e5'}
            />
          </div>
        </div>

        {/* Manage Members */}
        <div style={{ border: '1px solid #ebebeb', borderRadius: '12px', padding: '20px', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <span style={{ fontSize: '14px', fontWeight: '600' }}>Manage Members</span>
            <button
              onClick={() => setShowInvite(!showInvite)}
              style={{ padding: '8px 16px', background: '#111', color: 'white', border: 'none', borderRadius: '8px', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }}
            >
              Invite
            </button>
          </div>

          {showInvite && (
            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
              <input
                type="text"
                placeholder="Enter username"
                value={inviteUsername}
                onChange={e => setInviteUsername(e.target.value)}
                style={{ flex: 1, padding: '8px 12px', border: '1.5px solid #e5e5e5', borderRadius: '8px', fontSize: '13px', outline: 'none' }}
              />
              <button
                onClick={handleInvite}
                disabled={inviting}
                style={{ padding: '8px 16px', background: inviting ? '#888' : '#111', color: 'white', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: '600', cursor: inviting ? 'not-allowed' : 'pointer' }}
              >
                {inviting ? '...' : 'Add'}
              </button>
            </div>
          )}

          {loading ? (
            <p style={{ color: '#aaa', fontSize: '13px' }}>Loading members...</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {members.map(member => (
                <div key={member.username} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <Avatar name={member.username} size={36} />
                  <div>
                    <p style={{ margin: 0, fontSize: '13px', fontWeight: '600' }}>
                      {member.username} {Boolean(member.is_owner) && <span style={{ color: '#888', fontWeight: '400' }}>(Owner)</span>}
                    </p>
                    <p style={{ margin: 0, fontSize: '12px', color: '#aaa' }}>{member.email}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {error && <p style={{ color: '#c62828', fontSize: '13px', marginBottom: '12px' }}>{error}</p>}
        {successMsg && <p style={{ color: '#2e7d32', fontSize: '13px', marginBottom: '12px' }}>{successMsg}</p>}

        <button
          onClick={handleSave}
          disabled={saving}
          style={{
            width: '100%', padding: '12px', background: saving ? '#888' : '#111',
            color: 'white', border: 'none', borderRadius: '10px',
            fontSize: '14px', fontWeight: '600', cursor: saving ? 'not-allowed' : 'pointer'
          }}
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  )
}
