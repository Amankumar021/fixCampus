import React, { useEffect, useMemo, useRef, useState } from 'react';
import { AlertTriangle, ArrowUpRight, CheckCircle2, CircleCheck, Clock, FileText, MapPin, PlusCircle, Search, Send, Sparkles, Timer, Award, HeartHandshake } from 'lucide-react';
import apiClient, { API_ORIGIN } from '../../services/api';

const CATEGORIES = ['Electrical', 'IT', 'Plumbing', 'Cleanliness', 'Security', 'Furniture', 'Civil Maintenance', 'Sanitation', 'Cafeteria'];
const STATUS_STEPS = ['SUBMITTED', 'UNDER_REVIEW', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED'];

export const StudentDashboard = () => {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [predictedCategory, setPredictedCategory] = useState('');
  const [confidence, setConfidence] = useState(null);
  const [predicting, setPredicting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [attachmentUrl, setAttachmentUrl] = useState('');
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const hasLoadedComplaints = useRef(false);
  const [feedbackRating, setFeedbackRating] = useState(5);
  const [feedbackComments, setFeedbackComments] = useState('');
  const [existingFeedback, setExistingFeedback] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [notice, setNotice] = useState('');
  const [rewards, setRewards] = useState({ total_points: 0, next_milestone: 50, points_to_next_milestone: 50, transactions: [] });

  const fetchComplaints = async () => {
    try {
      if (!hasLoadedComplaints.current) setLoading(true);
      const response = await apiClient.get('/complaints');
      setComplaints(response.data);
      hasLoadedComplaints.current = true;
      setErrorMessage('');
    } catch (error) {
      setErrorMessage(error.response?.data?.detail || 'Could not load your issues. Please try again.');
    } finally { setLoading(false); }
  };
  useEffect(() => {
    const timer = setTimeout(() => { void fetchComplaints(); }, 0);
    return () => clearTimeout(timer);
  }, []);

  const fetchRewards = async () => {
    try {
      const response = await apiClient.get('/rewards/me');
      setRewards(response.data);
    } catch (error) {
      setErrorMessage(error.response?.data?.detail || 'Your reward balance could not be loaded.');
    }
  };
  useEffect(() => {
    const timer = setTimeout(() => { void fetchRewards(); }, 0);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (description.trim().length < 14) {
      const resetTimer = setTimeout(() => { setPredictedCategory(''); setConfidence(null); }, 0);
      return () => clearTimeout(resetTimer);
    }
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        setPredicting(true);
        const response = await apiClient.post('/ml/predict', { description: `${title} ${description}` }, { signal: controller.signal });
        setPredictedCategory(response.data.predicted_category);
        setConfidence(Math.round(response.data.confidence * 100));
        if (!selectedCategory) setSelectedCategory(response.data.is_confident ? response.data.predicted_category : '');
      } catch (error) {
        if (error.code !== 'ERR_CANCELED') setPredictedCategory('');
      } finally { setPredicting(false); }
    }, 550);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [description, title, selectedCategory]);

  const visibleComplaints = useMemo(() => complaints.filter((item) =>
    `${item.ticket_id} ${item.title} ${item.location} ${item.category}`.toLowerCase().includes(searchTerm.toLowerCase())
  ), [complaints, searchTerm]);
  const activeCount = complaints.filter((item) => ['SUBMITTED', 'UNDER_REVIEW', 'ASSIGNED', 'IN_PROGRESS', 'REOPENED'].includes(item.status)).length;
  const resolvedCount = complaints.filter((item) => ['RESOLVED', 'CLOSED'].includes(item.status)).length;

  const resetForm = () => { setTitle(''); setDescription(''); setLocation(''); setSelectedCategory(''); setPredictedCategory(''); setConfidence(null); setAttachmentUrl(''); };
  const handleAttachment = async (event) => {
    const file = event.target.files?.[0]; if (!file) return;
    const formData = new FormData(); formData.append('file', file);
    try {
      const response = await apiClient.post('/complaints/attachments', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      setAttachmentUrl(response.data.attachment_url); setNotice('Attachment uploaded.');
    } catch (error) { setErrorMessage(error.response?.data?.detail || 'Attachment upload failed.'); }
  };
  const handleSubmit = async (event) => {
    event.preventDefault(); setSubmitting(true); setErrorMessage('');
    try {
      const category = selectedCategory || (confidence >= 45 ? predictedCategory : 'Other');
      const response = await apiClient.post('/complaints', { title, description, location, category, attachment_url: attachmentUrl || null });
      setShowModal(false); resetForm(); setNotice(response.data.report_count > 1 ? `This matched an existing issue. It now has ${response.data.report_count} reports and ${response.data.priority} priority.` : response.data.reward_points_awarded ? `Your issue was submitted. You earned ${response.data.reward_points_awarded} Campus Impact points!` : 'Your issue was submitted. Your daily report points limit has been reached; the report is still in the queue.'); await Promise.all([fetchComplaints(), fetchRewards()]);
    } catch (error) { setErrorMessage(error.response?.data?.detail || 'Could not submit the issue. Please try again.'); }
    finally { setSubmitting(false); }
  };
  const viewComplaintDetail = async (complaint) => {
    setSelectedComplaint(complaint); setTimeline([]); setExistingFeedback(null); setTimelineLoading(true);
    try {
      const [timelineResponse, feedbackResponse] = await Promise.all([
        apiClient.get(`/complaints/${complaint.id}/timeline`),
        ['RESOLVED', 'CLOSED'].includes(complaint.status) ? apiClient.get(`/complaints/${complaint.id}/feedback`) : Promise.resolve({ data: null }),
      ]);
      setTimeline(timelineResponse.data); setExistingFeedback(feedbackResponse.data);
    }
    catch (error) { setErrorMessage(error.response?.data?.detail || 'Could not load the activity timeline.'); }
    finally { setTimelineLoading(false); }
  };
  const handleFeedbackSubmit = async (event) => {
    event.preventDefault();
    try {
      const response = await apiClient.post(`/complaints/${selectedComplaint.id}/feedback`, { rating: Number(feedbackRating), comments: feedbackComments });
      setNotice(response.data.reward_points_awarded ? `Thanks for helping improve campus services. You earned ${response.data.reward_points_awarded} Campus Impact points!` : 'Thanks for helping improve campus services.'); setSelectedComplaint(null); setFeedbackComments(''); await Promise.all([fetchComplaints(), fetchRewards()]);
    } catch (error) { setErrorMessage(error.response?.data?.detail || 'Could not submit feedback.'); }
  };
  const handleReopen = async (complaintId) => {
    try {
      await apiClient.patch(`/complaints/${complaintId}/status?target_status=REOPENED&comment=Student%20reopened%20complaint`);
      setSelectedComplaint(null); setNotice('Issue reopened. Your campus team will review it again.'); await fetchComplaints();
    } catch (error) { setErrorMessage(error.response?.data?.detail || 'Could not reopen the issue.'); }
  };

  return <div>
    <div className="page-heading"><div><div className="page-eyebrow">Student services</div><h1 className="page-title">Your campus, in good hands.</h1><p className="page-subtitle">Report an issue and follow every update from your campus team.</p></div><button onClick={() => { setErrorMessage(''); setShowModal(true); }} className="btn-primary"><PlusCircle size={17} /> Report an issue</button></div>
    {notice && <div className="notice notice-success" role="status">{notice}<button onClick={() => setNotice('')} aria-label="Dismiss">×</button></div>}
    {errorMessage && <div className="notice notice-error" role="alert">{errorMessage}<button onClick={() => setErrorMessage('')} aria-label="Dismiss">×</button></div>}
    <div className="metrics-grid student-metrics-grid">
      <Metric label="Campus Impact points" value={rewards.total_points} note={`${rewards.points_to_next_milestone} points to your next milestone`} icon={<Award size={16} />} tone="amber" />
      <Metric label="Issues reported" value={complaints.length} note="Your reports to date" icon={<FileText size={16} />} />
      <Metric label="Being handled" value={activeCount} note="Open with campus teams" icon={<Timer size={16} />} tone="blue" />
      <Metric label="Resolved" value={resolvedCount} note="Completed campus requests" icon={<CircleCheck size={16} />} tone="green" />
      <Metric label="Response tracking" value="Live" note="Updates appear in your timeline" icon={<Clock size={16} />} tone="amber" />
    </div>
    <section className="impact-card" aria-label="Campus Impact rewards">
      <div className="impact-icon"><HeartHandshake size={22} /></div>
      <div className="impact-copy"><strong>Your voice helps make campus better.</strong><span>Earn 10 points for reporting a campus issue and 5 more for sharing feedback after it’s resolved.</span>
        <div className="impact-progress" role="progressbar" aria-label="Progress to next Campus Impact milestone" aria-valuemin={0} aria-valuemax={rewards.next_milestone} aria-valuenow={rewards.total_points % rewards.next_milestone}>
          <span style={{ width: `${Math.min(100, ((rewards.total_points % rewards.next_milestone) / rewards.next_milestone) * 100)}%` }} />
        </div><small>{rewards.total_points} points · {rewards.points_to_next_milestone} to your {rewards.next_milestone}-point milestone</small>
      </div><span className="impact-total"><Award size={16} /> {rewards.total_points}</span>
    </section>
    <section className="card" id="issues">
      <div className="section-title"><div><h3>Your reported issues</h3><div className="metric-note" style={{ marginTop: 5 }}>Review status, priority, and recent activity.</div></div><SearchBox value={searchTerm} onChange={setSearchTerm} /></div>
      {loading ? <LoadingRows /> : visibleComplaints.length === 0 ? <div className="empty-state"><div className="empty-icon"><FileText size={20} /></div>{searchTerm ? 'No issues match your search.' : 'No issues reported yet. Use “Report an issue” to get started.'}</div> :
        <div className="table-container"><table><thead><tr><th>Ticket</th><th>Issue</th><th>Category</th><th>Status</th><th>Priority</th><th>Reported</th><th /></tr></thead><tbody>
          {visibleComplaints.map((item) => <tr key={item.id}><td><span className="ticket-id">{item.ticket_id}</span></td><td><strong>{item.title}</strong><span className="cell-sub"><MapPin size={11} />{item.location}</span>{item.report_count > 1 && <span className="cell-sub">{item.report_count} matching reports</span>}</td><td>{item.category}{item.predicted_category && <span className="cell-sub"><Sparkles size={11} /> Suggested {item.predicted_category} · {Math.round((item.prediction_confidence || 0) * 100)}%</span>}</td><td><span className={`badge badge-${item.status}`}>{item.status.replaceAll('_', ' ')}</span></td><td><span className={`priority-${item.priority}`}>{item.priority}</span></td><td>{new Date(item.created_at).toLocaleDateString()}</td><td><button onClick={() => viewComplaintDetail(item)} className="btn-secondary table-action">View updates <ArrowUpRight size={13} /></button></td></tr>)}
        </tbody></table></div>}
    </section>

    {showModal && <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) { setShowModal(false); resetForm(); } }}><section className="modal-panel" role="dialog" aria-modal="true" aria-labelledby="new-issue-title">
      <div className="modal-header"><div><div className="page-eyebrow">New campus report</div><h2 id="new-issue-title">Tell us what needs attention.</h2><p>Your report goes to the right campus team for review.</p></div><button className="icon-button" onClick={() => { setShowModal(false); resetForm(); }} aria-label="Close">×</button></div>
      <form onSubmit={handleSubmit} className="form-stack">
        <div><label className="form-label" htmlFor="issue-title">Issue title</label><input id="issue-title" required minLength={5} maxLength={200} className="input-field" placeholder="e.g. Ceiling fan stopped working" value={title} onChange={(e) => setTitle(e.target.value)} /></div>
        <div><label className="form-label" htmlFor="issue-location">Campus location</label><input id="issue-location" required minLength={2} className="input-field" placeholder="Building, floor, and room" value={location} onChange={(e) => setLocation(e.target.value)} /></div>
        <div><label className="form-label" htmlFor="issue-description">What happened?</label><textarea id="issue-description" required minLength={10} maxLength={5000} rows={4} className="input-field" placeholder="Describe the issue and anything that would help the campus team respond." value={description} onChange={(e) => setDescription(e.target.value)} /><div className="field-hint">{description.length}/5000 characters</div></div>
        {(predicting || predictedCategory) && <div className="prediction-callout"><Sparkles size={17} /><div><strong>{predicting ? 'Reviewing your description…' : confidence >= 45 ? `Suggested team: ${predictedCategory}` : 'Needs a quick team review'}</strong><span>{predicting ? 'The category suggestion will appear shortly.' : confidence >= 45 ? `Model ranking signal: ${confidence}%. You can change the category below.` : 'The suggestion is uncertain. Your report will be sent for manual triage.'}</span></div></div>}
        <div><label className="form-label" htmlFor="issue-category">Category <span className="optional-label">(optional)</span></label><select id="issue-category" className="input-field" value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)}><option value="">{confidence >= 45 && predictedCategory ? `Use suggestion: ${predictedCategory}` : 'Let the campus team triage this'}</option>{CATEGORIES.map((category) => <option value={category} key={category}>{category}</option>)}</select></div>
        <div><label className="form-label" htmlFor="issue-attachment">Photo or document <span className="optional-label">(optional · max 10 MB)</span></label><input id="issue-attachment" type="file" accept="image/jpeg,image/png,image/webp,application/pdf" className="input-field" onChange={handleAttachment} />{attachmentUrl && <div className="field-hint">Attachment uploaded and ready.</div>}</div>
        <div className="form-actions"><button type="button" className="btn-secondary" onClick={() => { setShowModal(false); resetForm(); }}>Cancel</button><button type="submit" disabled={submitting || predicting} className="btn-primary"><Send size={15} />{submitting ? 'Submitting…' : 'Submit report'}</button></div>
      </form>
    </section></div>}

    {selectedComplaint && <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelectedComplaint(null); }}><section className="modal-panel detail-panel" role="dialog" aria-modal="true" aria-labelledby="detail-title">
      <div className="modal-header"><div><div className="page-eyebrow">{selectedComplaint.ticket_id}</div><h2 id="detail-title">{selectedComplaint.title}</h2><p><MapPin size={12} /> {selectedComplaint.location} · {selectedComplaint.category}</p></div><button className="icon-button" onClick={() => setSelectedComplaint(null)} aria-label="Close">×</button></div>
      <div className="detail-summary"><div><span className="form-label">Current status</span><span className={`badge badge-${selectedComplaint.status}`}>{selectedComplaint.status.replaceAll('_', ' ')}</span></div><div><span className="form-label">Priority</span><span className={`priority-${selectedComplaint.priority}`}>{selectedComplaint.priority}</span></div></div>
      <ComplaintProgress status={selectedComplaint.status} /><div className="description-box">{selectedComplaint.description}</div>
      {selectedComplaint.attachment_url && <a className="attachment-link" href={`${API_ORIGIN}/api/v1/complaints/attachments/${encodeURIComponent(selectedComplaint.attachment_url.split('/').pop())}`} target="_blank" rel="noreferrer">View submitted attachment <ArrowUpRight size={13} /></a>}
      <h3 className="timeline-title">Activity & updates</h3>
      {timelineLoading ? (
        <div className="loading-rows" role="status" aria-label="Loading activity"><span /><span /></div>
      ) : timeline.length === 0 ? (
        <div className="empty-state compact">No updates have been added yet.</div>
      ) : (
        <div className="timeline-list">
          {timeline.map((entry) => (
            <article className="timeline-item" key={entry.id}>
              <span className="timeline-dot" />
              <strong>{entry.action.replaceAll('_', ' ')}</strong>
              <span className="timeline-meta">{entry.actor?.full_name || 'CampusFix'} · {new Date(entry.created_at).toLocaleString()}</span>
              {entry.comment && <p>{entry.comment}</p>}
            </article>
          ))}
        </div>
      )}
      {['RESOLVED', 'CLOSED'].includes(selectedComplaint.status) && <div className="feedback-panel"><h3>Rate the resolution</h3>{existingFeedback ? <div><strong>{'★'.repeat(existingFeedback.rating)}{'☆'.repeat(5 - existingFeedback.rating)} · {existingFeedback.rating}/5</strong>{existingFeedback.comments && <p>{existingFeedback.comments}</p>}<div className="metric-note">Thanks, your feedback has been recorded.</div></div> : <form onSubmit={handleFeedbackSubmit} className="form-stack"><div><label className="form-label" htmlFor="rating">How well was this issue resolved?</label><select id="rating" value={feedbackRating} onChange={(e) => setFeedbackRating(e.target.value)} className="input-field"><option value="5">5 · Excellent</option><option value="4">4 · Good</option><option value="3">3 · Fair</option><option value="2">2 · Poor</option><option value="1">1 · Needs improvement</option></select></div><textarea className="input-field" rows={2} maxLength={2000} placeholder="Share a comment about the staff response (optional)" value={feedbackComments} onChange={(e) => setFeedbackComments(e.target.value)} /><div className="form-actions"><button type="submit" className="btn-primary">Send rating</button>{selectedComplaint.status === 'RESOLVED' && <button type="button" className="btn-secondary" onClick={() => handleReopen(selectedComplaint.id)}><AlertTriangle size={14} /> Reopen issue</button>}</div></form>}</div>}
    </section></div>}
  </div>;
};

function Metric({ label, value, note, icon, tone = '' }) { return <div className="metric-card"><div className="metric-top">{label}<span className={`metric-icon ${tone}`}>{icon}</span></div><div className="metric-value">{value}</div><div className="metric-note">{note}</div></div>; }
function SearchBox({ value, onChange }) { return <div className="search-control"><Search size={15} /><input aria-label="Search issues" placeholder="Search issues" value={value} onChange={(event) => onChange(event.target.value)} /></div>; }
function LoadingRows() { return <div className="loading-rows" role="status"><span /><span /><span /></div>; }
function ComplaintProgress({ status }) {
  const terminalIndex = status === 'REJECTED' ? -1 : STATUS_STEPS.indexOf(status);
  return <div className="progress-track" aria-label={`Complaint progress: ${status}`}>{STATUS_STEPS.map((step, index) => <div className={`progress-step ${index <= terminalIndex ? 'complete' : ''} ${index === terminalIndex ? 'current' : ''}`} key={step}><span className="progress-node">{index < terminalIndex ? <CheckCircle2 size={13} /> : index + 1}</span><span>{step.replaceAll('_', ' ')}</span></div>)}</div>;
}
