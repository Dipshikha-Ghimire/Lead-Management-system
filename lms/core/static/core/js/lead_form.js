let currentStep = 1;
const totalSteps = 4;

const eduDocLabels = {
    'high_school': 'SEE/ SLC Certificate',
    'bachelors': "Bachelor's Certificate & Marksheet",
    'masters': "Master's Certificate & Marksheet",
    'diploma_certificate': 'Diploma Certificate & Transcripts',
};

const eduLevelSelect = document.getElementById('eduLevel');
const eduDocField = document.getElementById('eduDocField');
const eduDocLabel = document.getElementById('eduDocLabel');
const eduDocInput = document.getElementById('eduDoc');
const eduDocInfo = document.getElementById('eduDocInfo');
const eduDocErr = document.getElementById('eduDocErr');

if (eduLevelSelect) {
    eduLevelSelect.addEventListener('change', function() {
        const value = this.value;
        if (value && eduDocLabels[value]) {
            eduDocField.style.display = 'block';
            eduDocLabel.textContent = eduDocLabels[value];
            eduDocInput.required = true;
            if (eduDocErr) eduDocErr.classList.remove('show');
            eduDocInput.classList.remove('error');
        } else {
            eduDocField.style.display = 'none';
            eduDocInput.required = false;
            eduDocInput.value = '';
            eduDocInfo.textContent = '';
            if (eduDocErr) eduDocErr.classList.remove('show');
            eduDocInput.classList.remove('error');
        }
    });
}

if (eduDocInput) {
    eduDocInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const maxSize = 5 * 1024 * 1024;
            if (file.size > maxSize) {
                alert('File size must be less than 5MB');
                this.value = '';
                eduDocInfo.textContent = '';
                return;
            }
            eduDocInfo.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
            if (eduDocErr) eduDocErr.classList.remove('show');
            this.classList.remove('error');
        } else {
            eduDocInfo.textContent = '';
        }
    });
}

// Source tag toggle
document.querySelectorAll('.tag-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tag-btn').forEach((tagButton) => tagButton.classList.remove('selected'));
        btn.classList.add('selected');
        document.getElementById('leadSource').value = btn.dataset.val;
        document.getElementById('leadSourceErr').classList.remove('show');
    });
});

function getSelectedText(selectId) {
    const selectEl = document.getElementById(selectId);
    if (!selectEl || selectEl.selectedIndex < 0) return '';
    return (selectEl.options[selectEl.selectedIndex]?.textContent || '').trim();
}

function getCheckedRadioLabel(groupName) {
    const selected = document.querySelector(`input[name="${groupName}"]:checked`);
    if (!selected) return '';
    const label = selected.closest('label');
    const labelText = (label?.textContent || '').trim();
    return labelText || selected.value;
}

function getSelectedSourceLabel() {
    const selectedTag = document.querySelector('.tag-btn.selected');
    if (!selectedTag) return '';
    return selectedTag.dataset.label || (selectedTag.textContent || '').trim() || selectedTag.dataset.val || '';
}

function validateStep(step) {
    let valid = true;

    const clearErr = (id, errId) => {
        const el = document.getElementById(id);
        el.classList.remove('error');
        document.getElementById(errId).classList.remove('show');
    };

    const showErr = (id, errId) => {
        const el = document.getElementById(id);
        el.classList.add('error');
        document.getElementById(errId).classList.add('show');
        valid = false;
    };

    if (step === 1) {
        ['firstName', 'lastName', 'email', 'phone'].forEach((field) => clearErr(field, `${field}Err`));
        if (!document.getElementById('firstName').value.trim()) showErr('firstName', 'firstNameErr');
        if (!document.getElementById('lastName').value.trim()) showErr('lastName', 'lastNameErr');
        const email = document.getElementById('email').value.trim();
        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) showErr('email', 'emailErr');
        if (!document.getElementById('phone').value.trim()) showErr('phone', 'phoneErr');
    }

    if (step === 2) {
        ['program', 'eduLevel'].forEach((field) => clearErr(field, `${field}Err`));
        if (!document.getElementById('program').value) showErr('program', 'programErr');
        if (!document.getElementById('eduLevel').value) showErr('eduLevel', 'eduLevelErr');

        if (eduDocErr) eduDocErr.classList.remove('show');
        if (eduDocInput) eduDocInput.classList.remove('error');
        const educationSelected = document.getElementById('eduLevel').value;
        const hasEduDoc = eduDocInput && eduDocInput.files && eduDocInput.files.length > 0;
        if (educationSelected && !hasEduDoc) {
            if (eduDocErr) eduDocErr.classList.add('show');
            if (eduDocInput) eduDocInput.classList.add('error');
            valid = false;
        }
    }

    if (step === 3) {
        document.getElementById('leadSourceErr').classList.remove('show');
        if (!document.getElementById('leadSource').value) {
            document.getElementById('leadSourceErr').classList.add('show');
            valid = false;
        }
    }

    return valid;
}

