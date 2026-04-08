import { useEffect, useState } from 'react'
import { getGroupMembers, getEventDetails, updateEvent, deleteEvent } from '../api/api'

// ─── API functions used in this file ────────────────────────────────────────
// getGroupMembers(groupId)   → [{ username, email, is_owner }, ...]
// getEventDetails(eventId)   → { event_id, event_name, paid_by, currency, description,
//                               transactions: [{ transaction_id, subgroup_id, item_name,
//                                               category, amount_due, owed_by[] }] }
// updateEvent(payload)       → { status: "ok" }
//   payload: {
//     group_id: int,
//     event_updates: { event_name?, description?, currency?, paid_by? },
//     transaction_updates: [
//       { subgroup_id, action: "delete" },
//       { subgroup_id, action: "update", transaction_data: { item_name, category, amount_due, owed_by } },
//       { action: "new", transaction_data: { item_name, category, amount_due, owed_by } }
//     ]
//   }
// ────────────────────────────────────────────────────────────────────────────

const CATEGORIES = ['Food', 'Transport', 'Shopping', 'Accommodation', 'Entertainment', 'General', 'Testing']
const CURRENCIES = ['JPY', 'USD', 'CAD', 'EUR', 'GBP', 'KRW']

const emptyRow = () => ({
  transaction_id: null,
  subgroup_id: null,    // null = new row not yet in DB
  item_name: '',
  amount_due: '',
  category: 'General',
  owed_by: []
})

