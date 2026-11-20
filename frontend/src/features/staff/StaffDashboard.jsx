import React, { useState, useEffect, useRef } from 'react';
import apiClient from '../../services/api';
import { Clock } from 'lucide-react';
import { ClipboardCheck, CircleCheck, Timer, Search, Star, MessageSquareText } from 'lucide-react';
import { useToast } from '../../components/common/Toast';

export const StaffDashboard = () => {
  const [assignments, setAssignments] = useState([]);
  const [feedback, setFeedback] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('ALL');
  
  // Resolution notes modal
  const [selectedTask, setSelectedTask] = useState(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const hasLoadedAssignments = useRef(false);
  const { notify } = useToast();

  const fetchAssignments = async () => {
    try {
      if (!hasLoadedAssignments.current) setLoading(true);
      const [res, feedbackRes] = await Promise.all([apiClient.get('/staff/assignments'), apiClient.get('/staff/feedback')]);
      setAssignments(res.data);
      setFeedback(feedbackRes.data);
      hasLoadedAssignments.current = true;
      setErrorMessage('');
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Assignments could not be loaded.');
      console.error('Failed to load assignments', err);
    } finally {
      setLoading(false);
    }
  };

  const refreshAssignments = () => { void fetchAssignments(); };

  useEffect(() => {
    const timer = setTimeout(() => { void fetchAssignments(); }, 0);
    return () => clearTimeout(timer);
  }, []);

  const handleRespond = async (assignmentId, accept) => {
    try {
      await apiClient.post(`/staff/assignments/${assignmentId}/respond`, {
        accept,
        rejection_reason: accept ? null : rejectionReason,
      });
      setShowRejectModal(false);
      setRejectionReason('');
      notify(accept ? 'Assignment accepted and added to your active work.' : 'Assignment declined and returned to the triage queue.');
      refreshAssignments();
    } catch (err) {
      notify(err.response?.data?.detail || 'Could not update the assignment.', 'error');
    }
  };

  const handleResolve = async (e) => {
    e.preventDefault();
    if (!resolutionNotes.trim()) {
      notify('Add a short note describing the work you completed.', 'error');
      return;
    }
    setSubmitting(true);
    try {
      await apiClient.post(`/staff/assignments/${selectedTask.id}/resolve`, {
        resolution_notes: resolutionNotes,
      });
      setSelectedTask(null);
      setResolutionNotes('');
      notify('Work order marked resolved. The student can now share feedback.');
      refreshAssignments();
    } catch (err) {
      notify(err.response?.data?.detail || 'Could not resolve this work order.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const filteredTasks = assignments.filter((a) => {
    if (activeTab === 'ALL') return true;
    return a.status === activeTab;
  }).filter((a) => `${a.complaint?.ticket_id} ${a.complaint?.title} ${a.complaint?.location} ${a.complaint?.category}`.toLowerCase().includes(searchTerm.toLowerCase()));
  const averageRating = feedback.length ? (feedback.reduce((sum, item) => sum + item.rating, 0) / feedback.length).toFixed(1) : '—';

  return (
    <div>
      <div className="page-heading">
        <div><div className="page-eyebrow">Maintenance workspace</div>
        <h1 className="page-title">Today’s work, clearly organized.</h1>
        <p className="page-subtitle">Review your work orders and keep students updated as you make progress.</p></div>
      </div>

      <section className="card" style={{ marginBottom: 18 }} id="feedback">
        <div className="section-title"><div><h3>Student feedback</h3><div className="metric-note" style={{ marginTop: 5 }}>Ratings and comments for work you completed.</div></div></div>
        <div className="metrics-grid" style={{ marginBottom: 14 }}>
          <div className="metric-card"><div className="metric-top">Average rating <span className="metric-icon amber"><Star size={16} /></span></div><div className="metric-value">{averageRating}<small style={{ fontSize: 13 }}> / 5</small></div><div className="metric-note">Across {feedback.length} rating{feedback.length === 1 ? '' : 's'}</div></div>
          <div className="metric-card"><div className="metric-top">Written comments <span className="metric-icon"><MessageSquareText size={16} /></span></div><div className="metric-value">{feedback.filter((item) => item.comments?.trim()).length}</div><div className="metric-note">Student notes on completed work</div></div>
        </div>
        {feedback.length === 0 ? <div className="empty-state">No student ratings yet. Feedback appears here after a resolved issue is rated.</div> : <div className="table-container"><table><thead><tr><th>Rating</th><th>Ticket</th><th>Issue</th><th>Student comment</th><th>Received</th></tr></thead><tbody>{feedback.map((item) => <tr key={item.id}><td><span style={{ color: '#bd8d2e', whiteSpace: 'nowrap' }}>{'★'.repeat(item.rating)}{'☆'.repeat(5 - item.rating)} {item.rating}/5</span></td><td><span className="ticket-id">{item.complaint?.ticket_id}</span></td><td>{item.complaint?.title}<span className="cell-sub">{item.complaint?.location}</span></td><td>{item.comments || <span className="metric-note">No comment</span>}</td><td>{new Date(item.created_at).toLocaleDateString()}</td></tr>)}</tbody></table></div>}
      </section>

      {/* Metrics Row */}
      <div className="metrics-grid">
        <div className="metric-card"><div className="metric-top">Assigned work <span className="metric-icon"><ClipboardCheck size={16} /></span></div>
          <div className="metric-value">{assignments.length}</div><div className="metric-note">All work orders</div>
        </div>
        <div className="metric-card"><div className="metric-top">Needs review <span className="metric-icon amber"><Clock size={16} /></span></div>
          <div className="metric-value">
            {assignments.filter(a => a.status === 'PENDING').length}
          </div><div className="metric-note">Waiting for your response</div>
        </div>
        <div className="metric-card"><div className="metric-top">In progress <span className="metric-icon blue"><Timer size={16} /></span></div>
          <div className="metric-value">
            {assignments.filter(a => a.status === 'ACCEPTED').length}
          </div><div className="metric-note">Work accepted</div>
        </div>
        <div className="metric-card"><div className="metric-top">Completed <span className="metric-icon green"><CircleCheck size={16} /></span></div>
          <div className="metric-value">
            {assignments.filter(a => a.status === 'COMPLETED').length}
          </div><div className="metric-note">Resolved work orders</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        {['ALL', 'PENDING', 'ACCEPTED', 'COMPLETED', 'REJECTED'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={activeTab === tab ? 'btn-primary' : 'btn-secondary'}
            style={{ padding: '0.4rem 0.9rem' }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tasks Table */}
      <div className="card" id="issues">
        <div className="section-title"><div><h3>Work order queue</h3><div className="metric-note" style={{ marginTop: 5 }}>Assignments routed to your team.</div></div><div className="search-control"><Search size={15} /><input aria-label="Search work orders" placeholder="Search work orders" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} /></div></div>
        {errorMessage && <div className="notice notice-error" role="alert">{errorMessage}<button onClick={() => setErrorMessage('')} aria-label="Dismiss">×</button></div>}
        {loading ? (
          <p style={{ color: 'var(--text-muted)' }}>Loading assigned work orders...</p>
        ) : filteredTasks.length === 0 ? (
          <div className="empty-state">No work orders match this view.</div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Issue Details</th>
                  <th>Location</th>
                  <th>Priority / Reports</th>
                  <th>Assigned Date</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredTasks.map((task) => (
                  <tr key={task.id}>
                    <td style={{ fontFamily: 'monospace', fontWeight: '600' }}>
                      {task.complaint?.ticket_id}
                    </td>
                    <td>
                      <div style={{ fontWeight: '600' }}>{task.complaint?.title}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{task.complaint?.description}</div>
                    </td>
                    <td>{task.complaint?.location}</td>
                    <td><span className={`priority-${task.complaint?.priority}`}>{task.complaint?.priority}</span>{task.complaint?.report_count > 1 && <div className="cell-sub">{task.complaint.report_count} reports</div>}</td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      {new Date(task.assigned_at).toLocaleDateString()}
                    </td>
                    <td>
                      <span className={`badge badge-${task.status}`}>{task.status}</span>
                    </td>
                    <td>
                      {task.status === 'PENDING' && (
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button onClick={() => handleRespond(task.id, true)} className="btn-success" style={{ padding: '0.3rem 0.6rem' }}>
                            Accept
                          </button>
                          <button
                            onClick={() => { setSelectedTask(task); setShowRejectModal(true); }}
                            className="btn-danger"
                            style={{ padding: '0.3rem 0.6rem' }}
                          >
                            Reject
                          </button>
                        </div>
                      )}
                      {task.status === 'ACCEPTED' && (
                        <button
                          onClick={() => setSelectedTask(task)}
                          className="btn-primary"
                          style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                        >
                          Mark Resolved
                        </button>
                      )}
                      {task.status === 'COMPLETED' && (
                        <span style={{ fontSize: '0.8rem', color: '#16a34a', fontWeight: '500' }}>Done</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Resolution Notes Modal */}
      {selectedTask && !showRejectModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="card" style={{ width: '100%', maxWidth: '500px' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1rem' }}>Complete Work Order</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Ticket: {selectedTask.complaint?.ticket_id} - {selectedTask.complaint?.title}
            </p>
            <form onSubmit={handleResolve} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.875rem', fontWeight: '500', display: 'block', marginBottom: '0.3rem' }}>
                  Resolution Notes & Parts Repaired
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Describe repair action (e.g. Replaced capacitor on AC unit and cleaned filter. System working normally)."
                  className="input-field"
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button type="button" onClick={() => setSelectedTask(null)} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={submitting} className="btn-success">
                  {submitting ? 'Submitting...' : 'Mark as Resolved'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reject Assignment Modal */}
      {showRejectModal && selectedTask && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="card" style={{ width: '100%', maxWidth: '450px' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '1rem' }}>Reject Assignment</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Provide a valid reason for why you are unable to fulfill this task.
            </p>
            <div>
              <textarea
                rows={3}
                placeholder="e.g. Requires specialized HVAC contractor / Out of campus on emergency leave."
                className="input-field"
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '1rem' }}>
              <button type="button" onClick={() => { setShowRejectModal(false); setSelectedTask(null); }} className="btn-secondary">Cancel</button>
              <button type="button" onClick={() => handleRespond(selectedTask.id, false)} className="btn-danger">
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
