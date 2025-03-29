$(document).ready(function() {
    // Initialize date picker
    let currentDate = new Date($('#datePicker').val());
    
    // Close application
    $('#closeApp').click(function(e) {
        e.preventDefault();
        if (confirm('Вы уверены, что хотите закрыть программу?')) {
            window.location.href = '/shutdown';
        }
    });
    
    // Calendar toggle
    $('#calendarToggle').click(function() {
        $('#calendar').toggle();
    });
    
    // Previous date
    $('#prevDate').click(function() {
        currentDate.setDate(currentDate.getDate() - 1);
        updateDate();
    });
    
    // Next date
    $('#nextDate').click(function() {
        currentDate.setDate(currentDate.getDate() + 1);
        updateDate();
    });
    
    // Update date and reload page
    function updateDate() {
        const formattedDate = currentDate.toISOString().split('T')[0];
        window.location.href = '/?date=' + formattedDate;
    }
    
    // Send to REO button
    $('#sendToREOBtn, #sendToReo').click(function() {
        const selectedRows = Array.from(document.querySelectorAll('input[name="row_select"]:checked'))
            .map(checkbox => parseInt(checkbox.value));
        
        if (selectedRows.length === 0) {
            showError('Выберите записи для отправки');
            return;
        }

        if (!confirm('Отправить выбранные данные в РЭО?')) {
            return;
        }

        const currentDate = document.getElementById('current_date').value;
        
        fetch('/send_to_reo', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                date: currentDate,
                selected_rows: selectedRows
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showSuccess(data.message);
                location.reload();
            } else {
                showError(data.message);
            }
        })
        .catch(error => showError(error));
    });
    
    // Refresh data
    $('#refresh').click(function() {
        location.reload();
    });
    
    // Context menu for table cells
    $('.table').on('contextmenu', 'td', function(e) {
        e.preventDefault();
        const text = $(this).text();
        const $temp = $("<input>");
        $("body").append($temp);
        $temp.val(text).select();
        document.execCommand("copy");
        $temp.remove();
    });
    
    // Close calendar when clicking outside
    $(document).click(function(e) {
        if (!$(e.target).closest('.date-picker').length) {
            $('#calendar').hide();
        }
    });
    
    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
});

// Utility functions
function showError(message) {
    alert('Ошибка: ' + message);
}

function showSuccess(message) {
    alert('Успешно: ' + message);
}

// Settings page
document.addEventListener('DOMContentLoaded', function() {
    // Save settings form
    const settingsForm = document.querySelector('form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            fetch('/save_settings', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showSuccess(data.message);
                } else {
                    showError(data.message);
                }
            })
            .catch(error => showError(error));
        });

        // Database file selection button
        const dbFileBtn = document.querySelector('button[data-action="select-db"]');
        if (dbFileBtn) {
            dbFileBtn.addEventListener('click', function() {
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = '.gdb,.db';
                
                input.addEventListener('change', function(e) {
                    const file = e.target.files[0];
                    if (file) {
                        document.querySelector('input[name="db_path"]').value = file.path;
                    }
                });
                
                input.click();
            });
        }

        // Check database connection button
        const checkDbBtn = document.querySelector('button[data-action="check-db"]');
        if (checkDbBtn) {
            checkDbBtn.addEventListener('click', function() {
                const dbPath = document.querySelector('input[name="db_path"]').value;
                
                fetch('/check_db_connection', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ db_path: dbPath })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showSuccess('Подключение к базе данных успешно');
                    } else {
                        showError(data.message);
                    }
                })
                .catch(error => showError(error));
            });
        }

        // Check REO connection button
        const checkReoBtn = document.querySelector('button[data-action="check-reo"]');
        if (checkReoBtn) {
            checkReoBtn.addEventListener('click', function() {
                const accessKey = document.querySelector('input[name="access_key"]').value;
                const serviceUrl = document.querySelector('input[name="object_url"]').value;
                
                fetch('/check_reo_connection', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        access_key: accessKey,
                        service_url: serviceUrl
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showSuccess('Подключение к РЭО успешно');
                    } else {
                        showError(data.message);
                    }
                })
                .catch(error => showError(error));
            });
        }
    }

    // Send to REO button
    const sendToReoBtn = document.getElementById('sendToReo');
    if (sendToReoBtn) {
        sendToReoBtn.addEventListener('click', function() {
            const selectedRows = Array.from(document.querySelectorAll('input[name="row_select"]:checked'))
                .map(checkbox => parseInt(checkbox.value));
            
            if (selectedRows.length === 0) {
                showError('Выберите записи для отправки');
                return;
            }

            const currentDate = document.getElementById('current_date').value;
            
            fetch('/send_to_reo', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    date: currentDate,
                    selected_rows: selectedRows
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showSuccess(data.message);
                } else {
                    showError(data.message);
                }
            })
            .catch(error => showError(error));
        });
    }
});

