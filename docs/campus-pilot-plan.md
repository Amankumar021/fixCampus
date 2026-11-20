# CampusFix campus pilot plan

This plan is a proposed four-week operational pilot. A campus owner must approve the cohort, privacy notice, support route, and escalation contacts before real students use the system.

## Before launch

- Name an accountable campus service owner and one reviewer per issue category.
- Confirm the category list, buildings/locations, service hours, critical safety escalation path, and expected first-response windows.
- Use campus-managed accounts or approved SSO before broad access. Rotate all demo credentials, configure a production secret, TLS, backups, monitoring, and private attachment storage.
- Publish what is collected, who can view reports and evidence, how long records are kept, and where students can request help or removal.
- Train reviewers to correct categories. AI suggestions remain advisory; ambiguous and safety related reports go to human triage.
- Test account recovery with a campus-controlled SMTP provider and verify the reset link origin and sender.

## Four-week rollout

1. **Week 1 — staff rehearsal:** test one sample per category, attachments, triage, reassignment, staff deactivation, status notices, recovery, and restore from backup. Remove test data before pilot launch.
2. **Week 2 — limited cohort:** invite one or two academic blocks. Hold a daily 15-minute queue review and document duplicate reports, routing errors, and overdue work.
3. **Week 3 — calibrate:** review AI predictions against admin-confirmed categories, inspect per-category precision/recall and abstentions, address confusing forms, and adjust operational thresholds with service owners.
4. **Week 4 — decision:** compare service and student outcomes with the baseline, resolve high-risk issues, and record a go / extend / stop decision with an owner and due date for each follow-up.

## Measures and initial targets

Set baseline values with campus staff; these are pilot targets, not guarantees:

- At least 90% of reports receive a human triage decision within one business day.
- At least 80% of assignments are accepted or reassigned within the configured 24-hour response threshold.
- At least 80% of students who respond to the optional survey can find their ticket status and next step.
- Track time to first human response, time to resolution by category, reopen rate, duplicate rate, feedback response rate, overdue queue size, attachment access incidents, and inactive accounts.
- For ML, report reviewed sample count, class coverage, accuracy, macro F1, per-class precision/recall, abstention rate, and confusion matrix. Do not set a launch accuracy target until an independent, de-identified campus holdout set exists.

## Review and safety

- A staff reviewer confirms the final category; store that label separately from the model suggestion.
- Check class imbalance and reviewer consistency. Resolve label disagreements before treating the data as an evaluation set.
- Do not route emergency or immediate safety incidents solely through this app; display and document the campus emergency contact path.
- Review overdue items daily and contact the responsible department through its approved campus channel.
- Keep reward points capped and review unusual repeated-report patterns before changing rewards policy.
- At the end, export aggregate metrics, remove temporary pilot accounts, and apply the campus retention schedule to evidence and records.
