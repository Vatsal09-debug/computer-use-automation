import { useEffect, useState } from 'react'
import './App.css'

type View = 'overview' | 'members'

type Member = {
  id: string
  name: string
  initials: string
  savingsBalance: number
  accountNumber: string
  status: 'Active' | 'Restricted'
  branch: string
  lastActivity: string
}

const MEMBERS: Member[] = [
  {
    id: '12345',
    name: 'John Smith',
    initials: 'JS',
    savingsBalance: 4250,
    accountNumber: '•••• 4821',
    status: 'Active',
    branch: '0042',
    lastActivity: 'Today, 14:32',
  },
  {
    id: '67890',
    name: 'Sarah Johnson',
    initials: 'SJ',
    savingsBalance: 8125.5,
    accountNumber: '•••• 7194',
    status: 'Active',
    branch: '0018',
    lastActivity: 'Today, 13:18',
  },
]

function App() {
  const [view, setView] = useState<View>('overview')
  const [selectedMember, setSelectedMember] = useState<Member | null>(null)
  const [memberId, setMemberId] = useState('')
  const [error, setError] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [seconds, setSeconds] = useState(0)

  useEffect(() => {
    const timer = window.setInterval(() => {
      setSeconds((current) => current + 1)
    }, 1000)

    return () => window.clearInterval(timer)
  }, [])

  function formatTime(totalSeconds: number) {
    const hours = Math.floor(totalSeconds / 3600)
    const minutes = Math.floor((totalSeconds % 3600) / 60)
    const secs = totalSeconds % 60

    return [hours, minutes, secs]
      .map((value) => String(value).padStart(2, '0'))
      .join(':')
  }

  function openMembers() {
    setView('members')
    setSelectedMember(null)
    setError('')
  }

  function openOverview() {
    setView('overview')
    setSelectedMember(null)
    setError('')
  }

  function searchMember(id : string) {
    setError('')
    setIsSearching(true)

    window.setTimeout(() => {
      const foundMember = MEMBERS.find(
        (currentMember) => currentMember.id === id.trim(),
      )

      setIsSearching(false)

      if (!foundMember) {
        setSelectedMember(null)
        setError(
          'No member record was found for this identifier. Verify the member ID and try again.',
        )
        return
      }

      setMemberId(foundMember.id)
      setSelectedMember(foundMember)
    }, 450)
  }

  function openMember(member: Member) {
    setMemberId(member.id)
    setSelectedMember(member)
    setError('')
    setView('members')
  }

  function handleBackToMembers() {
    setSelectedMember(null)
    setError('')
  }

  return (
    <main className="northstar-app">
      <header className="topbar">
        <button
          type="button"
          className="brand"
          onClick={openOverview}
          aria-label="Northstar home"
        >
          <span className="brand-mark">N</span>

          <span className="brand-copy">
            <strong>Northstar</strong>
            <span>Banking Operations</span>
          </span>
        </button>

        <div className="topbar-center">
          <span className="live-dot" />
          <span>Core systems nominal</span>
          <span className="topbar-separator">/</span>
          <span>Secure session</span>
        </div>

        <div className="operator">
          <span className="operator-avatar">AO</span>

          <span className="operator-copy">
            <strong>Admin Operations</strong>
            <span>Administrator</span>
          </span>

          <span className="operator-chevron">⌄</span>
        </div>
      </header>

      <div className="workspace">
        <aside className="sidebar">
          <div>
            <p className="nav-label">OPERATIONS</p>

            <nav>
              <button
                type="button"
                className={`nav-item ${view === 'overview' ? 'active' : ''}`}
                onClick={openOverview}
              >
                <span>01</span>
                Overview
              </button>

              <button
                type="button"
                className={`nav-item ${
                  view === 'members' ? 'active' : ''
                }`}
                onClick={openMembers}
                data-testid="nav-members"
              >
                <span>02</span>
                Members
              </button>

              <button type="button" className="nav-item">
                <span>03</span>
                Accounts
              </button>

              <button type="button" className="nav-item">
                <span>04</span>
                Transactions
              </button>
            </nav>

            <p className="nav-label second-label">REPORTING</p>

            <nav>
              <button type="button" className="nav-item">
                <span>05</span>
                Activity
              </button>

              <button type="button" className="nav-item">
                <span>06</span>
                Reports
              </button>
            </nav>
          </div>

          <div className="secure-session">
            <div className="secure-icon">✓</div>

            <div>
              <strong>Secure session</strong>
              <span>Session {formatTime(seconds)}</span>
            </div>
          </div>
        </aside>

        <section className="main-content">
          {view === 'overview' ? (
            <Overview
              onOpenMembers={openMembers}
              onOpenMember={openMember}
            />
          ) : (
            <Members
              memberId={memberId}
              setMemberId={setMemberId}
              selectedMember={selectedMember}
              error={error}
              isSearching={isSearching}
              onSearch={searchMember}
              onOpenMember={openMember}
              onBack={handleBackToMembers}
            />
          )}
        </section>
      </div>
    </main>
  )
}