// Cargo Types page
document.addEventListener('DOMContentLoaded', function() {
    const addCargoTypeBtn = document.getElementById('addCargoType');
    const cargoModal = document.getElementById('cargoModal');
    const saveCargoTypeBtn = document.getElementById('saveCargoType');
    let editMode = false;
    let oldName = '';

    if (addCargoTypeBtn) {
        addCargoTypeBtn.addEventListener('click', function() {
            editMode = false;
            document.getElementById('modalTitle').textContent = 'Добавить род груза';
            document.getElementById('cargoName').value = '';
            document.getElementById('reosendYes').checked = true;
            new bootstrap.Modal(cargoModal).show();
        });
    }

    if (saveCargoTypeBtn) {
        saveCargoTypeBtn.addEventListener('click', function() {
            const name = document.getElementById('cargoName').value;
            const reosend = document.querySelector('input[name="reosend"]:checked').value;
            
            const endpoint = editMode ? '/cargo_types/edit' : '/cargo_types/add';
            const data = editMode ? 
                { old_name: oldName, new_name: name, reosend: parseInt(reosend) } :
                { name: name, reosend: parseInt(reosend) };

            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showSuccess(data.message);
                    location.reload();
                } else {
                    showError(data.message);
                }
            })
            .catch(error => showError(error));
        });
    }

    // Edit cargo type
    document.querySelectorAll('.edit-cargo').forEach(button => {
        button.addEventListener('click', function() {
            editMode = true;
            const row = this.closest('tr');
            oldName = row.cells[0].textContent;
            
            document.getElementById('modalTitle').textContent = 'Изменить род груза';
            document.getElementById('cargoName').value = oldName;
            document.getElementById(row.cells[1].textContent === 'Отправлять' ? 'reosendYes' : 'reosendNo').checked = true;
            
            new bootstrap.Modal(cargoModal).show();
        });
    });

    // Delete cargo type
    document.querySelectorAll('.delete-cargo').forEach(button => {
        button.addEventListener('click', function() {
            if (confirm('Вы уверены, что хотите удалить этот род груза?')) {
                const name = this.closest('tr').cells[0].textContent;
                
                fetch('/cargo_types/delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name: name })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showSuccess(data.message);
                        location.reload();
                    } else {
                        showError(data.message);
                    }
                })
                .catch(error => showError(error));
            }
        });
    });
});

