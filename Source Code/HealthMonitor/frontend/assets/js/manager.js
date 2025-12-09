// assets/js/manager.js

function formatDate(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        // Dùng UTC
        const day = String(date.getUTCDate()).padStart(2, '0');
        const month = String(date.getUTCMonth() + 1).padStart(2, '0');
        const year = date.getUTCFullYear();
        return `${day}/${month}/${year}`;
    } catch (e) { return dateString; }
}

function formatDateTime(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        const day = String(date.getUTCDate()).padStart(2, '0');
        const month = String(date.getUTCMonth() + 1).padStart(2, '0');
        const year = date.getUTCFullYear();
        const hours = String(date.getUTCHours()).padStart(2, '0');
        const minutes = String(date.getUTCMinutes()).padStart(2, '0');
        const seconds = String(date.getUTCSeconds()).padStart(2, '0');
        return `${hours}:${minutes}:${seconds} ${day}/${month}/${year}`;
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
    const user = JSON.parse(localStorage.getItem("user"));
    if(!user || user.role !== "manager"){ window.location.href="/login.html"; return; }
    const managerId = user.manager_id;
    
    if(document.getElementById("userProfileName")) document.getElementById("userProfileName").innerText = user.full_name;

    let doctorModal = null;
    let patientModal = null;
    try {
        const dModalEl = document.getElementById('doctorModal');
        if(dModalEl) doctorModal = new bootstrap.Modal(dModalEl);
        const pModalEl = document.getElementById('patientModal');
        if(pModalEl) patientModal = new bootstrap.Modal(pModalEl);
    } catch(e) { console.error(e); }

    let doctorsCache = []; 

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
            if (tabId === 'firmware') loadDevicesForFirmware();
        });
    });

    document.getElementById("logoutBtn").addEventListener("click", ()=> {
        localStorage.removeItem("user");
        window.location.href="/login.html";
    });
    
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
            
            document.querySelectorAll('.edit-btn').forEach(btn => {
                btn.addEventListener('click', () => openEditDoctorModal(btn.dataset.id));
            });
            document.querySelectorAll('.del-btn').forEach(btn => {
                btn.addEventListener('click', () => deleteDoctor(btn.dataset.id));
            });
            
        } catch(err){ console.error(err); }
    }

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

    async function deleteDoctor(id) {
        if (!confirm("Bạn có chắc chắn muốn xóa bác sĩ này? Bệnh nhân của họ sẽ bị gỡ gán.")) return;
        try {
            const res = await fetch(`/api/managers/doctors/${id}`, { method: 'DELETE' });
            if (res.ok) await loadDoctors(); 
            else alert("Xóa thất bại!");
        } catch (err) { alert("Lỗi khi xóa!"); }
    }

    async function loadPatients() {
    try {
        const res = await fetch(`/api/managers/${managerId}/patients`);
        if (!res.ok) return;
        const data = await res.json();
        const tbody = document.getElementById("patients-table-body");
        if (!tbody) return;
        tbody.innerHTML = "";

        if (data.length === 0) {
            tbody.innerHTML = "<tr><td colspan='6' class='text-center text-muted py-3'>Chưa có bệnh nhân nào.</td></tr>";
            return;
        }

        data.forEach((p, i) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td class="ps-4 fw-bold">${i + 1}</td>
                <td>${p.full_name}</td>
                <td>${p.email || ''}</td>
                <td><span class="text-primary fw-bold">${p.doctor_name || 'Đang chờ...'}</span></td>
                <td>${p.device_id || '-'}</td>
                <td class="text-center"></td>
                 
            
        </td>
            `;
            tbody.appendChild(tr);

            // Tạo nút Gán thiết bị và gắn event listener
            const btnTd = tr.querySelector("td.text-center");
            const btn = document.createElement("button");
            btn.className = "btn btn-sm btn-primary";
            btn.textContent = "Gán thiết bị";
            btn.addEventListener("click", () => openAssignDeviceModal(p.patient_id, p.full_name));
            btnTd.appendChild(btn);
            

            const unassignBtn = document.createElement("button");
            unassignBtn.className = "btn btn-sm btn-danger me-1";
            unassignBtn.textContent = "Hủy gán";
            if (!p.device_id) unassignBtn.disabled = true;
            unassignBtn.addEventListener("click", () => unassignDevice(p.patient_id));
            btnTd.appendChild(unassignBtn);
        });
    } catch (err) {
        console.error(err);
    }
}

//hủy gán 

async function unassignDevice(patientId) {
    if (!confirm("Bạn có chắc chắn muốn hủy gán thiết bị cho bệnh nhân này?")) return;

    try {
        const res = await fetch(`/api/managers/${managerId}/patients/${patientId}/unassign-device`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({})
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.message || "Hủy gán thiết bị thất bại!");

        alert(result.message || "Đã hủy gán thiết bị thành công!");
        await loadPatients();
    } catch (err) {
        alert(err.message);
    }
}


// Gán thiết bị cho bệnh nhân
const assignDeviceModal = new bootstrap.Modal(document.getElementById('assignDeviceModal'));
const assignPatientIdInput = document.getElementById("assignPatientId");
const assignDeviceSelect = document.getElementById("assignDeviceSelect");
const saveAssignDeviceBtn = document.getElementById("saveAssignDeviceBtn");

async function openAssignDeviceModal(patientId, patientName) {
    document.getElementById("assignDeviceModalTitle").innerText = `Gán thiết bị cho ${patientName}`;
    assignPatientIdInput.value = patientId;

    // Lấy danh sách thiết bị chưa gán
    try {
        const res = await fetch(`/api/managers/${managerId}/devices`);
        if(!res.ok) throw new Error("Lấy danh sách thiết bị thất bại");
        const devices = await res.json();

        // Chỉ hiện các thiết bị chưa gán (tức patient_id = null)
        const availableDevices = devices.filter(d => !d.patient_id);
        assignDeviceSelect.innerHTML = "";
        if(availableDevices.length === 0){
            assignDeviceSelect.innerHTML = `<option disabled>Không còn thiết bị trống</option>`;
        } else {
            availableDevices.forEach(d => {
                assignDeviceSelect.innerHTML += `<option value="${d.device_id}">${d.device_serial}</option>`;
            });
        }

        assignDeviceModal.show();
    } catch(err) {
        alert(err.message);
    }
}
saveAssignDeviceBtn.addEventListener("click", async () => {
    const patientId = assignPatientIdInput.value;
    const deviceId = assignDeviceSelect.value;
    if(!deviceId) return alert("Vui lòng chọn thiết bị!");

    try {
        const res = await fetch(`/api/managers/${managerId}/patients/${patientId}/assign-device`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ device_id: deviceId })
        });
        const result = await res.json();
        if(!res.ok) throw new Error(result.message || "Gán thiết bị thất bại!");

        assignDeviceModal.hide();
        await loadPatients();  // refresh bảng bệnh nhân
        // await refreshDevices(); // refresh bảng thiết bị
    } catch(err) {
        alert(err.message);
    }
});

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
                // Dùng formatDateTime (UTC)
                tr.innerHTML = `
                    <td class="ps-4 fw-bold">${i+1}</td>
                    <td class="font-monospace">${d.device_serial}</td>
                    <td>${statusBadge}</td>
                    <td>${formatDateTime(d.last_seen)}</td>`;
                tbody.appendChild(tr);
            });
        } catch(err){ console.error(err); }
    }

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
            
            if (!stats.alert_labels || stats.alert_labels.length === 0) {
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
    
    loadDoctors();


    // assets/js/manager.js

// ========================================

//QUẢN LÝ THIẾT BỊ

const devicesTableBody = document.getElementById("devices-table-body");
const addDeviceBtn = document.getElementById("addDeviceBtn");
const saveDeviceBtn = document.getElementById("saveDeviceBtn");
const modalDeviceSerial = document.getElementById("modalDeviceSerial");

// Biến lưu trạng thái modal (ĐẶT Ở NGOÀI để có thể truy cập từ onclick)
let isEditMode = false;
let currentDeviceId = null;

// ✅ ĐẶT HÀM Ở NGOÀI để có thể gọi từ onclick
window.openEditModal = function(deviceId, deviceSerial) {
    isEditMode = true;
    currentDeviceId = deviceId;
    document.getElementById("deviceModalTitle").innerText = "Sửa thiết bị";
    modalDeviceSerial.value = deviceSerial;
    new bootstrap.Modal(document.getElementById('deviceModal')).show();
};

// ✅ ĐẶT HÀM XÓA Ở NGOÀI để có thể gọi từ onclick
window.deleteDevice = async function(deviceId) {
    if (!confirm("Bạn có chắc chắn muốn xóa thiết bị này?")) return;
    
    try {
        const res = await fetch(`/api/managers/${managerId}/devices/${deviceId}`, {
            method: "DELETE"
        });
        
        const result = await res.json();
        
        if (!res.ok) throw new Error(result.message || "Xóa thất bại!");
        
        alert(result.message || "Xóa thiết bị thành công!");
        await refreshDevices();
        
    } catch (err) {
        alert(err.message);
    }
};

// Hiển thị modal THÊM thiết bị
addDeviceBtn.addEventListener("click", () => {
    isEditMode = false;
    currentDeviceId = null;
    document.getElementById("deviceModalTitle").innerText = "Thêm thiết bị";
    modalDeviceSerial.value = "";
    new bootstrap.Modal(document.getElementById('deviceModal')).show();
});

// Lưu thiết bị (THÊM hoặc SỬA)
saveDeviceBtn.addEventListener("click", async () => {
    const serial = modalDeviceSerial.value.trim();
    if (!serial) return alert("Vui lòng nhập Serial thiết bị!");

    const payload = { device_serial: serial };

    try {
        let url, method;
        
        if (isEditMode) {
            // Chế độ SỬA
            url = `/api/managers/${managerId}/devices/${currentDeviceId}`;
            method = "PUT";
        } else {
            // Chế độ THÊM
            url = `/api/managers/${managerId}/devices`;
            method = "POST";
        }

        const res = await fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const result = await res.json();
        if (!res.ok) throw new Error(result.message || "Thao tác thất bại!");

        alert(result.message || (isEditMode ? "Cập nhật thành công!" : "Thêm thiết bị thành công!"));
        await refreshDevices();
        bootstrap.Modal.getInstance(document.getElementById('deviceModal')).hide();
        
    } catch (err) {
        alert(err.message);
    }
});

// Render devices
function renderDevices(devices) {
    devicesTableBody.innerHTML = "";
    if (!devices.length) {
        devicesTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-3">Không có thiết bị nào.</td></tr>`;
        return;
    }
    devices.forEach((d, i) => {
        const tr = document.createElement("tr");
        // ✅ ESCAPE ký tự ' trong device_serial để tránh lỗi JavaScript
        const escapedSerial = d.device_serial.replace(/'/g, "\\'");
        tr.innerHTML = `
            <td class="ps-4">${i + 1}</td>
            <td>${d.device_serial}</td>
            <td>${d.status === "online" ? '<span class="badge bg-success">Online</span>' : '<span class="badge bg-secondary">Offline</span>'}</td>
            <td>${formatDateTime(d.last_seen) || '-'}</td>
            <td class="text-center">
                <button class="btn btn-sm btn-warning me-1" onclick="openEditModal(${d.device_id}, '${escapedSerial}')">
                    <i class="bi bi-pencil"></i> Sửa
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteDevice(${d.device_id})">
                    <i class="bi bi-trash"></i> Xóa
                </button>
            </td>
        `;
        devicesTableBody.appendChild(tr);
    });
}

async function refreshDevices() {
    try {
        const res = await fetch(`/api/managers/${managerId}/devices`);
        if (!res.ok) throw new Error("Lấy danh sách thất bại");
        const devices = await res.json();
        renderDevices(devices);
    } catch (err) {
        console.error(err);
    }
}

// Polling mỗi 3 giây
setInterval(refreshDevices, 3000);

// Load lần đầu
refreshDevices();


let selectedFirmwareFile = null;


// ============= FIRMWARE UPDATE =============


// Load danh sách thiết bị cho firmware
async function loadDevicesForFirmware() {
    const select = document.getElementById('firmwareDeviceSelect');
    
    console.log('[DEBUG] Bắt đầu load thiết bị cho firmware...');
    console.log('[DEBUG] Select element:', select);
    console.log('[DEBUG] Manager ID:', managerId);
    
    if (!select) {
        console.error('❌ Không tìm thấy element #firmwareDeviceSelect');
        return;
    }
    
    try {
        const url = `/api/managers/${managerId}/devices`;
        console.log('[DEBUG] Đang gọi API:', url);
        
        const response = await fetch(url);
        console.log('[DEBUG] Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: Không thể tải danh sách thiết bị`);
        }
        
        const devices = await response.json();
        console.log('[DEBUG] Dữ liệu nhận được:', devices);
        console.log('[DEBUG] Số lượng thiết bị:', devices.length);
        
        select.innerHTML = '<option value="">— Chọn thiết bị —</option>';
        
        if (devices.length === 0) {
            console.warn('⚠️ Không có thiết bị nào trong hệ thống');
            select.innerHTML += '<option disabled>Không có thiết bị nào</option>';
            return;
        }
        
        devices.forEach((device, index) => {
            console.log(`[DEBUG] Thêm thiết bị ${index + 1}:`, device);
            
            const option = document.createElement('option');
            option.value = device.device_serial;
            option.textContent = `${device.device_serial} - ${device.status || 'unknown'}`;
            option.dataset.deviceId = device.device_id;
            select.appendChild(option);
        });
        
        console.log(`✅ Đã load ${devices.length} thiết bị thành công`);
        
    } catch (error) {
        console.error('❌ Lỗi khi load thiết bị:', error);
        alert('Không thể tải danh sách thiết bị:\n' + error.message);
    }
}

// Xử lý khi chọn file
const firmwareFileInput = document.getElementById('firmwareFileInput');
if (firmwareFileInput) {
    firmwareFileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        const fileNameDisplay = document.getElementById('selectedFileName');
        
        if (file) {
            if (!file.name.endsWith('.bin')) {
                alert('Vui lòng chọn file .bin');
                this.value = '';
                selectedFirmwareFile = null;
                if (fileNameDisplay) fileNameDisplay.classList.add('d-none');
                return;
            }
            
            selectedFirmwareFile = file;
            if (fileNameDisplay) {
                fileNameDisplay.textContent = `✓ Đã chọn: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`;
                fileNameDisplay.classList.remove('d-none');
            }
        } else {
            selectedFirmwareFile = null;
            if (fileNameDisplay) fileNameDisplay.classList.add('d-none');
        }
    });
}

