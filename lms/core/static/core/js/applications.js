(function () {
    const csrfToken = document.getElementById('csrfToken')?.value || '';
    const modal = document.getElementById('applicationModal');
    const modalTitle = document.getElementById('applicationModalTitle');
    const modalClose = document.getElementById('applicationModalClose');
    const modalForm = document.getElementById('applicationForm');
    const addButton = document.getElementById('addApplicationBtn');
    const editButton = document.getElementById('applicationModalEditBtn');
    const saveButton = document.getElementById('applicationModalSaveBtn');

    const appIdField = document.getElementById('applicationId');
    const leadField = document.getElementById('applicationLead');
    const programField = document.getElementById('applicationProgram');
    const statusField = document.getElementById('applicationStatus');
    const documentsField = document.getElementById('applicationDocumentsUrl');
    const leadFirstNameField = document.getElementById('applicationLeadFirstName');
    const leadLastNameField = document.getElementById('applicationLeadLastName');
    const leadEmailField = document.getElementById('applicationLeadEmail');
    const leadProgramInterestField = document.getElementById('applicationLeadProgramInterest');

    const tableBody = document.getElementById('applicationsTableBody');

    if (!modal || !modalForm || !tableBody) {
        return;
    }

    function setFormMode(mode) {
        const editable = mode === 'create' || mode === 'edit';
        [
            leadField,
            programField,
            statusField,
            documentsField,
            leadFirstNameField,
            leadLastNameField,
            leadEmailField,
            leadProgramInterestField,
        ].forEach((field) => {
            field.disabled = !editable;
        });

        editButton.hidden = mode !== 'view';
        saveButton.hidden = mode === 'view';
    }

    function openModal() {
        modal.classList.add('open');
        modal.setAttribute('aria-hidden', 'false');
    }

    function closeModal() {
        modal.classList.remove('open');
        modal.setAttribute('aria-hidden', 'true');
    }

    function resetForm() {
        appIdField.value = '';
        leadField.value = '';
        programField.value = '';
        statusField.value = 'pending';
        documentsField.value = '';
        leadFirstNameField.value = '';
        leadLastNameField.value = '';
        leadEmailField.value = '';
        leadProgramInterestField.value = '';
    }

    function clearEmptyRow() {
        const emptyRow = document.getElementById('emptyApplicationsRow');
        if (emptyRow) {
            emptyRow.remove();
        }
    }

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function selectedLeadText() {
        const option = leadField.options[leadField.selectedIndex];
        return option ? option.textContent.trim() : '';
    }

    function renderRow(application) {
        return `
            <tr data-app-id="${application.id}">
                <td class="app-id">A${String(application.id).padStart(4, '0')}</td>
                <td>
                    <div class="applicant-name">${escapeHtml(application.applicant)}</div>
                    <small class="applicant-email">${escapeHtml(application.email)}</small>
                </td>
                <td class="program-name">${escapeHtml(application.program)}</td>
                <td><span class="status-badge status-${escapeHtml(application.status_key)}">${escapeHtml(application.status)}</span></td>
                <td class="submitted-date">${escapeHtml(application.submitted)}</td>
                <td class="col-actions">
                    <div class="action-btns workflow-btns">
                        <button type="button" class="action-btn review-btn app-action-btn" data-action="review" title="Mark reviewed and set lead qualified" data-id="${application.id}">Review</button>
                        <button type="button" class="action-btn accept-btn app-action-btn" data-action="accept" title="Accept and set lead converted" data-id="${application.id}">Accept</button>
                        <button type="button" class="action-btn reject-btn app-action-btn" data-action="reject" title="Reject and set lead dropped" data-id="${application.id}">Reject</button>
                    </div>
                    <div class="action-btns">
                        <button type="button" class="action-btn app-view-btn" title="View" data-id="${application.id}">View</button>
                        <button type="button" class="action-btn app-edit-btn" title="Edit" data-id="${application.id}">Edit</button>
                        <button type="button" class="action-btn delete-btn app-delete-btn" title="Delete" data-id="${application.id}">Delete</button>
                    </div>
                </td>
            </tr>
        `;
    }

    function applyRowUpdate(application) {
        const row = tableBody.querySelector(`tr[data-app-id="${application.id}"]`);
        if (!row) {
            clearEmptyRow();
            tableBody.insertAdjacentHTML('afterbegin', renderRow(application));
            return;
        }

        row.querySelector('.applicant-name').textContent = application.applicant;
        row.querySelector('.applicant-email').textContent = application.email;
        row.querySelector('.program-name').textContent = application.program;
        row.querySelector('.submitted-date').textContent = application.submitted;

        const badge = row.querySelectorAll('.status-badge')[0];
        badge.textContent = application.status;
        badge.className = `status-badge status-${application.status_key}`;
    }

    async function getApplication(appId) {
        const response = await fetch(`/applications/${appId}/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Unable to load application details.');
        }
        return data.application;
    }

    function fillForm(application) {
        appIdField.value = application.app_id;
        leadField.value = String(application.lead_id);
        programField.value = String(application.program_id);
        statusField.value = application.status;
        documentsField.value = application.documents_url || '';
        leadFirstNameField.value = application.lead_first_name || '';
        leadLastNameField.value = application.lead_last_name || '';
        leadEmailField.value = application.lead_email || '';
        leadProgramInterestField.value = application.lead_program_interest || '';
    }

    async function openForViewOrEdit(appId, mode) {
        try {
            const application = await getApplication(appId);
            fillForm(application);
            modalTitle.textContent = mode === 'edit' ? `Edit Application #${application.app_id}` : `Application #${application.app_id}`;
            setFormMode(mode);
            openModal();
        } catch (error) {
            alert(error.message || 'Could not open application.');
        }
    }

    function collectPayload() {
        return new URLSearchParams({
            csrfmiddlewaretoken: csrfToken,
            lead_id: leadField.value,
            program_id: programField.value,
            status: statusField.value,
            documents_url: documentsField.value.trim(),
            lead_first_name: leadFirstNameField.value.trim(),
            lead_last_name: leadLastNameField.value.trim(),
            lead_email: leadEmailField.value.trim(),
            lead_program_interest: leadProgramInterestField.value.trim(),
        });
    }

    async function createApplication() {
        const payload = collectPayload();
        const response = await fetch('/applications/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-CSRFToken': csrfToken,
            },
            body: payload.toString(),
        });

        const result = await response.json().catch(() => ({}));
        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Unable to create application.');
        }

        return result.application;
    }

    async function updateApplication(appId) {
        const payload = collectPayload();
        const response = await fetch(`/applications/${appId}/update/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-CSRFToken': csrfToken,
            },
            body: payload.toString(),
        });

        const result = await response.json().catch(() => ({}));
        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Unable to update application.');
        }

        return result.application;
    }

    async function deleteApplication(appId) {
        const response = await fetch(`/applications/${appId}/delete/`, {
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
    }

    async function runWorkflowAction(appId, action) {
        const response = await fetch(`/applications/${appId}/action/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-CSRFToken': csrfToken,
            },
            body: new URLSearchParams({
                csrfmiddlewaretoken: csrfToken,
                action,
            }).toString(),
        });

        const result = await response.json().catch(() => ({}));
        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Unable to run action.');
        }

        return result.application;
    }

    function bindRowActions() {
        tableBody.querySelectorAll('.app-view-btn').forEach((button) => {
            if (button.dataset.bound) return;
            button.dataset.bound = '1';
            button.addEventListener('click', () => openForViewOrEdit(button.dataset.id, 'view'));
        });

        tableBody.querySelectorAll('.app-edit-btn').forEach((button) => {
            if (button.dataset.bound) return;
            button.dataset.bound = '1';
            button.addEventListener('click', () => openForViewOrEdit(button.dataset.id, 'edit'));
        });

        tableBody.querySelectorAll('.app-delete-btn').forEach((button) => {
            if (button.dataset.bound) return;
            button.dataset.bound = '1';
            button.addEventListener('click', async () => {
                const appId = button.dataset.id;
                const confirmed = window.confirm(`Delete application #${appId}? This action cannot be undone.`);
                if (!confirmed) {
                    return;
                }

                try {
                    await deleteApplication(appId);
                    const row = tableBody.querySelector(`tr[data-app-id="${appId}"]`);
                    row?.remove();
                } catch (error) {
                    alert(error.message || 'Delete failed.');
                }
            });
        });

        tableBody.querySelectorAll('.app-action-btn').forEach((button) => {
            if (button.dataset.bound) return;
            button.dataset.bound = '1';
            button.addEventListener('click', async () => {
                const appId = button.dataset.id;
                const action = button.dataset.action;
                try {
                    const updated = await runWorkflowAction(appId, action);
                    applyRowUpdate(updated);
                } catch (error) {
                    alert(error.message || 'Action failed.');
                }
            });
        });
    }

    addButton?.addEventListener('click', () => {
        resetForm();
        modalTitle.textContent = 'Add Application';
        setFormMode('create');
        openModal();
    });

    editButton?.addEventListener('click', () => {
        setFormMode('edit');
        modalTitle.textContent = `Edit Application #${appIdField.value}`;
    });

    modalForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        try {
            const appId = appIdField.value;
            const application = appId ? await updateApplication(appId) : await createApplication();
            applyRowUpdate(application);
            bindRowActions();
            closeModal();
        } catch (error) {
            alert(error.message || 'Save failed.');
        }
    });

    modalClose?.addEventListener('click', closeModal);
    modal.querySelector('[data-close="true"]')?.addEventListener('click', closeModal);

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modal.classList.contains('open')) {
            closeModal();
        }
    });

    bindRowActions();
})();
