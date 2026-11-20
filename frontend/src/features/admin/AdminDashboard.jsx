import React, { useState, useEffect } from 'react';
import apiClient from '../../services/api';
import { Users, UserPlus, Sliders, TrendingUp, Search, ClipboardList, Timer, CircleCheck, Star, AlertTriangle } from 'lucide-react';
import { useToast } from '../../components/common/Toast';

export const AdminDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [complaints, setComplaints] = useState([]);
  const [staffList, setStaffList] = useState([]);
  const [staffPerformance, setStaffPerformance] = useState([]);
  const [activeView, setActiveView] = useState('TRIAGE'); // TRIAGE | TEAM | PERFORMANCE | METRICS
  const [loading, setLoading] = useState(true);

  // Assignment Modal
  const [assigningComplaint, setAssigningComplaint] = useState(null);
  const [selectedStaffId, setSelectedStaffId] = useState('');

  // Add Staff Modal
  const [showAddStaffModal, setShowAddStaffModal] = useState(false);
  const [staffEmail, setStaffEmail] = useState('');
  const [staffName, setStaffName] = useState('');
  const [staffDept, setStaffDept] = useState('Electrical');
  const [staffPassword, setStaffPassword] = useState('Staff@12345');
  const [searchTerm, setSearchTerm] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const { notify } = useToast();
  const filteredComplaints = complaints.filter((c) => `${c.ticket_id} ${c.title} ${c.location} ${c.category} ${c.student?.full_name}`.toLowerCase().includes(searchTerm.toLowerCase()));
  const activeStaff = staffList.filter((member) => member.is_active);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [analyticsRes, complaintsRes, staffRes, performanceRes] = await Promise.all([
        apiClient.get('/analytics/overview'),
        apiClient.get('/complaints?limit=100'),
        apiClient.get('/admin/staff'),
        apiClient.get('/admin/staff/performance'),
      ]);
      setAnalytics(analyticsRes.data);
      setComplaints(complaintsRes.data);
      setStaffList(staffRes.data);
      setStaffPerformance(performanceRes.data);
      setErrorMessage('');
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Campus operations data could not be loaded.');
      console.error('Error fetching admin data', err);
    } finally {
      setLoading(false);
    }
  };

  const refreshData = () => { void fetchData(); };

  useEffect(() => {
    const timer = setTimeout(() => { void fetchData(); }, 0);
    return () => clearTimeout(timer);
  }, []);

  const handleAssignSubmit = async (e) => {
    e.preventDefault();
    if (!selectedStaffId) return;
    try {
      await apiClient.post('/admin/assign', {
        complaint_id: assigningComplaint.id,
        staff_id: Number(selectedStaffId),
      });
      notify('Issue assigned to the selected staff member.');
      setAssigningComplaint(null);
      setSelectedStaffId('');
      refreshData();
    } catch (err) {
      notify(err.response?.data?.detail || 'Assignment failed. Please try again.', 'error');
    }
  };

  const handleCreateStaff = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/admin/staff', {
        email: staffEmail,
        full_name: staffName,
        department: staffDept,
        password: staffPassword,
      });
      notify('Staff account created successfully.');
      setShowAddStaffModal(false);
      setStaffEmail('');
      setStaffName('');
      refreshData();
    } catch (err) {
      notify(err.response?.data?.detail || 'Could not create this staff account.', 'error');
    }
  };

  const handlePriorityChange = async (complaintId, newPriority) => {
    try {
      await apiClient.patch(`/admin/complaints/${complaintId}`, {
        priority: newPriority,
      });
      notify('Priority updated.');
      refreshData();
    } catch (err) {
      notify(err.response?.data?.detail || 'Could not update priority.', 'error');
    }
  };

  const handleStaffActiveChange = async (staff) => {
    try {
      const response = await apiClient.patch(`/admin/staff/${staff.id}/active`, { is_active: !staff.is_active });
      setStaffList((current) => current.map((member) => member.id === staff.id ? response.data : member));
      notify(`${staff.full_name} ${staff.is_active ? 'deactivated' : 'reactivated'}.`);
    } catch (err) {
      notify(err.response?.data?.detail || 'Could not update this staff account.', 'error');
    }
  };

  return (
    <div>
      <div className="page-heading">
        <div>
          <div className="page-eyebrow">Operations overview</div>
          <h1 className="page-title">Campus operations overview</h1>
          <p className="page-subtitle">Triage incoming issues, coordinate staff, and monitor campus response.</p>
        </div>
        <button onClick={() => setShowAddStaffModal(true)} className="btn-primary"><UserPlus size={16} /> Add team member</button>
      </div>

      {/* Top Stat Cards */}
      {loading && !analytics ? <div className="metrics-grid" aria-label="Loading operations metrics"><div className="skeleton-card" /><div className="skeleton-card" /><div className="skeleton-card" /><div className="skeleton-card" /></div> : analytics && (
        <div className="metrics-grid">
          <div className="metric-card"><div className="metric-top">Total issues <span className="metric-icon"><ClipboardList size={16} /></span></div>
            <div className="metric-value">{analytics.total_complaints}</div><div className="metric-note">Across the campus</div>
          </div>
          <div className="metric-card"><div className="metric-top">Needs triage <span className="metric-icon amber"><Sliders size={16} /></span></div>
            <div className="metric-value">{analytics.pending_complaints}</div><div className="metric-note">Awaiting review</div>
          </div>
          <div className="metric-card"><div className="metric-top">In progress <span className="metric-icon blue"><Timer size={16} /></span></div>
            <div className="metric-value">{analytics.in_progress_complaints}</div><div className="metric-note">With response teams</div>
          </div>
          <div className="metric-card"><div className="metric-top">Avg. resolution <span className="metric-icon green"><CircleCheck size={16} /></span></div>
            <div className="metric-value">{analytics.avg_resolution_hours}<span style={{ fontSize: 12, marginLeft: 4, letterSpacing: 0 }}>hrs</span></div><div className="metric-note">From report to resolved</div>
          </div>
          <div className="metric-card"><div className="metric-top">Student rating <span className="metric-icon amber"><Star size={16} /></span></div>
            <div className="metric-value">{analytics.avg_feedback_rating}<span style={{ fontSize: 12, marginLeft: 4, letterSpacing: 0 }}>/ 5</span></div><div className="metric-note">Resolution feedback</div>
          </div>
          <div className="metric-card"><div className="metric-top">Overdue assignments <span className="metric-icon amber"><AlertTriangle size={16} /></span></div>
            <div className="metric-value">{analytics.overdue_assignments || 0}</div><div className="metric-note">Beyond response thresholds</div>
          </div>
        </div>
      )}

      {/* View Switcher */}
      {errorMessage && <div className="notice notice-error" role="alert">{errorMessage}<button onClick={() => setErrorMessage('')} aria-label="Dismiss">×</button></div>}
      <div style={{ display: 'flex', gap: 7, marginBottom: 14, flexWrap: 'wrap' }}>
        <button
          onClick={() => setActiveView('TRIAGE')}
          className={activeView === 'TRIAGE' ? 'btn-primary' : 'btn-secondary'}
        >
          <Sliders size={14} /> Triage queue
        </button>
        <button
          onClick={() => setActiveView('TEAM')}
          className={activeView === 'TEAM' ? 'btn-primary' : 'btn-secondary'}
        >
          <Users size={14} /> Staff directory
        </button>
        <button
          onClick={() => setActiveView('PERFORMANCE')}
          className={activeView === 'PERFORMANCE' ? 'btn-primary' : 'btn-secondary'}
        >
          <Star size={14} /> Performance desk
        </button>
        <button
          onClick={() => setActiveView('METRICS')}
          className={activeView === 'METRICS' ? 'btn-primary' : 'btn-secondary'}
        >
          <TrendingUp size={14} /> Insights
        </button>
      </div>

      {/* View 1: Triage & Dispatch Table */}
      {activeView === 'TRIAGE' && (
        <div className="card" id="issues">
          <div className="section-title"><div><h3>Campus issue queue</h3><div className="metric-note" style={{ marginTop: 5 }}>Review suggestions and route work to a department.</div></div><div className="search-control"><Search size={15} /><input aria-label="Search issues" placeholder="Search tickets" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} /></div></div>
          {loading && complaints.length === 0 ? <div className="loading-rows" role="status"><span /><span /><span /></div> : <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Student & Title</th>
                  <th>Location</th>
                  <th>Category (AI)</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Dispatch</th>
                </tr>
              </thead>
              <tbody>
                {filteredComplaints.map((c) => (
                  <tr key={c.id}>
                    <td style={{ fontFamily: 'monospace', fontWeight: '600' }}>{c.ticket_id}</td>
                    <td>
                      <div style={{ fontWeight: '600' }}>{c.title}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        Lodged by: {c.student?.full_name} ({c.student?.email})
                      </div>
                    </td>
                    <td>{c.location}</td>
                    <td>
                      <span style={{ fontWeight: '500' }}>{c.category}</span>
                      {c.predicted_category && (
                        <div style={{ fontSize: '0.75rem', color: '#6366f1' }}>
                          AI Match: {Math.round((c.prediction_confidence || 0.85) * 100)}%
                        </div>
                      )}
                    </td>
                    <td>
                      <select
                        value={c.priority}
                        onChange={(e) => handlePriorityChange(c.id, e.target.value)}
                        style={{ padding: '0.2rem 0.4rem', borderRadius: '4px', border: '1px solid var(--border)' }}
                      >
                        <option value="LOW">LOW</option>
                        <option value="MEDIUM">MEDIUM</option>
                        <option value="HIGH">HIGH</option>
                        <option value="CRITICAL">CRITICAL</option>
                      </select>
                    </td>
                    <td>
                      <span className={`badge badge-${c.status}`}>{c.status}</span>
                    </td>
                    <td>
                      <button
                        onClick={() => setAssigningComplaint(c)}
                        className="btn-secondary"
                        style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                      >
                        Assign Staff
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>}
        </div>
      )}

      {/* Staff directory and account management */}
      {activeView === 'TEAM' && (
        <div className="card">
          <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem', fontWeight: '600' }}>Staff directory</h3>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Staff Name</th>
                  <th>Department</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Account</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {staffList.map((st) => (
                  <tr key={st.id}>
                    <td style={{ fontWeight: '600' }}>{st.full_name}</td>
                    <td><span className="badge badge-SUBMITTED">{st.department}</span></td>
                    <td>{st.email}</td>
                    <td>{st.phone_number || 'N/A'}</td>
                    <td><span className={`badge ${st.is_active ? 'badge-RESOLVED' : 'badge-REJECTED'}`}>{st.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td><button type="button" className="btn-secondary" onClick={() => handleStaffActiveChange(st)}>{st.is_active ? 'Deactivate' : 'Reactivate'}</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Dedicated staff performance and feedback desk */}
      {activeView === 'PERFORMANCE' && (
        <div style={{ display: 'grid', gap: 16 }}>
          <div className="page-heading" style={{ marginBottom: 0 }}><div><div className="page-eyebrow">Team quality</div><h2 className="page-title" style={{ fontSize: 22 }}>Staff performance desk</h2><p className="page-subtitle">Review student ratings and resolution feedback by staff member.</p></div></div>
          <div className="metrics-grid">
            <div className="metric-card"><div className="metric-top">Rated staff <span className="metric-icon"><Users size={16} /></span></div><div className="metric-value">{staffPerformance.filter((item) => item.rating_count > 0).length}</div><div className="metric-note">Staff with at least one rating</div></div>
            <div className="metric-card"><div className="metric-top">Ratings received <span className="metric-icon amber"><Star size={16} /></span></div><div className="metric-value">{staffPerformance.reduce((sum, item) => sum + item.rating_count, 0)}</div><div className="metric-note">Student resolution ratings</div></div>
            <div className="metric-card"><div className="metric-top">Overall staff rating <span className="metric-icon green"><CircleCheck size={16} /></span></div><div className="metric-value">{analytics?.avg_feedback_rating ?? '—'}<small style={{ fontSize: 13 }}> / 5</small></div><div className="metric-note">Across submitted feedback</div></div>
          </div>
          <div className="card">
          <h3 style={{ marginBottom: 6, fontSize: '1.1rem', fontWeight: 600 }}>Ratings & comments by staff</h3>
          <p className="metric-note" style={{ marginBottom: 14 }}>Each rating is linked to the staff member who completed that work order.</p>
          {staffPerformance.every((item) => item.feedback.length === 0) ? <div className="empty-state">No staff feedback has been submitted yet.</div> : staffPerformance.filter((item) => item.feedback.length).map((item) => <section key={item.staff.id} style={{ borderTop: '1px solid var(--border)', padding: '14px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', marginBottom: 8 }}><div><strong>{item.staff.full_name}</strong><span className="cell-sub">{item.staff.department}</span></div><span style={{ color: '#bd8d2e', whiteSpace: 'nowrap' }}>★ {item.average_rating}/5 · {item.rating_count} rating{item.rating_count === 1 ? '' : 's'}</span></div>
            <div style={{ display: 'grid', gap: 8 }}>{item.feedback.map((entry) => <article key={entry.id} className="description-box"><strong>{entry.rating}/5 · {entry.complaint?.ticket_id} — {entry.complaint?.title}</strong>{entry.comments && <p style={{ margin: '6px 0 0' }}>{entry.comments}</p>}<span className="cell-sub">{entry.student?.full_name || 'Student'} · {new Date(entry.created_at).toLocaleDateString()}</span></article>)}</div>
          </section>)}
          </div>
        </div>
      )}

      {/* View 3: Metrics & Distribution Breakdown */}
      {activeView === 'METRICS' && analytics && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
          <div className="card">
            <h3 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '1rem' }}>Category Distribution</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {Object.entries(analytics.category_distribution || {}).map(([cat, count]) => (
                <div key={cat} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: '500' }}>{cat}</span>
                  <span className="badge badge-SUBMITTED">{count} tickets</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h3 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '1rem' }}>Status Lifecycle Breakdown</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {Object.entries(analytics.status_distribution || {}).map(([status, count]) => (
                <div key={status} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className={`badge badge-${status}`}>{status}</span>
                  <span style={{ fontWeight: '600' }}>{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Assign Staff Modal */}
      {assigningComplaint && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="card" style={{ width: '100%', maxWidth: '480px' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1rem' }}>Dispatch Maintenance Staff</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Ticket: <b>{assigningComplaint.ticket_id}</b> ({assigningComplaint.category})<br />
              Location: {assigningComplaint.location}
            </p>
            <form onSubmit={handleAssignSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.875rem', fontWeight: '500', display: 'block', marginBottom: '0.3rem' }}>
                  Select Maintenance Personnel
                </label>
                <select
                  required
                  className="input-field"
                  value={selectedStaffId}
                  onChange={(e) => setSelectedStaffId(e.target.value)}
                >
                  <option value="">-- Choose Staff Member --</option>
                  {activeStaff.map((st) => (
                    <option key={st.id} value={st.id}>
                      {st.full_name} ({st.department}) - {st.email}
                    </option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button type="button" onClick={() => setAssigningComplaint(null)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-primary">Confirm Assignment</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Staff Modal */}
      {showAddStaffModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="card" style={{ width: '100%', maxWidth: '480px' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1rem' }}>Register New Staff Member</h3>
            <form onSubmit={handleCreateStaff} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.875rem', fontWeight: '500', display: 'block', marginBottom: '0.3rem' }}>Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Mukesh Verma"
                  className="input-field"
                  value={staffName}
                  onChange={(e) => setStaffName(e.target.value)}
                />
              </div>
              <div>
                <label style={{ fontSize: '0.875rem', fontWeight: '500', display: 'block', marginBottom: '0.3rem' }}>Staff Work Email</label>
                <input
                  type="email"
                  required
                  placeholder="staff@campusfix.edu"
                  className="input-field"
                  value={staffEmail}
                  onChange={(e) => setStaffEmail(e.target.value)}
                />
              </div>
              <div>
                <label style={{ fontSize: '0.875rem', fontWeight: '500', display: 'block', marginBottom: '0.3rem' }}>Assigned Department</label>
                <select
                  className="input-field"
                  value={staffDept}
                  onChange={(e) => setStaffDept(e.target.value)}
                >
                  <option value="Electrical">Electrical</option>
                  <option value="IT">IT</option>
                  <option value="Plumbing">Plumbing</option>
                  <option value="Cleanliness">Cleanliness</option>
                  <option value="Security">Security</option>
                  <option value="Furniture">Furniture</option>
                  <option value="Civil Maintenance">Civil Maintenance</option>
                  <option value="Sanitation">Sanitation</option>
                  <option value="Cafeteria">Cafeteria</option>
                </select>
              </div>
              <div>
                <label style={{ fontSize: '0.875rem', fontWeight: '500', display: 'block', marginBottom: '0.3rem' }}>Default Password</label>
                <input
                  type="password"
                  required
                  className="input-field"
                  value={staffPassword}
                  onChange={(e) => setStaffPassword(e.target.value)}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
                <button type="button" onClick={() => setShowAddStaffModal(false)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-primary">Register Staff</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
