let currentStep = 1;
const totalSteps = 4;

// Source tag toggle
document.querySelectorAll('.tag-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tag-btn').forEach((tagButton) => tagButton.classList.remove('selected'));
        btn.classList.add('selected');
        document.getElementById('leadSource').value = btn.dataset.val;
        document.getElementById('leadSourceErr').classList.remove('show');
    });
});

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
        ['program', 'intakeYear'].forEach((field) => clearErr(field, `${field}Err`));
        if (!document.getElementById('program').value) showErr('program', 'programErr');
        if (!document.getElementById('intakeYear').value) showErr('intakeYear', 'intakeYearErr');
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
    const mode = document.querySelector('input[name="mode"]:checked')?.value || '—';
    const scholarship = document.querySelector('input[name="scholarship"]:checked')?.value || '—';
    const leadStatusEl = document.getElementById('leadStatus');
    const leadStatusValue = leadStatusEl?.value || '';
    const leadStatusLabel = leadStatusEl?.options?.[leadStatusEl.selectedIndex]?.textContent?.trim() || '';
    const leadStatus = leadStatusLabel || leadStatusValue.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase()) || '—';

    const data = [
        { label: 'Full Name', value: `${document.getElementById('firstName').value} ${document.getElementById('lastName').value}`, full: false },
        { label: 'Email', value: document.getElementById('email').value, full: false },
        { label: 'Phone', value: document.getElementById('phone').value, full: false },
        { label: 'Gender', value: document.getElementById('gender').value || '—', full: false },
        { label: 'Program', value: document.getElementById('program').value, full: true },
        { label: 'Intake', value: `${document.getElementById('intakeYear').value} – ${document.getElementById('intakeSem').value || '—'}`, full: false },
        { label: 'Education', value: document.getElementById('eduLevel').value || '—', full: false },
        { label: 'GPA / %', value: document.getElementById('gpa').value || '—', full: false },
        { label: 'Scholarship Interest', value: scholarship, full: false },
        { label: 'Study Mode', value: mode, full: false },
        { label: 'Lead Source', value: document.getElementById('leadSource').value || '—', full: false },
        { label: 'Lead Status', value: leadStatus, full: false },
        { label: 'Counselor', value: document.getElementById('counselor').value || '—', full: false },
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
        const payload = new URLSearchParams({
            csrfmiddlewaretoken: csrfToken,
            first_name: document.getElementById('firstName').value.trim(),
            last_name: document.getElementById('lastName').value.trim(),
            email: document.getElementById('email').value.trim(),
            phone: document.getElementById('phone').value.trim(),
            date_of_birth: document.getElementById('dob').value,
            gender: document.getElementById('gender').value,
            address: document.getElementById('address').value.trim(),
            nationality: document.getElementById('nationality').value.trim(),
            alternate_contact: document.getElementById('altContact').value.trim(),
            program_interest: document.getElementById('program').value,
            intake_year: document.getElementById('intakeYear').value,
            intake_semester: document.getElementById('intakeSem').value,
            education_level: document.getElementById('eduLevel').value,
            gpa_or_percentage: document.getElementById('gpa').value.trim(),
            previous_institution: document.getElementById('institution').value.trim(),
            scholarship_interest: document.querySelector('input[name="scholarship"]:checked')?.value || '',
            study_mode: document.querySelector('input[name="mode"]:checked')?.value || '',
            lead_source: document.getElementById('leadSource').value,
            lead_status: document.getElementById('leadStatus')?.value || 'new',
            counselor: document.getElementById('counselor').value,
            followup_date: document.getElementById('followupDate').value,
            notes: document.getElementById('notes').value.trim(),
        });

        const response = await fetch(window.location.pathname, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-CSRFToken': csrfToken,
            },
            body: payload.toString(),
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