// Hàm kiểm tra trạng thái OTA
async function checkOTAStatus(deviceSerial, statusBox, progressBar) {
    let attempts = 0;
    const maxAttempts = 120;
    
    return new Promise((resolve, reject) => {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`/api/managers/${managerId}/ota_status/${deviceSerial}`);
                const data = await response.json();
                
                const progress = data.progress || 0;
                const status = data.status || 'idle';
                const reason = data.reason || '';
                
                progressBar.style.width = `${progress}%`;
                
                
                if (status === 'downloading') {
                    statusBox.textContent = `Đang tải firmware... ${progress}%`;
                    statusBox.className = 'border rounded-4 p-3 bg-white text-center text-info fw-semibold';
                } else if (status === 'updating') {
                    statusBox.textContent = `Đang cập nhật... ${progress}%`;
                    statusBox.className = 'border rounded-4 p-3 bg-white text-center text-warning fw-semibold';
                } else if (status === 'success') {
                    statusBox.textContent = '✓ Cập nhật thành công!';
                    statusBox.className = 'border rounded-4 p-3 bg-white text-center text-success fw-semibold';
                    progressBar.style.width = '100%';
                    clearInterval(interval);
                    resolve(true);
                } else if (status === 'error') {
                    statusBox.textContent = `✗ Lỗi: ${reason}`;
                    statusBox.className = 'border rounded-4 p-3 bg-white text-center text-danger fw-semibold';
                    clearInterval(interval);
                    reject(new Error(reason || 'Cập nhật thất bại'));
                }
                
                attempts++;
                if (attempts >= maxAttempts && status !== 'success') {
                    clearInterval(interval);
                    reject(new Error('Timeout - Vượt quá thời gian chờ'));
                }
            } catch (error) {
                console.error('Lỗi kiểm tra OTA status:', error);
            }
        }, 1000);
    });
}

