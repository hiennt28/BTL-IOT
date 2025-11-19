// assets/js/doctor.js

// === Helpers ===
function formatDate(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        const day = String(date.getUTCDate()).padStart(2, '0');
        const month = String(date.getUTCMonth() + 1).padStart(2, '0');
        const year = date.getUTCFullYear();
        return `${day}/${month}/${year}`;
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
function getStatusClass(status) {
    if (!status) return 'status-unknown';
    const s = String(status).toLowerCase();
    if (s.includes('cảnh báo') || s.includes('nguy hiểm') || s.includes('bất thường') || s.includes('ngã')) return 'status-warning';
    if (s.includes('hoạt động mạnh') || s.includes('cực độ')) return 'status-strong';
    if (s.includes('hoạt động trung bình')) return 'status-medium';
    if (s.includes('hoạt động nhẹ')) return 'status-light';
    if (s.includes('bình thường')) return 'status-normal';
    return 'status-unknown';
}
function formatValue(val) {
    if (val === 0 || val === "0") return "0";
    if (val) return val;
    return "0";
}

document.addEventListener("DOMContentLoaded", async () => {
    console.log("Doctor Dashboard Loaded");
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user || user.role !== 'doctor') { window.location.href="/login.html"; return; }
    const doctorId = user.doctor_id;

    // --- INITIALIZE MODALS ---
    let updateDoctorInfoModal = null;
    let changePasswordModal = null;
    try {
        const updateEl = document.getElementById('updateDoctorInfoModal');
        if(updateEl) updateDoctorInfoModal = new bootstrap.Modal(updateEl);
        const passEl = document.getElementById('changePasswordModal');
        if(passEl) changePasswordModal = new bootstrap.Modal(passEl);
    } catch(e) { console.error(e); }

    // --- PROFILE ---
    if(document.getElementById("userProfileName")) document.getElementById("userProfileName").innerText = user.full_name;

    // --- TAB SWITCHING ---
    document.querySelectorAll("#sidebar .nav-link").forEach(link => {
        link.addEventListener("click", e => {
            e.preventDefault();
            document.querySelectorAll("#sidebar .nav-link").forEach(l=>l.classList.remove("active"));
            link.classList.add("active");
            document.querySelectorAll(".tab-content").forEach(t=>t.classList.add("d-none"));
            
            const tabId = link.dataset.tab;
            const tabContent = document.getElementById("tab-" + tabId);
            if(tabContent) tabContent.classList.remove("d-none");
            
            if(tabId === 'patients') loadPatients();
            if(tabId === 'alerts') loadAlerts();
            if(tabId === 'profile') loadDoctorInfo();
        });
    });

    // --- LOGOUT ---
    document.getElementById("logoutBtn").addEventListener("click", ()=> {
        localStorage.removeItem("user");
        window.location.href="/login.html";
    });

    // ==========================================
    // LOGIC TAB BỆNH NHÂN & CHỌN BỆNH NHÂN
    // ==========================================
    
    let monitoringInterval = null; // Biến giữ interval để xóa khi đổi bệnh nhân
    let bpmChart = null;
    let latestTimestamp = null;

    async function loadPatients() {
        try {
            const res = await fetch(`/api/doctors/${doctorId}/patients`);
            if(!res.ok) return;
            const data = await res.json();
            
            // 1. Fill Table
            const tbody = document.getElementById("patients-table-body");
            if(tbody) {
                tbody.innerHTML = "";
                if (data.length === 0) { tbody.innerHTML = "<tr><td colspan='5' class='text-center'>Chưa có bệnh nhân nào.</td></tr>"; }
                else {
                    data.forEach((p,i)=>{
                        const tr = document.createElement("tr");
                        tr.innerHTML = `
                            <td class="ps-4 fw-bold">${i+1}</td>
                            <td>${p.full_name}</td>
                            <td>${p.email}</td>
                            <td>${p.phone_number || ''}</td>
                            <td><button class="btn btn-sm btn-outline-primary view-health-btn" data-id="${p.patient_id}">Xem sức khỏe</button></td>`;
                        tbody.appendChild(tr);
                    });
                    
                    // Nút "Xem sức khỏe" chuyển sang tab Health
                    document.querySelectorAll(".view-health-btn").forEach(btn => {
                        btn.addEventListener("click", () => {
                            const pid = btn.dataset.id;
                            // Chuyển tab
                            document.querySelector('[data-tab="health"]').click();
                            // Chọn bệnh nhân
                            const select = document.getElementById("select-patient");
                            select.value = pid;
                            select.dispatchEvent(new Event('change')); // Kích hoạt sự kiện change
                        });
                    });
                }
            }

            // 2. Fill Select Dropdown (Tab Health)
            const select = document.getElementById("select-patient");
            if(select) {
                // Giữ lại option đầu tiên
                const defaultOpt = select.firstElementChild;
                select.innerHTML = "";
                select.appendChild(defaultOpt);
                
                data.forEach(p => {
                    const opt = document.createElement("option");
                    opt.value = p.patient_id;
                    opt.text = p.full_name;
                    select.appendChild(opt);
                });
            }

        } catch(err){ console.error(err); }
    }
    await loadPatients(); // Load ngay khi vào

    // --- SỰ KIỆN CHỌN BỆNH NHÂN ---
    const selectPatient = document.getElementById("select-patient");
    if(selectPatient) {
        selectPatient.addEventListener("change", (e) => {
            const patientId = e.target.value;
            
            // Reset Interval cũ
            if(monitoringInterval) clearInterval(monitoringInterval);
            
            if(!patientId) {
                // Ẩn dashboard
                document.getElementById("health-dashboard").classList.add("d-none");
                document.getElementById("no-patient-selected").classList.remove("d-none");
                return;
            }

            // Hiện dashboard
            document.getElementById("health-dashboard").classList.remove("d-none");
            document.getElementById("no-patient-selected").classList.add("d-none");
            
            // Reset Chart Timestamp để vẽ mới
            latestTimestamp = null;
            
            // Load dữ liệu ngay
            loadPatientStatus(patientId);
            loadPatientRealtimeData(patientId);
            initChart(patientId, document.getElementById("chart-range").value);
            
            // Set Interval mới (3s/lần)
            monitoringInterval = setInterval(() => {
                loadPatientStatus(patientId);
                loadPatientRealtimeData(patientId);
            }, 3000);
        });
    }

    // Load Status & Device Info
    async function loadPatientStatus(pid) {
        try {
            const res = await fetch(`/api/patients/${pid}`);
            if(!res.ok) return;
            const data = await res.json();
            
            // Status AI
            const statusSpan = document.getElementById("patient_health_status");
            const statusText = data.current_health_status || 'Đang chờ dữ liệu...';
            statusSpan.innerText = statusText;
            statusSpan.className = "fs-3 fw-bold " + getStatusClass(statusText);

            // Device Info
            document.getElementById("patient_device_serial").innerText = data.device_serial || "Chưa gán";
            document.getElementById("patient_device_status").innerText = data.device_status || "Offline";
            
            const measureSpan = document.getElementById("patient_measuring_status");
            if (data.is_measuring === 1) {
                measureSpan.innerText = "ĐANG ĐO...";
                measureSpan.className = "fw-bold device-active blink";
            } else {
                measureSpan.innerText = "ĐÃ DỪNG";
                measureSpan.className = "fw-bold device-inactive";
            }
        } catch(err) { console.error(err); }
    }

    // Load Stats Cards & Update Chart
    async function loadPatientRealtimeData(pid) {
        try {
            const res = await fetch(`/api/health/latest/${pid}`);
            if(!res.ok) return;
            const data = await res.json();

            // Update Cards
            ['bpm_val','ir_val','accel_x_val','accel_y_val','accel_z_val','a_total_val'].forEach(id => {
                const key = id.replace('_val', '');
                const el = document.getElementById(id);
                if(el) el.innerText = formatValue(data[key]);
            });

            // Update Chart (Running effect)
            if (bpmChart && data.timestamp) {
                const newTime = new Date(data.timestamp).getTime();
                // Chỉ thêm nếu là dữ liệu mới
                if (!latestTimestamp || newTime > latestTimestamp) {
                    latestTimestamp = newTime;
                    const label = new Date(data.timestamp).toLocaleTimeString();
                    const bpm = (data.bpm === null || data.bpm === undefined) ? 0 : data.bpm;
                    
                    bpmChart.data.labels.push(label);
                    bpmChart.data.datasets.forEach((dataset) => dataset.data.push(bpm));
                    
                    if (bpmChart.data.labels.length > 20) {
                        bpmChart.data.labels.shift();
                        bpmChart.data.datasets.forEach((dataset) => dataset.data.shift());
                    }
                    bpmChart.update('none');
                }
            }

        } catch(err) { console.error(err); }
    }

    // Init Chart
    async function initChart(pid, range="day") {
        try {
            const res = await fetch(`/api/health/history/${pid}?range=${range}`);
            if(!res.ok) return;
            let data = await res.json();
            
            const ctxEl = document.getElementById("bpmChart");
            if(!ctxEl) return;

            if(range === 'day' && data.length > 20) data = data.slice(data.length - 20);
            if(data.length > 0) latestTimestamp = new Date(data[data.length-1].timestamp).getTime();

            const labels = data.map(d=> new Date(d.timestamp).toLocaleTimeString());
            const bpmValues = data.map(d => (d.bpm === null || d.bpm === undefined) ? 0 : d.bpm);

            if(bpmChart) bpmChart.destroy();

            const ctx = ctxEl.getContext("2d");
            const gradient = ctx.createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, 'rgba(220, 53, 69, 0.6)');
            gradient.addColorStop(1, 'rgba(220, 53, 69, 0.0)');

            bpmChart = new Chart(ctx, {
                type: "line",
                data: {
                    labels: labels,
                    datasets: [{
                        label: "Nhịp tim (BPM)",
                        data: bpmValues,
                        borderColor: "#dc3545",
                        backgroundColor: gradient,
                        borderWidth: 2,
                        pointRadius: 3,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: { legend: { display: true, position: 'top' } },
                    scales: {
                        x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 6 } },
                        y: { beginAtZero: true, min: 0, grid: { color: 'rgba(0,0,0,0.05)' } }
                    }
                }
            });
        } catch(err) { console.error(err); }
    }
    
    // Range Select Listener
    const rangeSelect = document.getElementById("chart-range");
    if(rangeSelect) {
        rangeSelect.addEventListener("change", (e) => {
            const pid = document.getElementById("select-patient").value;
            if(pid) initChart(pid, e.target.value);
        });
    }

    // ==========================================
    // CÁC TAB KHÁC (ALERTS, PROFILE...)
    // ==========================================

    async function loadAlerts(){
        try {
            const res = await fetch(`/api/doctors/${doctorId}/alerts`);
            if(!res.ok) return;
            const data = await res.json();
            const container = document.getElementById("alerts-table");
            if(!container) return;
            
            container.innerHTML = "";
            if (data.length === 0) { container.innerHTML = "<p class='text-center py-3 text-muted'>Không có cảnh báo nào.</p>"; return; }
            
            data.forEach(a=>{
                const div = document.createElement("div");
                let statusClass = a.status === 'new' ? 'list-group-item-danger' : 'list-group-item-light';
                div.className = "list-group-item " + statusClass;
                div.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${a.alert_type}</strong> <span class="badge bg-secondary ms-2">${a.full_name}</span>
                            <p class="mb-0 mt-1 text-muted small">${a.message}</p>
                        </div>
                        <div class="text-end">
                             <small class="d-block mb-2">${new Date(a.timestamp).toLocaleString()}</small>
                             ${a.status === 'new' ? `<button class="btn btn-sm btn-warning mark-viewed" data-id="${a.alert_id}">Đã xem</button>` : ''}
                        </div>
                    </div>`;
                container.appendChild(div);
            });

            // Action buttons logic
            document.querySelectorAll('.mark-viewed').forEach(btn => {
                btn.addEventListener('click', async () => {
                    await fetch(`/api/doctors/alerts/${btn.dataset.id}`, {
                        method: 'PUT', headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ status: 'viewed', doctor_id: doctorId })
                    });
                    loadAlerts();
                });
            });
            
        } catch(err){ console.error(err); }
    }

    async function loadDoctorInfo() {
        try {
            const res = await fetch(`/api/doctors/${doctorId}`);
            if(!res.ok) return;
            const data = await res.json();
            ['doc_full_name','doc_email','doc_phone_number','doc_address','doc_date_of_birth','doc_title','doc_specialty'].forEach(id => {
                const key = id.replace('doc_', '');
                const key2 = key === 'date_of_birth' ? key : (key === 'full_name' ? key : (key === 'email' ? key : (key === 'phone_number' ? 'phone_number' : (key === 'address' ? 'address' : (key==='title'?'title':'specialty')))));
                // Simple map based on api keys
                const apiKeys = {
                    'doc_full_name': 'full_name', 'doc_email': 'email', 'doc_phone_number': 'phone_number',
                    'doc_address': 'address', 'doc_date_of_birth': 'date_of_birth', 'doc_title': 'title', 'doc_specialty': 'specialty'
                };
                if(document.getElementById(id)) document.getElementById(id).innerText = data[apiKeys[id]] || '';
            });
            // DOB format
            if(document.getElementById("doc_date_of_birth")) document.getElementById("doc_date_of_birth").innerText = formatDate(data.date_of_birth);
        } catch(err) { console.error(err); }
    }

    // --- MODAL EVENTS ---
    const docUpdateBtn = document.getElementById("doc-update-info-btn");
    if(docUpdateBtn) docUpdateBtn.addEventListener("click", ()=> {
        if(updateDoctorInfoModal) updateDoctorInfoModal.show();
        // Populate fields... 
    });
    
    const saveDocInfoBtn = document.getElementById("saveDoctorInfoBtn");
    if(saveDocInfoBtn) saveDocInfoBtn.addEventListener("click", async () => {
        const body = {
            full_name: document.getElementById("modalDocFullName").value,
            phone_number: document.getElementById("modalDocPhone").value,
            address: document.getElementById("modalDocAddress").value,
            date_of_birth: document.getElementById("modalDocDOB").value,
            title: document.getElementById("modalDocTitle").value,
            specialty: document.getElementById("modalDocSpecialty").value
        };
        try {
            await fetch(`/api/doctors/update/${doctorId}`, {method:"PUT", headers:{"Content-Type":"application/json"}, body: JSON.stringify(body)});
            alert("Cập nhật thành công!");
            loadDoctorInfo(); updateDoctorInfoModal.hide();
        } catch(e) { alert("Lỗi"); }
    });

    const changePassBtn = document.getElementById("doc-change-pass-btn");
    if(changePassBtn) changePassBtn.addEventListener("click", () => {
        if(changePasswordModal) changePasswordModal.show();
    });
    
    const saveNewPassBtn = document.getElementById("saveNewPassBtn");
    if(saveNewPassBtn) saveNewPassBtn.addEventListener("click", async () => {
        const old_password = document.getElementById("modalOldPass").value;
        const new_password = document.getElementById("modalNewPass").value;
        try {
            const res = await fetch(`/api/auth/change-password`, { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({ email: user.email, role: user.role, old_password, new_password }) });
            const data = await res.json();
            alert(data.message);
            if(data.success) changePasswordModal.hide();
        } catch(err) { alert("Lỗi máy chủ"); }
    });
});