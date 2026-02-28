import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/', label: '대시보드', icon: '📊' },
  { to: '/attendance', label: '출석 관리', icon: '✅' },
  { to: '/enrollment', label: '수업등록', icon: '📋' },
  { to: '/class-groups', label: '수업반 관리', icon: '📚' },
  { to: '/students', label: '학생 관리', icon: '👩‍🎓' },
  { to: '/payments', label: '수업료 관리', icon: '💰' },
  { to: '/makeup-lessons', label: '보충수업', icon: '📝' },
]

export default function Sidebar() {
  return (
    <aside className="w-60 border-r border-border bg-sidebar min-h-screen p-4 flex flex-col">
      <h1 className="text-lg font-bold mb-6 px-2">수학공부방</h1>
      <nav className="flex flex-col gap-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-sidebar-accent text-sidebar-accent-foreground font-medium'
                  : 'text-sidebar-foreground hover:bg-sidebar-accent/50'
              }`
            }
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
