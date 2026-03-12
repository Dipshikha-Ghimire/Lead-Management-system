(function () {
    const csrfToken = document.getElementById('csrfToken')?.value || '';
    
    const viewModal = document.getElementById('leadViewModal');
    const viewModalClose = document.getElementById('leadViewModalClose');
    const viewModalActions = document.getElementById('leadViewModalActions');
    
    const editModal = document.getElementById('leadEditModal');
    const editModalClose = document.getElementById('leadEditModalClose');
    const editForm = document.getElementById('leadEditForm');
    const editCancelBtn = document.getElementById('leadEditCancelBtn');

    if (!viewModal || !editModal) {
        return;
    }

    // View Modal Functions
    function openViewModal() {
        viewModal.classList.add('open');
        viewModal.setAttribute('aria-hidden', 'false');
    }

    function closeViewModal() {
        viewModal.classList.remove('open');
        viewModal.setAttribute('aria-hidden', 'true');
    }

    function populateViewModal(btn) {
        document.getElementById('viewLeadName').textContent = btn.dataset.name || '—';
        document.getElementById('viewLeadEmail').textContent = btn.dataset.email || '—';
        document.getElementById('viewLeadPhone').textContent = btn.dataset.phone || '—';
        document.getElementById('viewLeadDob').textContent = btn.dataset.dob || '—';
        document.getElementById('viewLeadGender').textContent = btn.dataset.gender || '—';
        document.getElementById('viewLeadNationality').textContent = btn.dataset.nationality || '—';
        document.getElementById('viewLeadAddress').textContent = btn.dataset.address || '—';
        document.getElementById('viewLeadAltContact').textContent = btn.dataset.altContact || '—';
        
        document.getElementById('viewLeadProgram').textContent = btn.dataset.program || '—';
        document.getElementById('viewLeadIntakeYear').textContent = btn.dataset.intakeYear || '—';
        document.getElementById('viewLeadIntakeSem').textContent = btn.dataset.intakeSem || '—';
        document.getElementById('viewLeadEducation').textContent = btn.dataset.education || '—';
        document.getElementById('viewLeadGpa').textContent = btn.dataset.gpa || '—';
        document.getElementById('viewLeadInstitution').textContent = btn.dataset.institution || '—';
        document.getElementById('viewLeadScholarship').textContent = btn.dataset.scholarship || '—';
        document.getElementById('viewLeadStudyMode').textContent = btn.dataset.studyMode || '—';
        
        document.getElementById('viewLeadSource').textContent = btn.dataset.source || '—';
        document.getElementById('viewLeadStatus').textContent = btn.dataset.leadStatus || '—';
        document.getElementById('viewLeadCounselor').textContent = btn.dataset.counselor || '—';
        document.getElementById('viewLeadFollowup').textContent = btn.dataset.followup || '—';
        document.getElementById('viewLeadNotes').textContent = btn.dataset.notes || '—';
        
        document.getElementById('viewLeadId').textContent = `L${String(btn.dataset.id).padStart(4, '0')}`;
        document.getElementById('viewLeadDateCaptured').textContent = btn.dataset.dateCaptured || '—';
        
        document.getElementById('leadViewModalTitle').textContent = `Student Details - L${String(btn.dataset.id).padStart(4, '0')}`;
        
        viewModalActions.innerHTML = `
            <button type="button" class="action-btn edit-btn" onclick="openEditModal(${btn.dataset.id})">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-5" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
                Edit
            </button>
        `;
    }

    function openViewApplication(btn) {
        populateViewModal(btn);
        openViewModal();
    }

    // Edit Modal Functions
    function openEditModal() {
        const btn = document.querySelector('.lead-view-btn.active') || document.querySelector('.lead-edit-btn[data-id="' + document.getElementById('editLeadId').value + '"]');
        if (btn) {
            const viewBtn = document.querySelector(`.lead-view-btn[data-id="${btn.dataset.id}"]`);
            if (viewBtn) {
                document.getElementById('editLeadId').value = viewBtn.dataset.id;
                document.getElementById('editFirstName').value = viewBtn.dataset.name.split(' ')[0] || '';
                document.getElementById('editLastName').value = viewBtn.dataset.name.split(' ').slice(1).join(' ') || '';
                document.getElementById('editEmail').value = viewBtn.dataset.email || '';
                document.getElementById('editPhone').value = viewBtn.dataset.phone || '';
                document.getElementById('editDateOfBirth').value = viewBtn.dataset.dob || '';
                document.getElementById('editAddress').value = viewBtn.dataset.address || '';
                document.getElementById('editNationality').value = viewBtn.dataset.nationality || '';
                document.getElementById('editAlternateContact').value = viewBtn.dataset.altContact || '';
                document.getElementById('editProgramInterest').value = viewBtn.dataset.program || '';
                document.getElementById('editDesiredIntakeYear').value = viewBtn.dataset.intakeYear || '';
                document.getElementById('editHighestEducationLevel').value = viewBtn.dataset.education || '';
                document.getElementById('editGpaOrPercentage').value = viewBtn.dataset.gpa || '';
                document.getElementById('editPreviousInstitution').value = viewBtn.dataset.institution || '';
                document.getElementById('editNotes').value = viewBtn.dataset.notes || '';
                
                document.getElementById('leadEditModalTitle').textContent = `Edit Lead - L${String(viewBtn.dataset.id).padStart(4, '0')}`;
            }
        }
        closeViewModal();
        editModal.classList.add('open');
        editModal.setAttribute('aria-hidden', 'false');
    }

    window.openEditModal = function(leadId) {
        const btn = document.querySelector(`.lead-view-btn[data-id="${leadId}"]`);
        if (btn) {
            document.getElementById('editLeadId').value = btn.dataset.id;
            document.getElementById('editFirstName').value = btn.dataset.name.split(' ')[0] || '';
            document.getElementById('editLastName').value = btn.dataset.name.split(' ').slice(1).join(' ') || '';
            document.getElementById('editEmail').value = btn.dataset.email || '';
            document.getElementById('editPhone').value = btn.dataset.phone || '';
            document.getElementById('editDateOfBirth').value = btn.dataset.dob || '';
            document.getElementById('editAddress').value = btn.dataset.address || '';
            document.getElementById('editNationality').value = btn.dataset.nationality || '';
            document.getElementById('editAlternateContact').value = btn.dataset.altContact || '';
            document.getElementById('editProgramInterest').value = btn.dataset.program || '';
            document.getElementById('editDesiredIntakeYear').value = btn.dataset.intakeYear || '';
            document.getElementById('editHighestEducationLevel').value = btn.dataset.education || '';
            document.getElementById('editGpaOrPercentage').value = btn.dataset.gpa || '';
            document.getElementById('editPreviousInstitution').value = btn.dataset.institution || '';
            document.getElementById('editNotes').value = btn.dataset.notes || '';
            
            document.getElementById('leadEditModalTitle').textContent = `Edit Lead - L${String(btn.dataset.id).padStart(4, '0')}`;
        }
        closeViewModal();
        editModal.classList.add('open');
        editModal.setAttribute('aria-hidden', 'false');
    };

    function closeEditModal() {
        editModal.classList.remove('open');
        editModal.setAttribute('aria-hidden', 'true');
    }

    async function fetchLeadDetails(leadId) {
        const response = await fetch(`/leads/${leadId}/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Unable to load lead details.');
        }
        return data.lead;
    }

    async function handleEditClick(btn) {
        try {
            const lead = await fetchLeadDetails(btn.dataset.id);
            document.getElementById('editLeadId').value = lead.lead_id;
            document.getElementById('editFirstName').value = lead.first_name || '';
            document.getElementById('editLastName').value = lead.last_name || '';
            document.getElementById('editEmail').value = lead.email || '';
            document.getElementById('editPhone').value = lead.phone || '';
            document.getElementById('editDateOfBirth').value = lead.date_of_birth || '';
            document.getElementById('editAddress').value = lead.address || '';
            document.getElementById('editNationality').value = lead.nationality || '';
            document.getElementById('editAlternateContact').value = lead.alternate_contact || '';
            document.getElementById('editProgramInterest').value = lead.program_interest || '';
            document.getElementById('editDesiredIntakeYear').value = lead.desired_intake_year || '';
            document.getElementById('editIntakeSemester').value = lead.intake_semester || '';
            document.getElementById('editHighestEducationLevel').value = lead.highest_education_level || '';
            document.getElementById('editGpaOrPercentage').value = lead.gpa_or_percentage || '';
            document.getElementById('editPreviousInstitution').value = lead.previous_institution || '';
            document.getElementById('editScholarshipInterest').value = lead.scholarship_interest || '';
            document.getElementById('editPreferredStudyMode').value = lead.preferred_study_mode || '';
            document.getElementById('editStatus').value = lead.current_status || 'new';
            document.getElementById('editSource').value = lead.source || 'other';
            document.getElementById('editAssignedStaffId').value = lead.assigned_staff_id || '';
            document.getElementById('editFollowupDate').value = lead.followup_date || '';
            document.getElementById('editNotes').value = lead.notes || '';
            
            document.getElementById('leadEditModalTitle').textContent = `Edit Lead - L${String(lead.lead_id).padStart(4, '0')}`;
            
            editModal.classList.add('open');
            editModal.setAttribute('aria-hidden', 'false');
        } catch (error) {
            alert(error.message || 'Could not load lead details.');
        }
    }

    async function submitUpdate(event) {
        event.preventDefault();
        
        const leadId = document.getElementById('editLeadId').value;
        const payload = new URLSearchParams({
            csrfmiddlewaretoken: csrfToken,
            first_name: document.getElementById('editFirstName').value.trim(),
            last_name: document.getElementById('editLastName').value.trim(),
            email: document.getElementById('editEmail').value.trim(),
            phone: document.getElementById('editPhone').value.trim(),
            date_of_birth: document.getElementById('editDateOfBirth').value,
            gender: document.getElementById('editGender').value,
            address: document.getElementById('editAddress').value.trim(),
            nationality: document.getElementById('editNationality').value.trim(),
            alternate_contact: document.getElementById('editAlternateContact').value.trim(),
            program_interest: document.getElementById('editProgramInterest').value.trim(),
            desired_intake_year: document.getElementById('editDesiredIntakeYear').value,
            intake_semester: document.getElementById('editIntakeSemester').value,
            highest_education_level: document.getElementById('editHighestEducationLevel').value,
            gpa_or_percentage: document.getElementById('editGpaOrPercentage').value.trim(),
            previous_institution: document.getElementById('editPreviousInstitution').value.trim(),
            scholarship_interest: document.getElementById('editScholarshipInterest').value,
            preferred_study_mode: document.getElementById('editPreferredStudyMode').value,
            current_status: document.getElementById('editStatus').value,
            source: document.getElementById('editSource').value,
            assigned_staff_id: document.getElementById('editAssignedStaffId').value,
            followup_date: document.getElementById('editFollowupDate').value,
            notes: document.getElementById('editNotes').value.trim(),
        });

        try {
            const response = await fetch(`/leads/${leadId}/update/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-CSRFToken': csrfToken,
                },
                body: payload.toString(),
            });

            const result = await response.json().catch(() => ({}));
            if (!response.ok || !result.success) {
                throw new Error(result.error || 'Unable to update lead.');
            }

            alert('Lead updated successfully!');
            closeEditModal();
            window.location.reload();
        } catch (error) {
            alert(error.message || 'Update failed.');
        }
    }

    async function deleteLead(leadId) {
        const response = await fetch(`/leads/${leadId}/delete/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-CSRFToken': csrfToken,
            },
            body: new URLSearchParams({ csrfmiddlewaretoken: csrfToken }).toString(),
        });

        const result = await response.json().catch(() => ({}));
        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Unable to delete lead.');
        }
    }

    // Event Bindings
    function bindEvents() {
        document.querySelectorAll('.lead-view-btn').forEach(btn => {
            if (btn.dataset.bound) return;
            btn.dataset.bound = '1';
            btn.addEventListener('click', () => openViewApplication(btn));
        });

        document.querySelectorAll('.lead-edit-btn').forEach(btn => {
            if (btn.dataset.bound) return;
            btn.dataset.bound = '1';
            btn.addEventListener('click', () => handleEditClick(btn));
        });

        document.querySelectorAll('.lead-delete-btn').forEach(btn => {
            if (btn.dataset.bound) return;
            btn.dataset.bound = '1';
            btn.addEventListener('click', async () => {
                const leadId = btn.dataset.id;
                const confirmed = window.confirm(`Permanently delete this student? This action cannot be undone.`);
                if (!confirmed) return;
                
                const confirmed2 = window.confirm('Are you absolutely sure?');
                if (!confirmed2) return;

                try {
                    await deleteLead(leadId);
                    const row = btn.closest('tr');
                    row?.remove();
                } catch (error) {
                    alert(error.message || 'Delete failed.');
                }
            });
        });

        viewModalClose?.addEventListener('click', closeViewModal);
        viewModal.querySelector('[data-close="true"]')?.addEventListener('click', closeViewModal);
        
        editModalClose?.addEventListener('click', closeEditModal);
        editCancelBtn?.addEventListener('click', closeEditModal);
        editForm?.addEventListener('submit', submitUpdate);

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                if (viewModal.classList.contains('open')) closeViewModal();
                if (editModal.classList.contains('open')) closeEditModal();
            }
        });
    }

    bindEvents();
})();