type OverviewProps = {
  onOpenMembers: () => void
  onOpenMember: (member: Member) => void
}

function Overview({ onOpenMembers, onOpenMember }: OverviewProps) {
  return (
    <>
      <div className="page-heading overview-heading">
        <div>
          <p className="breadcrumb">Northstar / Operations Center</p>

          <h1>Operations Center</h1>

          <p>
            A unified view of member services, account operations, and system
            activity.
          </p>
        </div>

        <div className="system-clock">
          <span>ENVIRONMENT</span>
          <strong>DEMO · PROTECTED</strong>
        </div>
      </div>

      <section className="hero-panel">
        <div className="hero-copy">
          <p className="section-kicker">NORTHSTAR CORE</p>

          <h2>
            Everything in one
            <br />
            <em>place.</em>
          </h2>

          <p>
            Monitor the banking environment, access member services, and
            maintain a complete operational trail from a single workspace.
          </p>

          <button
            type="button"
            className="primary-action hero-action"
            onClick={onOpenMembers}
          >
            Find a member
            <span>→</span>
          </button>
        </div>

        <div className="system-map" aria-label="Northstar system map">
          <div className="map-ring map-ring-one" />
          <div className="map-ring map-ring-two" />

          <div className="map-line line-one" />
          <div className="map-line line-two" />
          <div className="map-line line-three" />
          <div className="map-line line-four" />

          <div className="map-node node-core">
            <span>NS</span>
            <strong>CORE</strong>
          </div>

          <div className="map-node node-members">
            <span>●</span>
            <strong>MEMBERS</strong>
          </div>

          <div className="map-node node-accounts">
            <span>●</span>
            <strong>ACCOUNTS</strong>
          </div>

          <div className="map-node node-identity">
            <span>●</span>
            <strong>IDENTITY</strong>
          </div>

          <div className="map-node node-audit">
            <span>●</span>
            <strong>AUDIT</strong>
          </div>
        </div>
      </section>

      <section className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">MEMBER REGISTRY</span>
          <strong>2,481</strong>
          <span className="metric-meta">+2.4% this month</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">ACTIVE ACCOUNTS</span>
          <strong>4,826</strong>
          <span className="metric-meta">Across 18 branches</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">AVAILABILITY</span>
          <strong>99.98%</strong>
          <span className="metric-meta">Last 30 days</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">TODAY'S OPERATIONS</span>
          <strong>18,421</strong>
          <span className="metric-meta">+8.1% from yesterday</span>
        </div>
      </section>

      <section className="overview-grid">
        <div className="panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">SYSTEM INTEGRITY</p>
              <h2>Core services</h2>
            </div>

            <span className="panel-status">ALL OPERATIONAL</span>
          </div>

          <div className="service-list">
            <ServiceRow name="Member Registry" latency="42ms" />
            <ServiceRow name="Account Services" latency="68ms" />
            <ServiceRow name="Identity Service" latency="31ms" />
            <ServiceRow name="Audit Service" latency="54ms" />
          </div>
        </div>

        <div className="panel activity-panel">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">SESSION ACTIVITY</p>
              <h2>Recent operations</h2>
            </div>

            <span className="panel-time">LIVE</span>
          </div>

          <div className="activity-list">
            <ActivityRow
              title="Member profile accessed"
              detail="Member #12345"
              time="14:32:09"
            />

            <ActivityRow
              title="Account verification completed"
              detail="Savings •••• 4821"
              time="14:31:54"
            />

            <ActivityRow
              title="Secure session established"
              detail="Admin Operations"
              time="14:30:01"
            />
          </div>
        </div>
      </section>

      <section className="quick-access">
        <div>
          <p className="section-kicker">QUICK ACCESS</p>
          <h2>Start an operation</h2>
        </div>

        <div className="quick-actions">
          <button
            type="button"
            className="quick-action"
            onClick={onOpenMembers}
          >
            <span className="quick-number">01</span>
            <span>
              <strong>Find a member</strong>
              <small>Search the member registry</small>
            </span>
            <span className="quick-arrow">→</span>
          </button>

          <button
            type="button"
            className="quick-action"
            onClick={() => onOpenMember(MEMBERS[0])}
          >
            <span className="quick-number">02</span>
            <span>
              <strong>View demo account</strong>
              <small>Open member #12345</small>
            </span>
            <span className="quick-arrow">→</span>
          </button>
        </div>
      </section>
    </>
  )
}

