// assets/js/manager.js

// Helper formatDate
function formatDate(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('vi-VN');
    } catch (e) { return dateString; }
}

function formatDateForInput(dateString) {
    if (!dateString) return '';
     try {
        const date = new Date(dateString);
        const day = String(date.getUTCDate()).padStart(2, '0');
        const month = String(date.getUTCMonth() + 1).padStart(2, '0');
        const year = date.getUTCFullYear();
        return `${year}-${month}-${day}`;
     } catch (e) { return ''; }
}

document.addEventListener("DOMContentLoaded", async () => {
    console.log("Manager Dashboard Loaded");
    const user = JSON.parse(localStorage.getItem("user"));
    if(!user || user.role !== "manager"){ window.location.href="/login.html"; return; }
    const managerId = user.manager_id;
    
    // Profile Info
    if(document.getElementById("userProfileName")) document.getElementById("userProfileName").innerText = user.full_name;

    // Modals
    let doctorModal = null;
    let patientModal = null;
    try {
        const dModalEl = document.getElementById('doctorModal');
        if(dModalEl) doctorModal = new bootstrap.Modal(dModalEl);
        const pModalEl = document.getElementById('patientModal');
        if(pModalEl) patientModal = new bootstrap.Modal(pModalEl);
    } catch(e) { console.error(e); }

    let doctorsCache = []; 

    // Tab Switching
    document.querySelectorAll("#sidebar .nav-link").forEach(link => {
        link.addEventListener("click", e => {
            e.preventDefault();
            document.querySelectorAll("#sidebar .nav-link").forEach(l=>l.classList.remove("active"));
            link.classList.add("active");
            document.querySelectorAll(".tab-content").forEach(t=>t.classList.add("d-none"));
            
            const tabId = link.dataset.tab;
            document.getElementById("tab-" + tabId).classList.remove("d-none");
            
            if (tabId === 'doctors') loadDoctors();
            if (tabId === 'patients') loadPatients();
            if (tabId === 'devices') loadDevices();
            if (tabId === 'reports') loadReports();
        });
    });

    // Logout
    document.getElementById("logoutBtn").addEventListener("click", ()=> {
        localStorage.removeItem("user");
        window.location.href="/login.html";
    });
    
    // ==========================
    // QUẢN LÝ BÁC SĨ
    // ==========================

    async function loadDoctors(){
        try{
            const res = await fetch(`/api/managers/${managerId}/doctors`);
            if(!res.ok) return;
            doctorsCache = await res.json();
            const tbody = document.getElementById("doctors-table-body");
            if(!tbody) return;
            tbody.innerHTML="";
            
            if (doctorsCache.length === 0) {
                tbody.innerHTML = "<tr><td colspan='6' class='text-center text-muted py-3'>Chưa có bác sĩ nào.</td></tr>";
                return;
            }
            
            doctorsCache.forEach((d,i)=>{
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td class="ps-4 fw-bold">${i+1}</td>
                    <td>${d.full_name}</td>
                    <td>${d.email}</td>
                    <td>${d.phone_number || ''}</td>
                    <td><span class="badge bg-light text-dark border">${d.title || 'N/A'}</span></td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-outline-primary edit-btn me-1" data-id="${d.doctor_id}"><i class="bi bi-pencil-square"></i></button>
                        <button class="btn btn-sm btn-outline-danger del-btn" data-id="${d.doctor_id}"><i class="bi bi-trash"></i></button>
                    </td>`;
                tbody.appendChild(tr);
            });
            
            // Bind Events
            document.querySelectorAll('.edit-btn').forEach(btn => {
                btn.addEventListener('click', () => openEditDoctorModal(btn.dataset.id));
            });
            document.querySelectorAll('.del-btn').forEach(btn => {
                btn.addEventListener('click', () => deleteDoctor(btn.dataset.id));
            });
            
        } catch(err){ console.error(err); }
    }

    // Add Doctor
    const addDocBtn = document.getElementById('addDoctorBtn');
    if(addDocBtn) addDocBtn.addEventListener('click', () => {
        document.getElementById('doctorModalTitle').innerText = "Thêm bác sĩ";
        document.getElementById('modalDoctorId').value = "";
        const passField = document.getElementById('password-field');
        if(passField) passField.style.display = 'block'; 
        document.getElementById('doctorForm').reset();
        const msgEl = document.getElementById("doctorMsg");
        if(msgEl) msgEl.classList.add('d-none');
        if(doctorModal) doctorModal.show();
    });
    
    // Edit Doctor
    function openEditDoctorModal(id) {
        const doctor = doctorsCache.find(d => d.doctor_id == id);
        if (!doctor) return;
        
        document.getElementById('doctorModalTitle').innerText = "Sửa thông tin bác sĩ";
        document.getElementById('modalDoctorId').value = doctor.doctor_id;
        const passField = document.getElementById('password-field');
        if(passField) passField.style.display = 'none'; 
        
        const msgEl = document.getElementById("doctorMsg");
        if(msgEl) msgEl.classList.add('d-none');
        document.getElementById('doctorForm').reset();

        if(document.getElementById('modalDocFullName')) document.getElementById('modalDocFullName').value = doctor.full_name;
        if(document.getElementById('modalDocEmail')) document.getElementById('modalDocEmail').value = doctor.email;
        if(document.getElementById('modalDocPhone')) document.getElementById('modalDocPhone').value = doctor.phone_number || '';
        if(document.getElementById('modalDocAddress')) document.getElementById('modalDocAddress').value = doctor.address || '';
        if(document.getElementById('modalDocDOB')) document.getElementById('modalDocDOB').value = formatDateForInput(doctor.date_of_birth) || '';
        if(document.getElementById('modalDocTitle')) document.getElementById('modalDocTitle').value = doctor.title || '';
        if(document.getElementById('modalDocSpecialty')) document.getElementById('modalDocSpecialty').value = doctor.specialty || '';
        
        if(doctorModal) doctorModal.show();
    }
    
    // Save Doctor (Add/Edit)
    const saveDocBtn = document.getElementById('saveDoctorBtn');
    if(saveDocBtn) saveDocBtn.addEventListener('click', async () => {
        const doctorId = document.getElementById('modalDoctorId').value;
        const isEditing = !!doctorId;
        
        const body = {
            full_name: document.getElementById('modalDocFullName').value,
            email: document.getElementById('modalDocEmail').value,
            phone_number: document.getElementById('modalDocPhone').value,
            address: document.getElementById('modalDocAddress').value,
            date_of_birth: document.getElementById('modalDocDOB').value,
            title: document.getElementById('modalDocTitle').value,
            specialty: document.getElementById('modalDocSpecialty').value
        };
        
        let url = `/api/managers/${managerId}/doctors`; 
        let method = 'POST';
        
        if (isEditing) {
            url = `/api/managers/doctors/${doctorId}`;
            method = 'PUT';
        } else {
            body.password = document.getElementById('modalDocPassword').value;
        }
        
        const msgEl = document.getElementById("doctorMsg");
        try {
            const res = await fetch(url, {
                method: method,
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(body)
            });
            const data = await res.json();
            
            if (res.ok) {
                if(msgEl) { msgEl.textContent = data.message; msgEl.className = 'alert alert-success'; msgEl.classList.remove('d-none'); }
                await loadDoctors(); 
                setTimeout(() => { if(doctorModal) doctorModal.hide(); }, 1000);
            } else {
                if(msgEl) { msgEl.textContent = data.message; msgEl.className = 'alert alert-danger'; msgEl.classList.remove('d-none'); }
            }
        } catch (err) { alert("Lỗi máy chủ!"); }
    });

    // Delete Doctor
    async function deleteDoctor(id) {
        if (!confirm("Bạn có chắc chắn muốn xóa bác sĩ này? Bệnh nhân của họ sẽ bị gỡ gán.")) return;
        try {
            const res = await fetch(`/api/managers/doctors/${id}`, { method: 'DELETE' });
            if (res.ok) await loadDoctors(); 
            else alert("Xóa thất bại!");
        } catch (err) { alert("Lỗi khi xóa!"); }
    }


    // ==========================
    // QUẢN LÝ BỆNH NHÂN
    // ==========================

    async function loadPatients(){
        try{
            const res = await fetch(`/api/managers/${managerId}/patients`);
            if(!res.ok) return;
            const data = await res.json();
            const tbody = document.getElementById("patients-table-body");
            if(!tbody) return;
            tbody.innerHTML="";
            
            if (data.length === 0) {
                 tbody.innerHTML = "<tr><td colspan='4' class='text-center text-muted py-3'>Chưa có bệnh nhân nào.</td></tr>";
                 return;
            }
            
            data.forEach((p,i)=>{
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td class="ps-4 fw-bold">${i+1}</td>
                    <td>${p.full_name}</td>
                    <td>${p.email || ''}</td>
                    <td><span class="text-primary fw-bold">${p.doctor_name || 'Đang chờ...'}</span></td>`;
                tbody.appendChild(tr);
            });
        } catch(err){ console.error(err); }
    }

    const addPatientBtn = document.getElementById('addPatientBtn');
    if(addPatientBtn) addPatientBtn.addEventListener('click', () => {
        document.getElementById('patientForm').reset();
        const msgEl = document.getElementById("patientMsg");
        if(msgEl) msgEl.classList.add('d-none');
        if(patientModal) patientModal.show();
    });
    
    const savePatientBtn = document.getElementById('savePatientBtn');
    if(savePatientBtn) savePatientBtn.addEventListener('click', async () => {
        const body = {
            full_name: document.getElementById('modalPatientFullName').value,
            email: document.getElementById('modalPatientEmail').value,
            password: document.getElementById('modalPatientPassword').value,
            phone_number: document.getElementById('modalPatientPhone').value,
            address: document.getElementById('modalPatientAddress').value,
            date_of_birth: document.getElementById('modalPatientDOB').value
        };

        const msgEl = document.getElementById("patientMsg");
        try {
            const res = await fetch(`/api/managers/${managerId}/patients`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(body)
            });
            const data = await res.json();
            
            if (res.ok) {
                if(msgEl) { msgEl.textContent = data.message; msgEl.className = 'alert alert-success'; msgEl.classList.remove('d-none'); }
                await loadPatients();
                setTimeout(() => { if(patientModal) patientModal.hide(); }, 1000);
            } else {
                if(msgEl) { msgEl.textContent = data.message; msgEl.className = 'alert alert-danger'; msgEl.classList.remove('d-none'); }
            }
        } catch (err) { alert("Lỗi máy chủ!"); }
    });


    // ==========================
    // GIÁM SÁT THIẾT BỊ
    // ==========================

    async function loadDevices(){
        try{
            const res = await fetch(`/api/managers/${managerId}/devices`);
            if(!res.ok) return;
            const data = await res.json();
            const tbody = document.getElementById("devices-table-body");
            if(!tbody) return;
            tbody.innerHTML="";
             if (data.length === 0) {
                 tbody.innerHTML = "<tr><td colspan='4' class='text-center text-muted py-3'>Không có thiết bị nào.</td></tr>";
                 return;
            }
            data.forEach((d,i)=>{
                const tr = document.createElement("tr");
                const statusBadge = d.status === 'online' ? '<span class="badge bg-success">Online</span>' : '<span class="badge bg-secondary">Offline</span>';
                tr.innerHTML = `
                    <td class="ps-4 fw-bold">${i+1}</td>
                    <td class="font-monospace">${d.device_serial}</td>
                    <td>${statusBadge}</td>
                    <td>${new Date(d.last_seen).toLocaleString()}</td>`;
                tbody.appendChild(tr);
            });
        } catch(err){ console.error(err); }
    }

    // ==========================
    // THỐNG KÊ
    // ==========================

    let alertsChart;
    async function loadReports(){
        try{
            const res = await fetch(`/api/managers/${managerId}/stats`);
            if(!res.ok) return;
            const stats = await res.json();
            
            if(document.getElementById('total-patients')) document.getElementById('total-patients').innerText = stats.patients_total || 0;
            if(document.getElementById('total-doctors')) document.getElementById('total-doctors').innerText = stats.doctors_total || 0;

            const ctxEl = document.getElementById("alertsChart");
            if(!ctxEl) return;
            const ctx = ctxEl.getContext("2d");
            
            if(alertsChart) alertsChart.destroy();
            
            // Check if empty chart
            if (!stats.alert_labels || stats.alert_labels.length === 0) {
                // Vẽ chart rỗng hoặc hiện thông báo
                return;
            }

            alertsChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: stats.alert_labels,
                    datasets: [{
                        data: stats.alert_counts,
                        backgroundColor: ['#dc3545', '#0dcaf0', '#ffc107', '#198754'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right' }
                    }
                }
            });
        } catch(err){ console.error(err); }
    }
    
    // Initial Load
    loadDoctors();
});