// Companies page
document.addEventListener('DOMContentLoaded', function() {
    const addCompanyBtn = document.getElementById('addCompany');
    const companyModal = document.getElementById('companyModal');
    const saveCompanyBtn = document.getElementById('saveCompany');
    let editMode = false;
    let oldName = '';

    if (addCompanyBtn) {
        addCompanyBtn.addEventListener('click', function() {
            editMode = false;
            document.getElementById('modalTitle').textContent = 'Добавить компанию';
            document.getElementById('companyName').value = '';
            document.getElementById('companyINN').value = '';
            document.getElementById('companyKPP').value = '';
            document.getElementById('reosendYes').checked = true;
            new bootstrap.Modal(companyModal).show();
        });
    }

    if (saveCompanyBtn) {
        saveCompanyBtn.addEventListener('click', function() {
            const name = document.getElementById('companyName').value;
            const inn = document.getElementById('companyINN').value;
            const kpp = document.getElementById('companyKPP').value;
            const reosend = document.querySelector('input[name="reosend"]:checked').value;
            
            const endpoint = editMode ? '/companies/edit' : '/companies/add';
            const data = editMode ? 
                { old_name: oldName, new_name: name, inn: inn, kpp: kpp, reosend: parseInt(reosend) } :
                { name: name, inn: inn, kpp: kpp, reosend: parseInt(reosend) };

            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showSuccess(data.message);
                    location.reload();
                } else {
                    showError(data.message);
                }
            })
            .catch(error => showError(error));
        });
    }

    // Edit company
    document.querySelectorAll('.edit-company').forEach(button => {
        button.addEventListener('click', function() {
            editMode = true;
            const row = this.closest('tr');
            oldName = row.cells[0].textContent;
            
            document.getElementById('modalTitle').textContent = 'Изменить компанию';
            document.getElementById('companyName').value = oldName;
            document.getElementById('companyINN').value = row.cells[1].textContent;
            document.getElementById('companyKPP').value = row.cells[2].textContent;
            document.getElementById(row.cells[3].textContent === 'Отправлять' ? 'reosendYes' : 'reosendNo').checked = true;
            
            new bootstrap.Modal(companyModal).show();
        });
    });

    // Delete company
    document.querySelectorAll('.delete-company').forEach(button => {
        button.addEventListener('click', function() {
            if (confirm('Вы уверены, что хотите удалить эту компанию?')) {
                const name = this.closest('tr').cells[0].textContent;
                
                fetch('/companies/delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name: name })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showSuccess(data.message);
                        location.reload();
                    } else {
                        showError(data.message);
                    }
                })
                .catch(error => showError(error));
            }
        });
    });
});

// Auto page
document.addEventListener('DOMContentLoaded', function() {
    const addAutoBtn = document.getElementById('addAuto');
    const autoModal = document.getElementById('autoModal');
    const saveAutoBtn = document.getElementById('saveAuto');
    let editMode = false;
    let oldNomer = '';

    if (addAutoBtn) {
        addAutoBtn.addEventListener('click', function() {
            editMode = false;
            document.getElementById('modalTitle').textContent = 'Добавить транспорт';
            document.getElementById('autoNumber').value = '';
            document.getElementById('autoMark').value = '';
            document.getElementById('minWeight').value = '';
            document.getElementById('maxWeight').value = '';
            new bootstrap.Modal(autoModal).show();
        });
    }

    if (saveAutoBtn) {
        saveAutoBtn.addEventListener('click', function() {
            const nomer_ts2 = document.getElementById('autoNumber').value;
            const marka_ts2 = document.getElementById('autoMark').value;
            const min_weight = document.getElementById('minWeight').value;
            const max_weight = document.getElementById('maxWeight').value;
            
            const endpoint = editMode ? '/auto/edit' : '/auto/add';
            const data = editMode ? 
                { old_nomer: oldNomer, nomer_ts2, marka_ts2, min_weight, max_weight } :
                { nomer_ts2, marka_ts2, min_weight, max_weight };

            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showSuccess(data.message);
                    location.reload();
                } else {
                    showError(data.message);
                }
            })
            .catch(error => showError(error));
        });
    }

    // Edit auto
    document.querySelectorAll('.edit-auto').forEach(button => {
        button.addEventListener('click', function() {
            editMode = true;
            const row = this.closest('tr');
            oldNomer = row.cells[0].textContent;
            
            document.getElementById('modalTitle').textContent = 'Изменить транспорт';
            document.getElementById('autoNumber').value = oldNomer;
            document.getElementById('autoMark').value = row.cells[1].textContent;
            document.getElementById('minWeight').value = row.cells[2].textContent;
            document.getElementById('maxWeight').value = row.cells[3].textContent;
            
            new bootstrap.Modal(autoModal).show();
        });
    });

    // Delete auto
    document.querySelectorAll('.delete-auto').forEach(button => {
        button.addEventListener('click', function() {
            if (confirm('Вы уверены, что хотите удалить этот транспорт?')) {
                const nomer_ts2 = this.closest('tr').cells[0].textContent;
                
                fetch('/auto/delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ nomer_ts2: nomer_ts2 })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showSuccess(data.message);
                        location.reload();
                    } else {
                        showError(data.message);
                    }
                })
                .catch(error => showError(error));
            }
        });
    });
}); 