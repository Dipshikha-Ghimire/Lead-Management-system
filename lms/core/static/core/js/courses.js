document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token from the page
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    
    // Department Form
    const deptForm = document.getElementById('deptForm');
    if (deptForm) {
        deptForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(deptForm);
            const id = document.getElementById('editDeptId').value;
            let url = '/courses/department/add/';
            if (id) {
                url = '/courses/department/' + id + '/update/';
            }
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData
            }).then(function(response) {
                return response.json();
            }).then(function(data) {
                if (data.success) {
                    // Close the modal
                    const modal = document.getElementById('deptModal');
                    if (modal) {
                        modal.style.display = 'none';
                    }
                    // Reset form
                    deptForm.reset();
                    document.getElementById('editDeptId').value = '';
                    document.getElementById('deptModalTitle').textContent = 'Add Department';
                    // Reload to show updated list (could implement real-time DOM update here)
                    location.reload();
                } else {
                    alert(data.error || 'An error occurred');
                }
            }).catch(function(err) {
                console.error('Error:', err);
                alert('An error occurred. Please try again.');
            });
        });
    }
    
    // Program Form
    const progForm = document.getElementById('progForm');
    if (progForm) {
        progForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(progForm);
            const id = document.getElementById('editProgId').value;
            let url = '/courses/program/add/';
            if (id) {
                url = '/courses/program/' + id + '/update/';
            }
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData
            }).then(function(response) {
                return response.json();
            }).then(function(data) {
                if (data.success) {
                    // Close the modal
                    const modal = document.getElementById('progModal');
                    if (modal) {
                        modal.style.display = 'none';
                    }
                    // Reset form
                    progForm.reset();
                    document.getElementById('editProgId').value = '';
                    document.getElementById('progModalTitle').textContent = 'Add Program';
                    // Reload to show updated list (could implement real-time DOM update here)
                    location.reload();
                } else {
                    alert(data.error || 'An error occurred');
                }
            }).catch(function(err) {
                console.error('Error:', err);
                alert('An error occurred. Please try again.');
            });
        });
    }
});