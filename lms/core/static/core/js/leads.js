(function () {
    const csrfToken = document.getElementById('csrfToken')?.value || '';
    const modal = document.getElementById('leadModal');
    const modalTitle = document.getElementById('leadModalTitle');
    const modalClose = document.getElementById('leadModalClose');
    const modalForm = document.getElementById('leadModalForm');
    const modalLeadId = document.getElementById('modalLeadId');
    const modalFirstName = document.getElementById('modalFirstName');
    const modalLastName = document.getElementById('modalLastName');
    const modalEmail = document.getElementById('modalEmail');
    const modalPhone = document.getElementById('modalPhone');
    const modalProgramInterest = document.getElementById('modalProgramInterest');
    const modalStatus = document.getElementById('modalStatus');
    const modalSource = document.getElementById('modalSource');
    const modalNotes = document.getElementById('modalNotes');
    const editButton = document.getElementById('leadModalEditBtn');
    const saveButton = document.getElementById('leadModalSaveBtn');

    if (!modal || !modalForm) {
        return;
    }

    function buildSourceOptions() {
        const sourceChoices = window.leadCrudConfig?.sourceChoices || [];
        modalSource.innerHTML = sourceChoices
            .map((item) => `<option value="${item.value}">${item.label}</option>`)
            .join('');
    }

    function setEditMode(editable) {
        [modalFirstName, modalLastName, modalEmail, modalPhone, modalProgramInterest, modalStatus, modalSource, modalNotes]
            .forEach((field) => {
                field.disabled = !editable;
            });
        editButton.hidden = editable;
        saveButton.hidden = !editable;
    }

    function openModal() {
        modal.classList.add('open');
        modal.setAttribute('aria-hidden', 'false');
    }

    function closeModal() {
        modal.classList.remove('open');
        modal.setAttribute('aria-hidden', 'true');
        setEditMode(false);
    }

    function attachCloseHandlers() {
        modalClose?.addEventListener('click', closeModal);
        modal.querySelector('[data-close="true"]')?.addEventListener('click', closeModal);
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && modal.classList.contains('open')) {
                closeModal();
            }
        });
    }

    async function fetchLeadDetails(leadId) {
        const response = await fetch(`/leads/${leadId}/`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        });

        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Unable to load lead details.');
        }
        return data.lead;
    }

    function fillModal(lead) {
        modalLeadId.value = lead.lead_id;
        modalFirstName.value = lead.first_name || '';
        modalLastName.value = lead.last_name || '';
        modalEmail.value = lead.email || '';
        modalPhone.value = lead.phone || '';
        modalProgramInterest.value = lead.program_interest || '';
        modalStatus.value = lead.current_status || 'new';
        modalSource.value = lead.source || 'other';
        modalNotes.value = lead.notes || '';
    }

    async function handleViewOrEdit(leadId, shouldEdit) {
        try {
            const lead = await fetchLeadDetails(leadId);
            modalTitle.textContent = shouldEdit ? `Edit Lead #${lead.lead_id}` : `Lead Details #${lead.lead_id}`;
            fillModal(lead);
            setEditMode(shouldEdit);
            openModal();
        } catch (error) {
            alert(error.message || 'Could not open lead record.');
        }
    }

    function updateRowFromResponse(lead) {
        const row = document.querySelector(`.view-btn[data-id="${lead.lead_id}"]`)?.closest('tr');
        if (!row) {
            return;
        }

        const nameEl = row.querySelector('.lead-name');
        const emailEl = row.querySelector('.lead-email');
        const programCell = row.children[2];
        const badge = row.querySelector('.status-badge');

        if (nameEl) nameEl.textContent = lead.name;
        if (emailEl) emailEl.textContent = lead.email;
        if (programCell) programCell.textContent = lead.program_interest;

        if (badge) {
            badge.textContent = lead.status;
            badge.className = `status-badge status-${lead.status_key}`;
        }
    }

    async function submitUpdate(event) {
        event.preventDefault();

        const leadId = modalLeadId.value;
        const payload = new URLSearchParams({
            csrfmiddlewaretoken: csrfToken,
            first_name: modalFirstName.value.trim(),
            last_name: modalLastName.value.trim(),
            email: modalEmail.value.trim(),
            phone: modalPhone.value.trim(),
            program_interest: modalProgramInterest.value.trim(),
            current_status: modalStatus.value,
            source: modalSource.value,
            notes: modalNotes.value.trim(),
        });

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
            alert(result.error || 'Unable to update this lead.');
            return;
        }

        updateRowFromResponse(result.lead);
        closeModal();
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
            throw new Error(result.error || 'Unable to delete this lead.');
        }
    }

    function attachTableHandlers() {
        document.querySelectorAll('.view-btn').forEach((button) => {
            button.addEventListener('click', () => {
                handleViewOrEdit(button.dataset.id, false);
            });
        });

        document.querySelectorAll('.edit-btn').forEach((button) => {
            button.addEventListener('click', () => {
                handleViewOrEdit(button.dataset.id, true);
            });
        });

        document.querySelectorAll('.delete-btn').forEach((button) => {
            button.addEventListener('click', async () => {
                const leadId = button.dataset.id;
                const confirmed = window.confirm(`Delete lead #${leadId}? This action cannot be undone.`);
                if (!confirmed) {
                    return;
                }

                try {
                    await deleteLead(leadId);
                    const row = button.closest('tr');
                    row?.remove();
                } catch (error) {
                    alert(error.message || 'Delete failed.');
                }
            });
        });
    }

    editButton?.addEventListener('click', () => setEditMode(true));
    modalForm.addEventListener('submit', submitUpdate);

    buildSourceOptions();
    attachCloseHandlers();
    attachTableHandlers();
})();