function ServiceRow({
  name,
  latency,
}: {
  name: string
  latency: string
}) {
  return (
    <div className="service-row">
      <span className="service-indicator" />

      <strong>{name}</strong>

      <span className="service-latency">{latency}</span>

      <span className="service-status">Operational</span>
    </div>
  )
}

function ActivityRow({
  title,
  detail,
  time,
}: {
  title: string
  detail: string
  time: string
}) {
  return (
    <div className="activity-row">
      <span className="activity-marker" />

      <div>
        <strong>{title}</strong>
        <span>{detail}</span>
      </div>

      <time>{time}</time>
    </div>
  )
}

type MembersProps = {
  memberId: string
  setMemberId: (value: string) => void
  selectedMember: Member | null
  error: string
  isSearching: boolean
  onSearch: (id: string) => void
  onOpenMember: (member: Member) => void
  onBack: () => void
}

function Members({
  memberId,
  setMemberId,
  selectedMember,
  error,
  isSearching,
  onSearch,
  onOpenMember,
  onBack,
}: MembersProps) {
  if (selectedMember) {
    return (
      <>
        <div className="page-heading">
          <div>
            <p className="breadcrumb">
              Operations <span>/</span> Members <span>/</span> Dossier
            </p>

            <h1>Member Dossier</h1>

            <p>Verified member profile and account relationship.</p>
          </div>

          <button type="button" className="back-action" onClick={onBack}>
            ← Back to members
          </button>
        </div>

        <section className="dossier">
          <div className="dossier-hero">
            <div className="large-avatar">{selectedMember.initials}</div>

            <div className="identity">
              <p className="section-kicker">VERIFIED MEMBER</p>

              <h2 data-testid="member-name">{selectedMember.name}</h2>

              <span data-testid="member-id-result">
                Member #{selectedMember.id} · Branch {selectedMember.branch}
              </span>
            </div>

            <div className="member-status">
              <span className="status-dot" />
              {selectedMember.status}
            </div>
          </div>

          <div className="financial-grid">
            <div className="balance-card">
              <div className="card-top">
                <span>AVAILABLE SAVINGS</span>
                <span className="card-symbol">◇</span>
              </div>

              <strong data-testid="savings-balance">
                $
                {selectedMember.savingsBalance.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                })}
              </strong>

              <span className="balance-caption">Available balance</span>
            </div>

            <div className="account-card">
              <div className="account-card-header">
                <span>SAVINGS ACCOUNT</span>
                <span className="account-active">ACTIVE</span>
              </div>

              <strong>{selectedMember.accountNumber}</strong>

              <span>Personal savings</span>
            </div>
          </div>

          <div className="dossier-grid">
            <section className="detail-panel">
              <div className="detail-heading">
                <div>
                  <p className="section-kicker">IDENTITY</p>
                  <h3>Member information</h3>
                </div>
              </div>

              <div className="detail-list">
                <div>
                  <span>Full name</span>
                  <strong>{selectedMember.name}</strong>
                </div>

                <div>
                  <span>Member ID</span>
                  <strong>{selectedMember.id}</strong>
                </div>

                <div>
                  <span>Primary branch</span>
                  <strong>{selectedMember.branch}</strong>
                </div>

                <div>
                  <span>Account status</span>
                  <strong>{selectedMember.status}</strong>
                </div>
              </div>
            </section>

            <section className="detail-panel">
              <div className="detail-heading">
                <div>
                  <p className="section-kicker">AUDIT TRAIL</p>
                  <h3>Recent activity</h3>
                </div>
              </div>

              <div className="activity-list">
                <ActivityRow
                  title="Member profile retrieved"
                  detail="Verified successfully"
                  time={selectedMember.lastActivity}
                />

                <ActivityRow
                  title="Account status verified"
                  detail="Savings account"
                  time="Today, 14:31"
                />

                <ActivityRow
                  title="Secure session established"
                  detail="Admin Operations"
                  time="Today, 14:30"
                />
              </div>
            </section>
          </div>
        </section>
      </>
    )
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <p className="breadcrumb">
            Operations <span>/</span> Members
          </p>

          <h1>Member Services</h1>

          <p>
            Search the member registry to access account and profile
            information.
          </p>
        </div>

        <div className="heading-badge">
          <span>LIVE</span>
          Registry connected
        </div>
      </div>

      <section className="member-search-panel">
        <div className="panel-header">
          <div>
            <p className="section-kicker">MEMBER REGISTRY</p>

            <h2>Find a member</h2>

            <p>
              Enter a member identifier to securely retrieve their banking
              profile.
            </p>
          </div>

          <div className="registry-mark">
            <span>NS</span>
            <small>REGISTRY</small>
          </div>
        </div>

        <div className="search-divider" />

        <div className="search-form">
          <div className="field">
            <label htmlFor="member-id">MEMBER ID</label>

            <input
              id="member-id"
              name="member-id"
              data-testid="member-id"
              type="text"
              value={memberId}
              onChange={(event) => setMemberId(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  onSearch(memberId)
                }
              }}
              placeholder="Enter member ID"
            />
          </div>

          <button
            type="button"
            data-testid="search-member"
            className="primary-action"
            onClick={() => onSearch(memberId)}
            disabled={isSearching}
          >
            {isSearching ? (
              <>
                <span className="button-spinner" />
                Searching
              </>
            ) : (
              <>
                Search member
                <span>→</span>
              </>
            )}
          </button>
        </div>

        {error && (
          <div
            className="search-error"
            role="alert"
            data-testid="search-error"
          >
            <span>!</span>

            <div>
              <strong>Member lookup unsuccessful</strong>
              <p>{error}</p>
            </div>
          </div>
        )}

        <div className="demo-access">
          <span>DEMONSTRATION ACCESS</span>

          {MEMBERS.map((member) => (
            <button
              key={member.id}
              type="button"
              onClick={() =>{
                setMemberId(member.id)
                setError('')
              }}
            >
              {member.id} · {member.name}
            </button>
          ))}
        </div>
      </section>

      <section className="recent-section">
        <div className="recent-heading">
          <div>
            <p className="section-kicker">MEMBER REGISTRY</p>
            <h2>Recent member searches</h2>
          </div>

          <span>Current session</span>
        </div>

        <div className="member-table">
          <div className="table-header">
            <span>MEMBER</span>
            <span>MEMBER ID</span>
            <span>ACCOUNT</span>
            <span>BALANCE</span>
            <span>STATUS</span>
          </div>

          {MEMBERS.map((member) => (
            <button
              type="button"
              className="table-row"
              key={member.id}
              onClick={() => {
                onOpenMember(member.id)
                setError('')
              }}
            >
              <span className="member-cell">
                <span className="mini-avatar">{member.initials}</span>
                <strong>{member.name}</strong>
              </span>

              <span>{member.id}</span>

              <span>Savings</span>

              <strong>
                $
                {member.savingsBalance.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                })}
              </strong>

              <span className="active-status">
                <i />
                {member.status}
              </span>
            </button>
          ))}
        </div>
      </section>
    </>
  )
}

export default App