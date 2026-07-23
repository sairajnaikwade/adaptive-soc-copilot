import React from 'react'
import { motion } from 'framer-motion'
import {
  ShieldCheck, AlertTriangle, Users, Activity,
  LogOut, Shield, Bell, BarChart3, Settings
} from 'lucide-react'
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks'
import { logoutThunk } from '../store/authSlice'
import { useNavigate } from 'react-router-dom'

// ---- KPI Card ----
function KpiCard({ label, value, sub, color }: {
  label: string; value: string | number; sub?: string; color: string
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card flex flex-col gap-1"
    >
      <span className="text-soc-muted text-xs font-medium uppercase tracking-wider">{label}</span>
      <span className={`text-3xl font-bold ${color}`}>{value}</span>
      {sub && <span className="text-soc-muted text-xs">{sub}</span>}
    </motion.div>
  )
}

// ---- Sidebar ----
function Sidebar({ onLogout }: { onLogout: () => void }) {
  const navItems = [
    { icon: BarChart3, label: 'Dashboard', active: true },
    { icon: AlertTriangle, label: 'Threats' },
    { icon: Users, label: 'Monitored Accounts' },
    { icon: Activity, label: 'Events' },
    { icon: Shield, label: 'Rules & Responses' },
    { icon: Bell, label: 'Reports' },
    { icon: Settings, label: 'Settings' },
  ]

  return (
    <aside className="w-64 bg-soc-surface border-r border-soc-border flex flex-col">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-soc-border">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
          <ShieldCheck className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-soc-text leading-none">SOC CoPilot</p>
          <p className="text-[10px] text-soc-muted mt-0.5">Security Operations</p>
        </div>
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ icon: Icon, label, active }) => (
          <div key={label} className={active ? 'nav-item-active' : 'nav-item'}>
            <Icon className="w-4 h-4 flex-shrink-0" />
            <span className="text-sm font-medium">{label}</span>
            {label === 'Threats' && (
              <span className="ml-auto bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                3
              </span>
            )}
          </div>
        ))}
      </nav>

      {/* Logout */}
      <div className="px-3 py-4 border-t border-soc-border">
        <button
          onClick={onLogout}
          className="nav-item w-full text-left text-red-400 hover:text-red-300 hover:bg-red-900/20"
        >
          <LogOut className="w-4 h-4" />
          <span className="text-sm font-medium">Sign Out</span>
        </button>
      </div>
    </aside>
  )
}

// ---- Alert row ----
function AlertRow({ tier, account, score, time }: {
  tier: 'HIGH' | 'MEDIUM' | 'LOW'; account: string; score: number; time: string
}) {
  const badge = tier === 'HIGH' ? 'badge-high' : tier === 'MEDIUM' ? 'badge-medium' : 'badge-low'
  return (
    <div className="flex items-center gap-4 py-3 border-b border-soc-border/50 last:border-0">
      <span className={badge}>{tier}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-soc-text font-medium truncate">{account}</p>
        <p className="text-xs text-soc-muted">{time}</p>
      </div>
      <div className="text-right">
        <p className="text-sm font-mono text-soc-muted">Trust</p>
        <p className={`text-sm font-bold ${score < 40 ? 'text-red-400' : score < 70 ? 'text-amber-400' : 'text-emerald-400'}`}>
          {score}
        </p>
      </div>
    </div>
  )
}

// ---- Main Dashboard ----
export default function Dashboard() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { user } = useAppSelector((s) => s.auth)

  const handleLogout = async () => {
    await dispatch(logoutThunk())
    navigate('/login')
  }

  // Placeholder alerts for Week 1 UI
  const alerts = [
    { tier: 'HIGH' as const,   account: 'john.doe@acme.com',    score: 18, time: '2 min ago' },
    { tier: 'MEDIUM' as const, account: 'jane.smith@acme.com',  score: 52, time: '14 min ago' },
    { tier: 'HIGH' as const,   account: 'root@infra.acme.com',  score: 9,  time: '31 min ago' },
  ]

  return (
    <div className="flex h-screen bg-soc-bg overflow-hidden">
      <Sidebar onLogout={handleLogout} />

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {/* Top bar */}
        <header className="sticky top-0 z-10 bg-soc-surface/80 backdrop-blur border-b border-soc-border px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-soc-text">Security Overview</h1>
            <p className="text-xs text-soc-muted">Real-time threat monitoring dashboard</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-soc-bg rounded-lg px-3 py-1.5 border border-soc-border">
              <span className="threat-pulse" />
              <span className="text-xs text-soc-muted">Live</span>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-soc-text">{user?.full_name ?? 'Analyst'}</p>
              <p className="text-xs text-soc-muted capitalize">{user?.role}</p>
            </div>
          </div>
        </header>

        <div className="p-8 space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-4 gap-4">
            <KpiCard label="Active Threats"     value="3"   sub="↑ 1 from yesterday"     color="text-red-400" />
            <KpiCard label="Monitored Accounts" value="247" sub="Across all departments"  color="text-soc-accent" />
            <KpiCard label="Avg Trust Score"    value="78"  sub="↓ 3 pts from last week"  color="text-amber-400" />
            <KpiCard label="Honeypots Active"   value="1"   sub="1 attacker contained"    color="text-cyan-400" />
          </div>

          {/* Alerts + placeholder chart */}
          <div className="grid grid-cols-3 gap-4">
            {/* Recent alerts */}
            <div className="col-span-1 glass-card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold text-soc-text">Recent Alerts</h2>
                <span className="badge-high">3 open</span>
              </div>
              {alerts.map((a, i) => (
                <AlertRow key={i} {...a} />
              ))}
            </div>

            {/* Placeholder for threat timeline (Sprint 7) */}
            <div className="col-span-2 glass-card flex flex-col">
              <h2 className="text-sm font-semibold text-soc-text mb-4">Threat Timeline</h2>
              <div className="flex-1 flex items-center justify-center rounded-lg border border-dashed border-soc-border">
                <div className="text-center">
                  <BarChart3 className="w-10 h-10 text-soc-border mx-auto mb-2" />
                  <p className="text-soc-muted text-sm">Timeline chart — Sprint 7</p>
                  <p className="text-soc-border text-xs mt-1">Recharts integration coming soon</p>
                </div>
              </div>
            </div>
          </div>

          {/* System status */}
          <div className="glass-card">
            <h2 className="text-sm font-semibold text-soc-text mb-4">System Status — Week 1 Foundation</h2>
            <div className="grid grid-cols-4 gap-3 text-center text-xs">
              {[
                { name: 'FastAPI Backend',    status: 'online' },
                { name: 'PostgreSQL DB',      status: 'online' },
                { name: 'ML Pipeline',        status: 'sprint-3' },
                { name: 'SHAP Explainer',     status: 'sprint-4' },
              ].map(({ name, status }) => (
                <div key={name} className="bg-soc-bg rounded-lg p-3 border border-soc-border">
                  <div className={`w-2 h-2 rounded-full mx-auto mb-2 ${
                    status === 'online' ? 'bg-emerald-400' : 'bg-soc-border'
                  }`} />
                  <p className="text-soc-text font-medium">{name}</p>
                  <p className={`mt-0.5 ${status === 'online' ? 'text-emerald-400' : 'text-soc-muted'}`}>
                    {status === 'online' ? '● Online' : `⏳ ${status}`}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