export default function EditEvent({ group, currentUser, event, onBack, onDelete, onSubmit }) {
  const [members, setMembers] = useState([])
  const [loadingMembers, setLoadingMembers] = useState(true)
  const [loadingEvent, setLoadingEvent] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const [form, setForm] = useState({
    event_name: '',
    description: '',
    paid_by: '',
    currency: 'JPY',
  })
  const [originalForm, setOriginalForm] = useState(null)

  const [rows, setRows] = useState([])
  const [originalRows, setOriginalRows] = useState([])

  useEffect(() => {
    if (!group || !event) return
    fetchMembers()
    fetchEventData()
  }, [event?.event_id])

  async function fetchMembers() {
    setLoadingMembers(true)
    try {
      const data = await getGroupMembers(group.group_id)
      setMembers(data)
    } catch (err) {
      setError("Failed to load members")
    } finally {
      setLoadingMembers(false)
    }
  }

  async function fetchEventData() {
    setLoadingEvent(true)
    try {
      const data = await getEventDetails(event.event_id)

      const formData = {
        event_name: data.event_name || '',
        description: data.description || '',
        paid_by: data.paid_by || currentUser,
        currency: data.currency || 'JPY',
      }
      setForm(formData)
      setOriginalForm(formData)

      const existingRows = data.transactions.map(tx => ({
        transaction_id: tx.transaction_id,
        subgroup_id: tx.subgroup_id,
        item_name: tx.item_name,
        amount_due: tx.amount_due,
        category: tx.category,
        owed_by: tx.owed_by || []
      }))
      setRows(existingRows)
      // Deep copy so original is never mutated
      setOriginalRows(existingRows.map(r => ({ ...r, owed_by: [...r.owed_by] })))
    } catch (err) {
      setError("Failed to load event data")
    } finally {
      setLoadingEvent(false)
    }
  }

  function updateRow(index, field, value) {
    setRows(rows.map((r, i) => i === index ? { ...r, [field]: value } : r))
  }

  function toggleOwedBy(index, name) {
    const current = rows[index].owed_by
    const updated = current.includes(name)
      ? current.filter(n => n !== name)
      : [...current, name]
    updateRow(index, 'owed_by', updated)
  }

  function selectAllOwedBy(index) {
    const allNames = members.map(m => m.username)
    const allSelected = allNames.every(n => rows[index].owed_by.includes(n))
    updateRow(index, 'owed_by', allSelected ? [] : allNames)
  }

  function addRow() {
    setRows([...rows, emptyRow()])
  }

  function removeRow(index) {
    if (rows.length === 1) return
    setRows(rows.filter((_, i) => i !== index))
  }

  function rowHasChanged(row) {
    const original = originalRows.find(o => o.subgroup_id === row.subgroup_id)
    if (!original) return true
    return (
      row.item_name         !== original.item_name  ||
      String(row.amount_due) !== String(original.amount_due) ||
      row.category          !== original.category   ||
      JSON.stringify([...row.owed_by].sort()) !== JSON.stringify([...original.owed_by].sort())
    )
  }

  function buildEventUpdates() {
    if (!originalForm) return {}
    const updates = {}
    if (form.event_name  !== originalForm.event_name)  updates.event_name  = form.event_name
    if (form.description !== originalForm.description) updates.description = form.description
    if (form.currency    !== originalForm.currency)    updates.currency    = form.currency
    if (form.paid_by     !== originalForm.paid_by)     updates.paid_by     = form.paid_by
    return updates
  }

  function buildTransactionUpdates() {
    const updates = []

    // Deleted rows — existed originally but no longer in rows
    originalRows.forEach(original => {
      const stillExists = rows.find(r => r.subgroup_id === original.subgroup_id)
      if (!stillExists) {
        updates.push({
          subgroup_id: original.subgroup_id,
          action: "delete"
        })
      }
    })

    // Updated rows — exist in both but values changed
    rows.forEach(row => {
      if (row.subgroup_id !== null && rowHasChanged(row)) {
        updates.push({
          subgroup_id: row.subgroup_id,
          action: "update",
          transaction_data: {
            item_name: row.item_name,
            category: row.category,
            amount_due: parseFloat(row.amount_due),
            owed_by: row.owed_by
          }
        })
      }
    })

    // New rows — subgroup_id is null
    rows.forEach(row => {
      if (row.subgroup_id === null && row.item_name.trim() && row.amount_due) {
        updates.push({
          action: "new",
          transaction_data: {
            item_name: row.item_name,
            category: row.category,
            amount_due: parseFloat(row.amount_due),
            owed_by: row.owed_by
          }
        })
      }
    })

    return updates
  }

  async function handleSubmit() {
    if (!form.event_name.trim()) {
      setError("Event name is required")
      return
    }
    const group_id = group.group_id
    const event_updates = buildEventUpdates()
    const transaction_updates = buildTransactionUpdates()

    if (Object.keys(event_updates).length === 0 && transaction_updates.length === 0) {
      onBack()
      return
    }

    const payload = {
      group_id,
      event_updates,
      transaction_updates
    }
    
    setSubmitting(true)
    setError(null)
    try {
      await updateEvent(payload, event.event_id)
      onSubmit()
    } catch (err) {
      setError("Failed to save changes")
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete() {
    const confirmation = confirm("Are you sure about that?")
    
    if (!confirmation) return
    
    try {
      await deleteEvent(event.event_id)
      onDelete()
    } catch (err) {
      setError("Could not delete group")
    } finally {
      setDeleting(true)
    }

  }

  const memberNames = members.map(m => m.username)
  const isLoading = loadingMembers || loadingEvent

  return (
    <div style={{ minHeight: '100vh', background: '#f5f4f0', padding: '32px', fontFamily: "'DM Sans', sans-serif" }}>
      <button
        onClick={onBack}
        style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '13px', color: '#888', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '6px', padding: 0 }}
      >
        ← Back to Dashboard
      </button>

      <div style={{ maxWidth: '720px', background: 'white', borderRadius: '16px', padding: '32px', border: '1px solid #ebebeb' }}>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px' }}>
          <div style={{ display: 'flex', gap: '10px' }}>
            <div style={{ padding: '8px 16px', borderRadius: '8px', border: '1.5px solid #111', background: '#111', color: 'white', fontSize: '13px', fontWeight: '500' }}>
              {group?.group_name || 'Group'}
            </div>
            <button onClick={handleDelete}
              style={{ padding: '8px 16px', borderRadius: '8px', border: '1.5px solid #111', cursor: 'pointer', background: '#111', color: 'white', fontSize: '13px', fontWeight: '500' }}
              disabled = { deleting || submitting || isLoading }
            >
              DELETE EVENT
            </button>
          </div>
          <span style={{ fontSize: '12px', color: '#aaa', fontWeight: '500' }}>Editing event</span>
        </div>

        {isLoading ? (
          <p style={{ color: '#aaa', fontSize: '13px' }}>Loading event data...</p>
        ) : (
          <>
            {/* Form fields */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '28px' }}>
              {[
                { label: 'Event Name:', key: 'event_name', type: 'text' },
                { label: 'Description:', key: 'description', type: 'text' },
              ].map(field => (
                <div key={field.key} style={{ display: 'grid', gridTemplateColumns: '130px 1fr', alignItems: 'center', gap: '16px' }}>
                  <label style={{ fontSize: '14px', fontWeight: '600' }}>{field.label}</label>
                  <input
                    type={field.type}
                    value={form[field.key]}
                    onChange={e => setForm({ ...form, [field.key]: e.target.value })}
                    style={{ padding: '10px 14px', border: '1.5px solid #e5e5e5', borderRadius: '8px', fontSize: '13px', outline: 'none', background: '#fafafa', width: '100%', boxSizing: 'border-box' }}
                    onFocus={e => e.target.style.borderColor = '#111'}
                    onBlur={e => e.target.style.borderColor = '#e5e5e5'}
                  />
                </div>
              ))}

              <div style={{ display: 'grid', gridTemplateColumns: '130px 1fr', alignItems: 'center', gap: '16px' }}>
                <label style={{ fontSize: '14px', fontWeight: '600' }}>Paid by:</label>
                <select
                  value={form.paid_by}
                  onChange={e => setForm({ ...form, paid_by: e.target.value })}
                  style={{ padding: '10px 14px', border: '1.5px solid #e5e5e5', borderRadius: '8px', fontSize: '13px', outline: 'none', background: '#fafafa', cursor: 'pointer' }}
                >
                  {memberNames.map(name => <option key={name} value={name}>{name}</option>)}
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '130px 1fr', alignItems: 'center', gap: '16px' }}>
                <label style={{ fontSize: '14px', fontWeight: '600' }}>Currency:</label>
                <select
                  value={form.currency}
                  onChange={e => setForm({ ...form, currency: e.target.value })}
                  style={{ padding: '10px 14px', border: '1.5px solid #e5e5e5', borderRadius: '8px', fontSize: '13px', outline: 'none', background: '#fafafa', cursor: 'pointer' }}
                >
                  {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            </div>

            {/* Transactions table */}
            <div>
              <p style={{ fontSize: '14px', fontWeight: '700', margin: '0 0 12px' }}>Transactions</p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 90px 120px 1fr 36px', gap: '10px', padding: '8px 0', borderBottom: '1px solid #f0f0f0', marginBottom: '4px' }}>
                {['Item Name', 'Total', 'Category', 'Owed By', ''].map((h, i) => (
                  <span key={i} style={{ fontSize: '11px', fontWeight: '700', color: '#aaa', letterSpacing: '0.5px' }}>{h}</span>
                ))}
              </div>

              {rows.map((row, index) => (
                <div
                  key={row.subgroup_id ?? `new-${index}`}
                  style={{
                    display: 'grid', gridTemplateColumns: '1fr 90px 120px 1fr 36px',
                    gap: '10px', padding: '8px 0 8px 8px', borderBottom: '1px solid #f8f8f8',
                    alignItems: 'start',
                    // Green left border for new rows so user can tell them apart
                    borderLeft: row.subgroup_id === null ? '3px solid #4CAF50' : '3px solid transparent',
                  }}
                >
                  <input
                    placeholder="Item name"
                    value={row.item_name}
                    onChange={e => updateRow(index, 'item_name', e.target.value)}
                    style={{ padding: '8px 12px', border: '1.5px solid #e5e5e5', borderRadius: '7px', fontSize: '13px', outline: 'none', background: '#fafafa' }}
                    onFocus={e => e.target.style.borderColor = '#111'}
                    onBlur={e => e.target.style.borderColor = '#e5e5e5'}
                  />
                  <input
                    placeholder="0"
                    type="number"
                    value={row.amount_due}
                    onChange={e => updateRow(index, 'amount_due', e.target.value)}
                    style={{ padding: '8px 10px', border: '1.5px solid #e5e5e5', borderRadius: '7px', fontSize: '13px', outline: 'none', background: '#fafafa', width: '100%', boxSizing: 'border-box' }}
                    onFocus={e => e.target.style.borderColor = '#111'}
                    onBlur={e => e.target.style.borderColor = '#e5e5e5'}
                  />
                  <select
                    value={row.category}
                    onChange={e => updateRow(index, 'category', e.target.value)}
                    style={{ padding: '8px 10px', border: '1.5px solid #e5e5e5', borderRadius: '7px', fontSize: '13px', outline: 'none', background: '#fafafa', cursor: 'pointer' }}
                  >
                    {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>

                  {/* Owed By chips */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                    <button
                      onClick={() => selectAllOwedBy(index)}
                      style={{ padding: '4px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '500', border: '1.5px solid #e0e0e0', background: 'white', color: '#666', cursor: 'pointer' }}
                    >
                      All
                    </button>
                    {memberNames.map(name => (
                      <button
                        key={name}
                        onClick={() => toggleOwedBy(index, name)}
                        style={{
                          padding: '4px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '500',
                          border: '1.5px solid',
                          borderColor: row.owed_by.includes(name) ? '#111' : '#e0e0e0',
                          background: row.owed_by.includes(name) ? '#111' : 'white',
                          color: row.owed_by.includes(name) ? 'white' : '#666',
                          cursor: 'pointer', transition: 'all 0.12s'
                        }}
                      >
                        {name}
                      </button>
                    ))}
                  </div>

                  <button
                    onClick={() => removeRow(index)}
                    style={{ width: '30px', height: '30px', borderRadius: '6px', border: '1px solid #e5e5e5', background: 'white', cursor: 'pointer', fontSize: '16px', color: '#aaa', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                  >
                    ×
                  </button>
                </div>
              ))}

              <button
                onClick={addRow}
                style={{ marginTop: '12px', padding: '8px 16px', border: '1.5px dashed #ccc', borderRadius: '8px', background: 'transparent', cursor: 'pointer', fontSize: '13px', color: '#888', fontWeight: '500', transition: 'all 0.15s' }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = '#888'; e.currentTarget.style.color = '#444' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = '#ccc'; e.currentTarget.style.color = '#888' }}
              >
                + Add Row
              </button>
            </div>
          </>
        )}

        {error && <p style={{ color: '#c62828', fontSize: '13px', marginTop: '16px' }}>{error}</p>}

        <button
          onClick={handleSubmit}
          disabled={submitting || isLoading}
          style={{
            marginTop: '28px', width: '100%', padding: '14px',
            background: submitting || isLoading ? '#888' : '#111',
            color: 'white', border: 'none', borderRadius: '10px',
            fontSize: '14px', fontWeight: '700',
            cursor: submitting || isLoading ? 'not-allowed' : 'pointer',
            letterSpacing: '0.2px'
          }}
        >
          {submitting ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  )
}