function populateReview() {
    const mode = getCheckedRadioLabel('mode') || '—';
    const scholarship = getCheckedRadioLabel('scholarship') || '—';
    const leadStatusEl = document.getElementById('leadStatus');
    const leadStatusValue = leadStatusEl?.value || '';
    const leadStatusLabel = leadStatusEl?.options?.[leadStatusEl.selectedIndex]?.textContent?.trim() || '';
    const leadStatus = leadStatusLabel || leadStatusValue.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase()) || '—';
    const genderDisplay = getSelectedText('gender') || '—';
    const programDisplay = getSelectedText('program') || document.getElementById('program').value || '—';
    const educationDisplay = getSelectedText('eduLevel') || '—';
    const counselorDisplay = getSelectedText('counselor') || '—';
    const sourceDisplay = getSelectedSourceLabel() || '—';
    const eduDocDisplay = document.getElementById('eduDoc').files[0]?.name || '—';

    const data = [
        { label: 'Full Name', value: `${document.getElementById('firstName').value} ${document.getElementById('lastName').value}`, full: false },
        { label: 'Email', value: document.getElementById('email').value, full: false },
        { label: 'Phone', value: document.getElementById('phone').value, full: false },
        { label: 'Gender', value: genderDisplay, full: false },
        { label: 'Program', value: programDisplay, full: true },
        { label: 'Education', value: educationDisplay, full: false },
        { label: 'Education Doc', value: eduDocDisplay, full: false },
        { label: 'GPA / %', value: document.getElementById('gpa').value || '—', full: false },
        { label: 'Scholarship Interest', value: scholarship, full: false },
        { label: 'Study Mode', value: mode, full: false },
        { label: 'Lead Source', value: sourceDisplay, full: false },
        { label: 'Lead Status', value: leadStatus, full: false },
        { label: 'Counselor', value: counselorDisplay, full: false },
        { label: 'Follow-up Date', value: document.getElementById('followupDate').value || '—', full: false },
        { label: 'Notes', value: document.getElementById('notes').value || '—', full: true },
    ];

    document.getElementById('reviewGrid').innerHTML = data
        .map((item) => `
      <div class="review-item ${item.full ? 'full' : ''}">
        <div class="review-label">${item.label}</div>
        <div class="review-value">${item.value}</div>
      </div>
    `)
        .join('');
}

function updateStepsNav() {
    document.querySelectorAll('.step-item').forEach((el) => {
        const step = parseInt(el.dataset.step, 10);
        el.classList.remove('active', 'done');
        if (step === currentStep) el.classList.add('active');
        if (step < currentStep) el.classList.add('done');
    });
}

function goToStep(targetStep) {
    if (Number.isNaN(targetStep) || targetStep < 1 || targetStep > totalSteps) return;
    if (targetStep === currentStep) return;

    // Moving forward requires current step validation.
    if (targetStep > currentStep && !validateStep(currentStep)) return;

    if (targetStep === totalSteps && currentStep < totalSteps) {
        populateReview();
    }

    currentStep = targetStep;
    updateUI();
}

function goNext() {
    if (!validateStep(currentStep)) return;
    if (currentStep === 4) {
        submitForm();
        return;
    }
    if (currentStep === totalSteps - 1) populateReview();
    currentStep++;
    updateUI();
}

function goBack() {
    if (currentStep <= 1) return;
    currentStep--;
    updateUI();
}

function updateUI() {
    document.querySelectorAll('.form-step').forEach((step) => step.classList.remove('active'));
    document.getElementById(`step${currentStep}`)?.classList.add('active');
    updateStepsNav();

    document.getElementById('stepCounter').textContent = `Step ${currentStep} of ${totalSteps}`;
    document.getElementById('btnBack').style.visibility = currentStep > 1 ? 'visible' : 'hidden';
    document.getElementById('btnNext').textContent = currentStep === totalSteps ? '🚀 Submit Lead' : 'Continue →';
}

