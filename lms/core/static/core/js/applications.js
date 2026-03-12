(function () {
    const csrfToken = document.getElementById('csrfToken')?.value || '';
    const viewModal = document.getElementById('viewApplicationModal');
    const viewModalClose = document.getElementById('viewModalClose');
    const viewModalActions = document.getElementById('viewModalActions');
    let currentTab = 'pending';

    if (!viewModal) {
        return;
    }

    // Tab functionality
    const tabs = document.querySelectorAll('.app-tab');
    const sections = document.querySelectorAll('.app-section');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;
            
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            sections.forEach(section => {
                section.classList.remove('active');
                if (section.id === targetTab + 'Section') {
                    section.classList.add('active');
                }
            });
            
            currentTab = targetTab;
        });
    });

    function escapeHtml(value) {
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function openViewModal() {
        viewModal.classList.add('open');
        viewModal.setAttribute('aria-hidden', 'false');
    }

    function closeViewModal() {
        viewModal.classList.remove('open');
        viewModal.setAttribute('aria-hidden', 'true');
    }

    function populateViewModalFromButton(btn) {
        const appId = btn.dataset.id;
        
        document.getElementById('viewFullName').textContent = btn.dataset.applicant || '—';
        document.getElementById('viewEmail').textContent = btn.dataset.email || '—';
        document.getElementById('viewPhone').textContent = btn.dataset.phone || '—';
        document.getElementById('viewDob').textContent = btn.dataset.dob || '—';
        document.getElementById('viewGender').textContent = btn.dataset.gender || '—';
        document.getElementById('viewNationality').textContent = btn.dataset.nationality || '—';
        document.getElementById('viewAddress').textContent = btn.dataset.address || '—';
        document.getElementById('viewAltContact').textContent = btn.dataset.altContact || '—';
        
        document.getElementById('viewProgram').textContent = btn.dataset.program || '—';
        document.getElementById('viewIntakeYear').textContent = btn.dataset.intakeYear || '—';
        document.getElementById('viewIntakeSem').textContent = btn.dataset.intakeSem || '—';
        document.getElementById('viewEducation').textContent = btn.dataset.education || '—';
        document.getElementById('viewGpa').textContent = btn.dataset.gpa || '—';
        document.getElementById('viewInstitution').textContent = btn.dataset.institution || '—';
        document.getElementById('viewScholarship').textContent = btn.dataset.scholarship || '—';
        document.getElementById('viewStudyMode').textContent = btn.dataset.studyMode || '—';
        
        document.getElementById('viewSource').textContent = btn.dataset.source || '—';
        document.getElementById('viewLeadStatus').textContent = btn.dataset.leadStatus || '—';
        document.getElementById('viewCounselor').textContent = btn.dataset.counselor || '—';
        document.getElementById('viewFollowup').textContent = btn.dataset.followup || '—';
        document.getElementById('viewNotes').textContent = btn.dataset.notes || '—';
        
        document.getElementById('viewAppId').textContent = `A${String(appId).padStart(4, '0')}`;
        document.getElementById('viewSubmitted').textContent = btn.dataset.submitted || '—';
        document.getElementById('viewStatus').textContent = 'Pending';
        
        document.getElementById('viewModalTitle').textContent = 
            `Application #${String(appId).padStart(4, '0')}`;
        
        // Show actions based on current tab
        updateModalActions(appId, 'pending');
    }

    function updateModalActions(appId, status) {
        let actionsHtml = '';
        
        if (currentTab === 'pending') {
            actionsHtml = `
                <button type="button" class="action-btn reject-btn" onclick="handleReject(${appId})">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    Reject
                </button>
                <button type="button" class="action-btn approve-btn" onclick="handleApprove(${appId})">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="20 6 9 17 4 12"/></svg>
                    Approve
                </button>
            `;
        } else if (currentTab === 'rejected') {
            actionsHtml = `
                <button type="button" class="action-btn delete-btn" onclick="handlePermanentDelete(${appId})">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    Delete
                </button>
                <button type="button" class="action-btn restore-btn" onclick="handleRestore(${appId})">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
                    Restore
                </button>
            `;
        }
        
        viewModalActions.innerHTML = actionsHtml;
    }

    function openViewApplication(btn) {
        populateViewModalFromButton(btn);
        openViewModal();
    }

    // Approve handler
    window.handleApprove = async function(appId) {
        const confirmed = window.confirm('Are you sure you want to approve this application?');
        if (!confirmed) return;

        try {
            const response = await fetch(`/applications/${appId}/approve/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-CSRFToken': csrfToken,
                },
                body: new URLSearchParams({ csrfmiddlewaretoken: csrfToken }).toString(),
            });

            const result = await response.json().catch(() => ({}));
            if (!response.ok || !result.success) {
                throw new Error(result.error || 'Unable to approve application.');
            }

            alert('Application approved successfully!');
            closeViewModal();
            window.location.reload();
        } catch (error) {
            alert(error.message || 'Approve failed.');
        }
    };

    // Reject handler
    window.handleReject = async function(appId) {
        const confirmed = window.confirm('Are you sure you want to reject this application?');
        if (!confirmed) return;

        try {
            const response = await fetch(`/applications/${appId}/reject/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-CSRFToken': csrfToken,
                },
                body: new URLSearchParams({ csrfmiddlewaretoken: csrfToken }).toString(),
            });

            const result = await response.json().catch(() => ({}));
            if (!response.ok || !result.success) {
                throw new Error(result.error || 'Unable to reject application.');
            }

            alert('Application rejected.');
            closeViewModal();
            window.location.reload();
        } catch (error) {
            alert(error.message || 'Reject failed.');
        }
    };

    // Restore handler
    window.handleRestore = async function(appId) {
        const confirmed = window.confirm('Restore this application to pending?');
        if (!confirmed) return;

        try {
            const response = await fetch(`/applications/${appId}/restore/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-CSRFToken': csrfToken,
                },
                body: new URLSearchParams({ csrfmiddlewaretoken: csrfToken }).toString(),
            });

            const result = await response.json().catch(() => ({}));
            if (!response.ok || !result.success) {
                throw new Error(result.error || 'Unable to restore application.');
            }

            alert('Application restored to pending.');
            closeViewModal();
            window.location.reload();
        } catch (error) {
            alert(error.message || 'Restore failed.');
        }
    };

    // Permanent delete handler
    window.handlePermanentDelete = async function(appId) {
        const confirmed = window.confirm('WARNING: This will permanently delete the application and lead data. This action cannot be undone.');
        if (!confirmed) return;

        try {
            const response = await fetch(`/applications/${appId}/permanent-delete/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-CSRFToken': csrfToken,
                },
                body: new URLSearchParams({ csrfmiddlewaretoken: csrfToken }).toString(),
            });

            const result = await response.json().catch(() => ({}));
            if (!response.ok || !result.success) {
                throw new Error(result.error || 'Unable to delete application.');
            }

            alert('Application permanently deleted.');
            closeViewModal();
            window.location.reload();
        } catch (error) {
            alert(error.message || 'Delete failed.');
        }
    };

    // Event bindings
    function bindCardActions() {
        document.querySelectorAll('.app-view-btn').forEach(button => {
            if (button.dataset.bound) return;
            button.dataset.bound = '1';
            button.addEventListener('click', () => openViewApplication(button));
        });

        document.querySelectorAll('.app-approve-btn').forEach(button => {
            if (button.dataset.bound) return;
            button.dataset.bound = '1';
            button.addEventListener('click', async () => {
                await window.handleApprove(button.dataset.id);
            });
        });

        document.querySelectorAll('.app-reject-btn').forEach(button => {
            if (button.dataset.bound) return;
            button.dataset.bound = '1';
            button.addEventListener('click', async () => {
                await window.handleReject(button.dataset.id);
            });
        });

        document.querySelectorAll('.app-restore-btn').forEach(button => {
            if (button.dataset.bound) return;
            button.dataset.bound = '1';
            button.addEventListener('click', async () => {
                await window.handleRestore(button.dataset.id);
            });
        });

        document.querySelectorAll('.app-permanent-delete-btn').forEach(button => {
            if (button.dataset.bound) return;
            button.dataset.bound = '1';
            button.addEventListener('click', async () => {
                await window.handlePermanentDelete(button.dataset.id);
            });
        });
    }

    viewModalClose?.addEventListener('click', closeViewModal);
    viewModal.querySelector('[data-close="true"]')?.addEventListener('click', closeViewModal);

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && viewModal.classList.contains('open')) {
            closeViewModal();
        }
    });

    bindCardActions();
})();
