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
                },
                body: formData
            }).then(function(response) {
                return response.json();
            }).then(function(data) {
                if (data.success) {
                    location.reload();
                } else {
                    alert(data.error || 'An error occurred');
                }
            }).catch(function() {
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
                },
                body: formData
            }).then(function(response) {
                return response.json();
            }).then(function(data) {
                if (data.success) {
                    location.reload();
                } else {
                    alert(data.error || 'An error occurred');
                }
            }).catch(function() {
                alert('An error occurred. Please try again.');
            });
        });
    }
});