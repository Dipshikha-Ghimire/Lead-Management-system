document.addEventListener('DOMContentLoaded', function() {
    const editPersonalBtn = document.getElementById('editPersonalBtn');
    const cancelPersonalBtn = document.getElementById('cancelPersonalBtn');
    const personalInfoForm = document.getElementById('personalInfoForm');
    if (!personalInfoForm) return;

    const personalEditActions = personalInfoForm.querySelector('.edit-actions');
    const personalFields = personalInfoForm.querySelectorAll('input[name="full_name"], input[name="phone"], input[name="email"], textarea[name="bio"]');
    const departmentSelect = document.getElementById('departmentSelect');
    const departmentHidden = document.getElementById('departmentHidden');
    const canEditDepartment = personalInfoForm.dataset.canEditDepartment === 'true';

    if (editPersonalBtn && cancelPersonalBtn) {
        editPersonalBtn.addEventListener('click', function() {
            personalFields.forEach(field => field.removeAttribute('readonly'));
            if (canEditDepartment && departmentSelect) {
                departmentSelect.removeAttribute('disabled');
            }
            editPersonalBtn.style.display = 'none';
            personalEditActions.style.display = 'flex';
        });

        cancelPersonalBtn.addEventListener('click', function() {
            personalFields.forEach(field => field.setAttribute('readonly', 'true'));
            if (departmentSelect) {
                departmentSelect.setAttribute('disabled', 'true');
                const savedValue = departmentHidden ? departmentHidden.value : '';
                departmentSelect.value = savedValue;
            }
            editPersonalBtn.style.display = 'block';
            personalEditActions.style.display = 'none';
        });
    }
});