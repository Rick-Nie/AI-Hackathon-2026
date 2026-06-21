import { useState } from 'react'
import { MessageCircle, MapPin } from 'lucide-react'
import './Sidebar.css'

type Tab = 'chat' | 'restaurants'

interface SidebarProps {
  active: Tab
  setActive: (t: Tab) => void
}

export default function Sidebar({ active, setActive }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <button className="collapse-btn" onClick={() => setCollapsed(!collapsed)}>
        {collapsed ? '›' : '‹'}
      </button>
      <div className="sidebar-buttons">
        <button
          className={`side-btn ${active === 'chat' ? 'active' : ''}`}
          onClick={() => setActive('chat')}
        >
          <MessageCircle />
          <span>Chat</span>
        </button>
        <button
          className={`side-btn ${active === 'restaurants' ? 'active' : ''}`}
          onClick={() => setActive('restaurants')}
        >
          <MapPin />
          <span>Restaurants</span>
        </button>
      </div>
    </div>
  )
}
