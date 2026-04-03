import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import GroupSettings from './pages/GroupSettings'
import AddTransaction from './pages/AddTransaction'
import EditEvent from './pages/EditEvent'
import Login from './pages/Login'
import './App.css'

export default function App() {
  const [currentUser, setCurrentUser] = useState(null)
  const [activePage, setActivePage] = useState('dashboard')
  const [selectedGroup, setSelectedGroup] = useState(null)
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  function triggerRefresh() {
    setRefreshKey(k => k + 1)
  }

  if (!currentUser) {
    return <Login onLogin={(user) => setCurrentUser(user)} />
  }

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif", minHeight: '100vh', background: '#f5f4f0' }}>
      {activePage === 'dashboard' && (
        <Dashboard
          currentUser={currentUser}
          selectedGroup={selectedGroup}
          refreshKey={refreshKey}
          onSelectGroup={(group) => setSelectedGroup(group)}
          onOpenSettings={() => setActivePage('settings')}
          onAddTransaction={() => setActivePage('add-transaction')}
          onEditEvent={(event, group) => {
            setSelectedEvent(event)
            setSelectedGroup(group)
            setActivePage('edit-event')
          }}
        />
      )}
      {activePage === 'settings' && (
        <GroupSettings
          group={selectedGroup}
          currentUser={currentUser}
          onBack={() => {
            triggerRefresh()
            setActivePage('dashboard')
          }}
        />
      )}
      {activePage === 'add-transaction' && (
        <AddTransaction
          group={selectedGroup}
          currentUser={currentUser}
          onBack={() => setActivePage('dashboard')}
          onSubmit={() => {
            triggerRefresh()
            setActivePage('dashboard')
          }}
        />
      )}
      {activePage === 'edit-event' && (
        <EditEvent
          group={selectedGroup}
          currentUser={currentUser}
          event={selectedEvent}
          onBack={() => setActivePage('dashboard')}
          onSubmit={() => {
            triggerRefresh()
            setActivePage('dashboard')
          }}
        />
      )}
    </div>
  )
}
