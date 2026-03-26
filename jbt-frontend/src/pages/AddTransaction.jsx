import { useEffect, useState } from 'react'
import { getGroupMembers, createEvent } from '../api/api'

// ─── API functions used in this file ───────────────────────────────────────
// getGroupMembers(groupId)             → returns array of member objects
// createEvent(groupId, {              → submits the event and transactions
//   event_name, description,
//   currency, paid_by,
//   transactions: [{ item_name, amount_due, category, owed_by }]
// })                                  → returns { status: "ok" }
// ───────────────────────────────────────────────────────────────────────────

const CATEGORIES = ['Food', 'Transport', 'Shopping', 'Accommodation', 'Entertainment', 'General']
const CURRENCIES = ['JPY', 'USD', 'CAD', 'EUR', 'GBP', 'KRW']

const emptyRow = () => ({ item_name: '', amount_due: '', category: 'General', owed_by: [] })

export default function AddTransaction({ group, currentUser, onBack, onSubmit }) {
  const [members, setMembers] = useState([])
  const [loadingMembers, setLoadingMembers] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const [form, setForm] = useState({
    event_name: '',
    description: '',
    paid_by: currentUser || '',
    currency: 'JPY',
  })
  const [rows, setRows] = useState([emptyRow()])

  useEffect(() => {
    if (!group) return
    async function fetchMembers() {
      try {
        const data = await getGroupMembers(group.group_id)
        setMembers(data)
        // Default paid_by to currentUser if they're in the group
        const match = data.find(m => m === currentUser)
        if (match) setForm(f => ({ ...f, paid_by: match.username }))
      } catch (err) {
        setError("Failed to load members")
      } finally {
        setLoadingMembers(false)
      }
    }
    fetchMembers()
  }, [group?.group_id])

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

  async function handleSubmit() {
    if (!form.event_name.trim()) {
      setError("Event name is required")
      return
    }
    const validRows = rows.filter(r => r.item_name.trim() && r.amount_due)
    if (validRows.length === 0) {
      setError("Add at least one transaction item")
      return
    }

    setSubmitting(true)
    setError(null)
    try {
      console.log(validRows[0].owed_by)
      await createEvent(group.group_id, {
        event_name: form.event_name,
        description: form.description,
        currency: form.currency,
        paid_by: form.paid_by,
        transactions: validRows.map(r => ({
          item_name: r.item_name,
          amount_due: parseFloat(r.amount_due),
          category: r.category,
          owed_by: r.owed_by || form.paid_by,  // uses first selected, fallback to paid_by
        }))
      })
      onSubmit()  // navigate back and trigger dashboard refresh
    } catch (err) {
      setError("Failed to submit transaction")
    } finally {
      setSubmitting(false)
    }
  }

  const memberNames = members.map(m => m.username)

  return (
    <div style={{ minHeight: '100vh', background: '#f5f4f0', padding: '32px', fontFamily: "'DM Sans', sans-serif" }}>
      <button
        onClick={onBack}
        style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '13px', color: '#888', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '6px', padding: 0 }}
      >
        ← Back to Dashboard
      </button>

      <div style={{ maxWidth: '720px', background: 'white', borderRadius: '16px', padding: '32px', border: '1px solid #ebebeb' }}>
        {/* Tab row */}
        <div style={{ display: 'flex', gap: '10px', marginBottom: '28px' }}>
          <div style={{ padding: '8px 16px', borderRadius: '8px', border: '1.5px solid #111', background: '#111', color: 'white', fontSize: '13px', fontWeight: '500' }}>
            {group?.group_name || 'Group'}
          </div>
          <div style={{ padding: '8px 16px', borderRadius: '8px', border: '1.5px solid #e5e5e5', background: 'white', color: '#444', fontSize: '13px', fontWeight: '500', cursor: 'pointer' }}>
            Create with Receipt
          </div>
        </div>

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
            {loadingMembers ? (
              <span style={{ fontSize: '13px', color: '#aaa' }}>Loading...</span>
            ) : (
              <select
                value={form.paid_by}
                onChange={e => setForm({ ...form, paid_by: e.target.value })}
                style={{ padding: '10px 14px', border: '1.5px solid #e5e5e5', borderRadius: '8px', fontSize: '13px', outline: 'none', background: '#fafafa', cursor: 'pointer' }}
              >
                {memberNames.map(name => <option key={name} value={name}>{name}</option>)}
              </select>
            )}
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
            <div key={index} style={{ display: 'grid', gridTemplateColumns: '1fr 90px 120px 1fr 36px', gap: '10px', padding: '8px 0', borderBottom: '1px solid #f8f8f8', alignItems: 'start' }}>
              <input
                placeholder="Item name"
                value={row.item_name}
                onChange={e => updateRow(index, 'item_name', e.target.value)}
                style={{ padding: '8px 12px', border: '1.5px solid #e5e5e5', borderRadius: '7px', fontSize: '13px', outline: 'none', background: '#fafafa' }}
              />
              <input
                placeholder="0"
                type="number"
                value={row.amount_due}
                onChange={e => updateRow(index, 'amount_due', e.target.value)}
                style={{ padding: '8px 10px', border: '1.5px solid #e5e5e5', borderRadius: '7px', fontSize: '13px', outline: 'none', background: '#fafafa', width: '100%', boxSizing: 'border-box' }}
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
                  style={{
                    padding: '4px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '500',
                    border: '1.5px solid #e0e0e0', background: 'white', color: '#666', cursor: 'pointer'
                  }}
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

        {error && <p style={{ color: '#c62828', fontSize: '13px', marginTop: '16px' }}>{error}</p>}

        <button
          onClick={handleSubmit}
          disabled={submitting}
          style={{
            marginTop: '28px', width: '100%', padding: '14px',
            background: submitting ? '#888' : '#111', color: 'white', border: 'none',
            borderRadius: '10px', fontSize: '14px', fontWeight: '700',
            cursor: submitting ? 'not-allowed' : 'pointer', letterSpacing: '0.2px'
          }}
        >
          {submitting ? 'Submitting...' : 'Submit'}
        </button>
      </div>
    </div>
  )
}