async function submitForm() {
    try {
        const csrfToken = document.getElementById('csrfToken')?.value || '';
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', csrfToken);
        formData.append('first_name', document.getElementById('firstName').value.trim());
        formData.append('last_name', document.getElementById('lastName').value.trim());
        formData.append('email', document.getElementById('email').value.trim());
        formData.append('phone', document.getElementById('phone').value.trim());
        formData.append('date_of_birth', document.getElementById('dob').value);
        formData.append('gender', document.getElementById('gender').value);
        formData.append('address', document.getElementById('address').value.trim());
        formData.append('nationality', document.getElementById('nationality').value.trim());
        formData.append('alternate_contact', document.getElementById('altContact').value.trim());
        formData.append('program_interest', document.getElementById('program').value);
        formData.append('education_level', document.getElementById('eduLevel').value);
        formData.append('gpa_or_percentage', document.getElementById('gpa').value.trim());
        formData.append('previous_institution', document.getElementById('institution').value.trim());
        formData.append('scholarship_interest', document.querySelector('input[name="scholarship"]:checked')?.value || '');
        formData.append('study_mode', document.querySelector('input[name="mode"]:checked')?.value || '');
        formData.append('lead_source', document.getElementById('leadSource').value);
        formData.append('lead_status', document.getElementById('leadStatus')?.value || 'new');
        formData.append('counselor', document.getElementById('counselor').value);
        formData.append('followup_date', document.getElementById('followupDate').value);
        formData.append('notes', document.getElementById('notes').value.trim());

        const eduDocFile = document.getElementById('eduDoc').files[0];
        if (eduDocFile) {
            formData.append('education_document', eduDocFile);
        }

        const response = await fetch(window.location.pathname, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
            },
            body: formData,
        });

        const result = await response.json().catch(() => ({}));
        if (!response.ok || !result.success) {
            const message = result.error || 'Unable to save lead. Please try again.';
            alert(message);
            return;
        }

        const leadId = `LEAD-${String(result.lead_id).padStart(3, '0')}`;
        const name = `${document.getElementById('firstName').value} ${document.getElementById('lastName').value}`;

        document.getElementById('formFooter').style.display = 'none';
        document.querySelectorAll('.form-step').forEach((step) => step.classList.remove('active'));
        document.getElementById('stepsNav').style.opacity = '0.3';
        document.getElementById('stepsNav').style.pointerEvents = 'none';

        document.getElementById('successScreen').classList.add('show');
        document.getElementById('successName').textContent = name;
        document.getElementById('leadIdBadge').textContent = `Lead ID: ${leadId}`;

        // Send users to Leads list so they can immediately verify the new record.
        setTimeout(() => {
            window.location.href = '/leads/';
        }, 1200);
    } catch (error) {
        alert('Network error while saving lead. Please retry.');
    }
}

function resetForm() {
    document.querySelector('form') && document.querySelector('form').reset();
    document.querySelectorAll('input:not([type=radio]):not([type=checkbox])').forEach((el) => {
        el.value = '';
    });
    document.querySelectorAll('select').forEach((el) => {
        el.selectedIndex = 0;
    });
    document.querySelectorAll('textarea').forEach((el) => {
        el.value = '';
    });
    document.querySelectorAll('input[type=radio], input[type=checkbox]').forEach((el) => {
        el.checked = false;
    });
    const leadStatusEl = document.getElementById('leadStatus');
    if (leadStatusEl) {
        leadStatusEl.value = 'new';
    }
    document.querySelectorAll('.tag-btn').forEach((button) => button.classList.remove('selected'));
    document.getElementById('leadSource').value = '';

    currentStep = 1;
    document.getElementById('successScreen').classList.remove('show');
    document.getElementById('formFooter').style.display = 'flex';
    document.getElementById('stepsNav').style.opacity = '1';
    document.getElementById('stepsNav').style.pointerEvents = 'auto';
    updateUI();
    document.querySelectorAll('.form-step').forEach((step) => step.classList.remove('active'));
    document.getElementById('step1').classList.add('active');
}

const btnNext = document.getElementById('btnNext');
const btnBack = document.getElementById('btnBack');
const btnReset = document.getElementById('btnReset');
const stepNavItems = document.querySelectorAll('.step-item');
const leadStatusSelect = document.getElementById('leadStatus');

if (btnNext) btnNext.addEventListener('click', goNext);
if (btnBack) btnBack.addEventListener('click', goBack);
if (btnReset) btnReset.addEventListener('click', resetForm);

if (leadStatusSelect) {
    leadStatusSelect.addEventListener('change', () => {
        if (currentStep === 4) {
            populateReview();
        }
    });
}

stepNavItems.forEach((item) => {
    item.addEventListener('click', () => {
        const step = parseInt(item.dataset.step, 10);
        goToStep(step);
    });
});

updateUI();
