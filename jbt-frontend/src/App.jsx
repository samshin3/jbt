import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import GroupSettings from './pages/GroupSettings'
import AddTransaction from './pages/AddTransaction'
import Login from './pages/Login'
import './App.css'

export default function App() {
  const [currentUser, setCurrentUser] = useState(null)
  const [activePage, setActivePage] = useState('dashboard')
  const [selectedGroup, setSelectedGroup] = useState(null)

  if (!currentUser) {
    return <Login onLogin={(user) => setCurrentUser(user)} />
  }

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif", minHeight: '100vh', background: '#f5f4f0' }}>
      {activePage === 'dashboard' && (
        <Dashboard
          currentUser={currentUser}
          selectedGroup={selectedGroup}
          onSelectGroup={setSelectedGroup}
          onOpenSettings={() => setActivePage('settings')}
          onAddTransaction={() => setActivePage('add-transaction')}
        />
      )}
      {activePage === 'settings' && (
        <GroupSettings
          group={selectedGroup}
          currentUser={currentUser}
          onBack={() => setActivePage('dashboard')}
        />
      )}
      {activePage === 'add-transaction' && (
        <AddTransaction
          group={selectedGroup}
          currentUser={currentUser}
          onBack={() => setActivePage('dashboard')}
          onSubmit={() => setActivePage('dashboard')}
        />
      )}
    </div>
  )
}