// Xử lý cập nhật firmware
const startFirmwareUpdateBtn = document.getElementById('startFirmwareUpdateBtn');
if (startFirmwareUpdateBtn) {
    startFirmwareUpdateBtn.addEventListener('click', async function() {
        const deviceSerial = document.getElementById('firmwareDeviceSelect').value;
        const statusBox = document.getElementById('firmwareStatusBox');
        const progressBar = document.getElementById('firmwareProgress');
        const updateBtn = this;
        
        if (!deviceSerial) {
            alert('Vui lòng chọn thiết bị cần cập nhật');
            return;
        }
        
        if (!selectedFirmwareFile) {
            alert('Vui lòng chọn file firmware (.bin)');
            return;
        }
        
        const select = document.getElementById('firmwareDeviceSelect');
        const selectedOption = select.options[select.selectedIndex];
        const deviceName = selectedOption.textContent;
        
        if (!confirm(`Bạn có chắc muốn cập nhật firmware cho thiết bị "${deviceName}"?\n\n⚠️ LƯU Ý: KHÔNG ngắt nguồn trong quá trình cập nhật!`)) {
            return;
        }
        
        updateBtn.disabled = true;
        document.getElementById('firmwareDeviceSelect').disabled = true;
        document.getElementById('firmwareFileInput').disabled = true;
        
        try {
            statusBox.textContent = 'Đang gửi firmware lên server...';
            statusBox.className = 'border rounded-4 p-3 bg-white text-center text-info fw-semibold';
            progressBar.style.width = '10%';
            
            const formData = new FormData();
            formData.append('firmware', selectedFirmwareFile);
            
            const response = await fetch(`/api/managers/${managerId}/update_firmware/${deviceSerial}`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Lỗi khi gửi firmware');
            }
            
            const result = await response.json();
            
            if (result.status === 'success') {
                statusBox.textContent = 'Đã gửi lệnh OTA, đang chờ phản hồi từ thiết bị...';
                progressBar.style.width = '20%';
                
                await checkOTAStatus(deviceSerial, statusBox, progressBar);
                
                alert(`✓ Cập nhật firmware cho thiết bị "${deviceName}" thành công!`);
                
                setTimeout(() => {
                    resetFirmwareUpdate();
                }, 3000);
                
            } else {
                throw new Error(result.message || 'Không thể gửi lệnh OTA');
            }
            
        } catch (error) {
            console.error('Lỗi cập nhật firmware:', error);
            statusBox.textContent = `✗ Lỗi: ${error.message}`;
            statusBox.className = 'border rounded-4 p-3 bg-white text-center text-danger fw-semibold';
            progressBar.style.width = '0%';
            
            alert('❌ Cập nhật firmware thất bại:\n' + error.message);
            
            updateBtn.disabled = false;
            document.getElementById('firmwareDeviceSelect').disabled = false;
            document.getElementById('firmwareFileInput').disabled = false;
        }
    });
}

// Reset form cập nhật firmware
function resetFirmwareUpdate() {
    const deviceSelect = document.getElementById('firmwareDeviceSelect');
    const fileInput = document.getElementById('firmwareFileInput');
    const fileName = document.getElementById('selectedFileName');
    const statusBox = document.getElementById('firmwareStatusBox');
    const progressBar = document.getElementById('firmwareProgress');
    const updateBtn = document.getElementById('startFirmwareUpdateBtn');
    
    if (deviceSelect) {
        deviceSelect.value = '';
        deviceSelect.disabled = false;
    }
    if (fileInput) {
        fileInput.value = '';
        fileInput.disabled = false;
    }
    if (fileName) fileName.classList.add('d-none');
    if (statusBox) {
        statusBox.textContent = 'Chưa bắt đầu';
        statusBox.className = 'border rounded-4 p-3 bg-white text-center text-muted fw-semibold';
    }
    if (progressBar) progressBar.style.width = '0%';
    if (updateBtn) updateBtn.disabled = false;
    
    selectedFirmwareFile = null;
}


// ============= KẾT THÚC FIRMWARE UPDATE =============

});