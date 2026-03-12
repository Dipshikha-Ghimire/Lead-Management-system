document.addEventListener('DOMContentLoaded', function() {
    // Personal Information Edit
    const editPersonalBtn = document.getElementById('editPersonalBtn');
    const cancelPersonalBtn = document.getElementById('cancelPersonalBtn');
    const personalInfoForm = document.getElementById('personalInfoForm');
    const personalEditActions = personalInfoForm.querySelector('.edit-actions');
    const personalFields = personalInfoForm.querySelectorAll('input[name="full_name"], input[name="phone"], input[name="department"], textarea[name="bio"]');

    if (editPersonalBtn && cancelPersonalBtn) {
        editPersonalBtn.addEventListener('click', function() {
            personalFields.forEach(field => field.removeAttribute('readonly'));
            editPersonalBtn.style.display = 'none';
            personalEditActions.style.display = 'flex';
        });

        cancelPersonalBtn.addEventListener('click', function() {
            personalFields.forEach(field => field.setAttribute('readonly', 'true'));
            personalInfoForm.reset();
            editPersonalBtn.style.display = 'block';
            personalEditActions.style.display = 'none';
        });
    }
});