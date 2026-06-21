import { useState } from 'react'
import { MessageCircle, MapPin } from 'lucide-react'
import './Sidebar.css'

type Tab = 'chat' | 'restaurants'

interface SidebarProps {
  active: Tab
  setActive: (t: Tab) => void
}

const NAV: { id: Tab; num: string; title: string; desc: string; Icon: typeof MessageCircle }[] = [
  { id: 'chat', num: '00', title: 'Chat', desc: 'Build your profile', Icon: MessageCircle },
  { id: 'restaurants', num: '01', title: 'Discover', desc: 'Matched restaurants', Icon: MapPin },
]

export default function Sidebar({ active, setActive }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-head">
        <span className="eyebrow">Index</span>
        <button
          className="collapse-btn"
          onClick={() => setCollapsed(!collapsed)}
          aria-label={collapsed ? 'Expand navigation' : 'Collapse navigation'}
        >
          {collapsed ? '›' : '‹'}
        </button>
      </div>

      <nav className="sidebar-nav">
        {NAV.map(({ id, num, title, desc, Icon }) => (
          <button
            key={id}
            className={`nav-item ${active === id ? 'active' : ''}`}
            onClick={() => setActive(id)}
          >
            <span className="nav-num">{num}</span>
            <span className="nav-body">
              <span className="nav-title">{title}</span>
              <span className="nav-desc">{desc}</span>
            </span>
            <Icon className="nav-icon" size={16} strokeWidth={1.6} />
          </button>
        ))}
      </nav>

      <div className="sidebar-foot">
        <span className="eyebrow">DietMate67</span>
        <span className="eyebrow sidebar-foot-dim">Est. 2026</span>
      </div>
    </aside>
  )
}
