// assets/js/patient.js

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

function formatTime(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        const hours = String(date.getUTCHours()).padStart(2, '0');
        const minutes = String(date.getUTCMinutes()).padStart(2, '0');
        const seconds = String(date.getUTCSeconds()).padStart(2, '0');
        return `${hours}:${minutes}:${seconds}`;
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
// ============================================================

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
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user || user.role !== 'patient') { window.location.href="/login.html"; return; }
    
    const patientId = user.patient_id;
    let currentPatientData = {};

    let updateInfoModal = null;
    let changePasswordModal = null;
    let wifiModal = null; // Modal Wifi Mới
    
    try {
        const updateEl = document.getElementById('updateInfoModal');
        if(updateEl) updateInfoModal = new bootstrap.Modal(updateEl);
        const passEl = document.getElementById('changePasswordModal');
        if(passEl) changePasswordModal = new bootstrap.Modal(passEl);
        const wifiEl = document.getElementById('wifiModal'); // Init Wifi Modal
        if(wifiEl) wifiModal = new bootstrap.Modal(wifiEl);
    } catch(e) { console.error(e); }

    const updateInfoBtn = document.getElementById("update-info-btn");
    if(updateInfoBtn) {
        updateInfoBtn.addEventListener("click", () => {
            if(document.getElementById("modalFullName")) document.getElementById("modalFullName").value = currentPatientData.full_name || '';
            if(document.getElementById("modalPhone")) document.getElementById("modalPhone").value = currentPatientData.phone_number || '';
            if(document.getElementById("modalAddress")) document.getElementById("modalAddress").value = currentPatientData.address || '';
            if(document.getElementById("modalDOB")) document.getElementById("modalDOB").value = formatDateForInput(currentPatientData.date_of_birth) || '';
            if(updateInfoModal) updateInfoModal.show();
        });
    }

    const saveInfoBtn = document.getElementById("saveInfoBtn");
    if(saveInfoBtn) {
        saveInfoBtn.addEventListener("click", async () => {
            const body = {
                full_name: document.getElementById("modalFullName").value,
                phone_number: document.getElementById("modalPhone").value,
                address: document.getElementById("modalAddress").value,
                date_of_birth: document.getElementById("modalDOB").value
            };
            try {
                const res = await fetch(`/api/patients/update/${patientId}`, { 
                    method:"PUT", headers:{"Content-Type":"application/json"}, body: JSON.stringify(body)
                });
                if(res.ok) {
                    alert("Cập nhật thành công!");
                    await loadPatientInfo(); 
                    if(updateInfoModal) updateInfoModal.hide();
                } else { alert("Cập nhật thất bại!"); }
            } catch(err) { alert("Lỗi kết nối server!"); }
        });
    }
    
    const changePassBtn = document.getElementById("change-pass-btn");
    if(changePassBtn) {
        changePassBtn.addEventListener("click", () => {
            if(document.getElementById("modalOldPass")) document.getElementById("modalOldPass").value = "";
            if(document.getElementById("modalNewPass")) document.getElementById("modalNewPass").value = "";
            if(changePasswordModal) changePasswordModal.show();
        });
    }

    const saveNewPassBtn = document.getElementById("saveNewPassBtn");
    if(saveNewPassBtn) {
        saveNewPassBtn.addEventListener("click", async () => {
            const old_password = document.getElementById("modalOldPass").value;
            const new_password = document.getElementById("modalNewPass").value;
            try {
                const res = await fetch(`/api/auth/change-password`, { 
                    method:"POST", headers:{"Content-Type":"application/json"}, 
                    body: JSON.stringify({ email: user.email, role: user.role, old_password, new_password }) 
                });
                const data = await res.json();
                alert(data.message);
                if(data.success && changePasswordModal) changePasswordModal.hide();
            } catch(err) { alert("Lỗi máy chủ"); }
        });
    }
    
    // === XỬ LÝ CẤU HÌNH WIFI ===
    const saveWifiBtn = document.getElementById("saveWifiBtn");
    if(saveWifiBtn) {
        saveWifiBtn.addEventListener("click", async () => {
            const ssid = document.getElementById("wifiSSID").value;
            const pass = document.getElementById("wifiPass").value;
            
            if(!ssid) { alert("Vui lòng nhập tên Wifi!"); return; }

            try {
                const res = await fetch(`/api/patients/${patientId}/device/wifi-config`, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ ssid: ssid, password: pass })
                });
                
                const data = await res.json();
                
                if(res.ok) {
                    alert(data.message);
                    if(wifiModal) wifiModal.hide();
                    document.getElementById("wifiSSID").value = ""; // Reset form
                    document.getElementById("wifiPass").value = "";
                } else {
                    alert("Lỗi: " + data.message);
                }
            } catch(err) {
                console.error(err);
                alert("Lỗi kết nối server!");
            }
        });
    }

    const logoutBtn = document.getElementById("logoutBtn");
    if(logoutBtn) {
        logoutBtn.addEventListener("click", ()=> {
            localStorage.removeItem("user");
            window.location.href="/login.html";
        });
    }

    document.querySelectorAll("#sidebar .nav-link").forEach(link => {
        link.addEventListener("click", e => {
            e.preventDefault();
            document.querySelectorAll("#sidebar .nav-link").forEach(l=>l.classList.remove("active"));
            link.classList.add("active");
            document.querySelectorAll(".tab-content").forEach(t=>t.classList.add("d-none"));
            
            const tabId = link.dataset.tab;
            const tabContent = document.getElementById("tab-" + tabId);
            if(tabContent) tabContent.classList.remove("d-none");
            
            if (tabId === 'history') { loadHistory(); }
            if (tabId === 'health') { 
                setTimeout(() => {
                    const range = document.getElementById("chart-range") ? document.getElementById("chart-range").value : "day";
                    initChart(range);
                }, 150);
            }
        });
    });

    if(document.getElementById("userProfileName")) document.getElementById("userProfileName").innerText = user.full_name;
    if(document.getElementById("userProfileRole")) document.getElementById("userProfileRole").innerText = user.role;

    async function loadPatientInfo() {
        try {
            const res = await fetch(`/api/patients/${patientId}?t=${new Date().getTime()}`);
            if(!res.ok) return; 
            
            const data = await res.json();
            currentPatientData = data; 

            const ids = ['full_name', 'email', 'phone_number', 'address', 'doctor_name'];
            ids.forEach(id => {
                const el = document.getElementById(id);
                if(el) el.innerText = data[id] || (id === 'doctor_name' ? 'Chưa được gán' : '');
            });

            if(document.getElementById("date_of_birth")) document.getElementById("date_of_birth").innerText = formatDate(data.date_of_birth) || '';

            const statusSpan = document.getElementById("health_status");
            if(statusSpan) {
                const statusText = data.current_health_status || 'Đang chờ...';
                statusSpan.innerText = statusText;
                statusSpan.className = "fw-bold " + getStatusClass(statusText);
            }

            const deviceSerialEl = document.getElementById("device_serial");
            const deviceStatusEl = document.getElementById("device_connection_status");

            if (data.device_serial) {
                if(deviceSerialEl) deviceSerialEl.innerText = data.device_serial;
                
                if(deviceStatusEl) {
                    const status = (data.device_status || 'Offline').toLowerCase();
                    deviceStatusEl.innerText = status.charAt(0).toUpperCase() + status.slice(1);
                    if (status === 'online') {
                        deviceStatusEl.className = "fw-bold text-success"; 
                    } else {
                        deviceStatusEl.className = "fw-bold text-secondary"; 
                    }
                }
                updateMeasuringUI(data.is_measuring === 1);
            } else {
                if(deviceSerialEl) deviceSerialEl.innerText = "Chưa gán";
                if(deviceStatusEl) {
                    deviceStatusEl.innerText = "N/A";
                    deviceStatusEl.className = "fw-bold text-secondary";
                }
                disableMeasuringControls();
            }
        } catch(err) { console.error(err); }
    }

    function updateMeasuringUI(isMeasuring) {
        const statusText = document.getElementById("measuring_status_text");
        const btnStart = document.getElementById("btn-start-measure");
        const btnStop = document.getElementById("btn-stop-measure");

        if (statusText) {
            if (isMeasuring) {
                statusText.innerText = "ĐANG ĐO...";
                statusText.className = "fw-bold device-active blink";
                if(btnStart) btnStart.disabled = true;
                if(btnStop) btnStop.disabled = false;
            } else {
                statusText.innerText = "ĐÃ DỪNG";
                statusText.className = "fw-bold device-inactive";
                if(btnStart) btnStart.disabled = false;
                if(btnStop) btnStop.disabled = true;
            }
        }
    }
    
    function disableMeasuringControls() {
        const btnStart = document.getElementById("btn-start-measure");
        const btnStop = document.getElementById("btn-stop-measure");
        const statusText = document.getElementById("measuring_status_text");
        const wifiBtn = document.querySelector("[data-bs-target='#wifiModal']"); // Nút wifi

        if(btnStart) btnStart.disabled = true;
        if(btnStop) btnStop.disabled = true;
        if(wifiBtn) wifiBtn.disabled = true; // Khóa nút wifi nếu chưa có thiết bị
        if(statusText) statusText.innerText = "KHÔNG CÓ THIẾT BỊ";
    }

    const btnStart = document.getElementById("btn-start-measure");
    if(btnStart) btnStart.addEventListener("click", () => controlDevice('start'));
    const btnStop = document.getElementById("btn-stop-measure");
    if(btnStop) btnStop.addEventListener("click", () => controlDevice('stop'));

    async function controlDevice(action) {
        try {
            const res = await fetch(`/api/patients/${patientId}/device/control`, {
                method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({ action: action })
            });
            const data = await res.json();
            if (data.success) { await loadPatientInfo(); } else { alert("Lỗi: " + data.message); }
        } catch (err) { alert("Lỗi kết nối server!"); }
    }

    let bpmChart = null;
    let latestTimestamp = null;

    async function loadLatestHealth(){
        try {
            const res = await fetch(`/api/health/latest/${patientId}`);
            if(!res.ok) return;
            const data = await res.json();
            
            if(document.getElementById("bpm_val")) document.getElementById("bpm_val").innerText = formatValue(data.bpm);
            if(document.getElementById("ir_val")) document.getElementById("ir_val").innerText = formatValue(data.ir_value);
            if(document.getElementById("accel_x_val")) document.getElementById("accel_x_val").innerText = formatValue(data.accel_x);
            if(document.getElementById("accel_y_val")) document.getElementById("accel_y_val").innerText = formatValue(data.accel_y);
            if(document.getElementById("accel_z_val")) document.getElementById("accel_z_val").innerText = formatValue(data.accel_z);
            if(document.getElementById("a_total_val")) document.getElementById("a_total_val").innerText = formatValue(data.a_total);

            if (bpmChart && data.timestamp) {
                const newTime = new Date(data.timestamp).getTime();
                if (!latestTimestamp || newTime > latestTimestamp) {
                    latestTimestamp = newTime;
                    const label = formatTime(data.timestamp);
                    const bpm = (data.bpm === null || data.bpm === undefined) ? 0 : data.bpm;
                    addDataToChart(bpmChart, label, bpm);
                }
            }
        } catch(err) { console.error(err); }
    }
    
    function addDataToChart(chart, label, data) {
        chart.data.labels.push(label);
        chart.data.datasets.forEach((dataset) => dataset.data.push(data));
        if (chart.data.labels.length > 20) {
            chart.data.labels.shift();
            chart.data.datasets.forEach((dataset) => dataset.data.shift());
        }
        chart.update('none');
    }

    async function initChart(range="day"){
        try {
            const res = await fetch(`/api/health/history/${patientId}?range=${range}`);
            if(!res.ok) return;
            let data = await res.json();
            const ctxEl = document.getElementById("bpmChart");
            if(!ctxEl || typeof Chart === 'undefined') return;

            if(range === 'day' && data.length > 20) data = data.slice(data.length - 20);

            const labels = data.map(d=> formatTime(d.timestamp));
            const bpmValues = data.map(d => (d.bpm === null || d.bpm === undefined) ? 0 : d.bpm);
            
            if(data.length > 0) latestTimestamp = new Date(data[data.length-1].timestamp).getTime();
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
                        pointHoverRadius: 6,
                        pointBackgroundColor: "#fff",
                        pointBorderColor: "#dc3545",
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: { duration: 1000, easing: 'easeOutQuart' },
                    interaction: { mode: 'index', intersect: false },
                    plugins: { legend: { display: true, position: 'top' } },
                    scales: {
                        x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 6 } },
                        y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' }, border: { display: false } }
                    }
                }
            });
        } catch(err){ console.error("Lỗi vẽ biểu đồ:", err); }
    }
    
    const rangeSelect = document.getElementById("chart-range");
    if(rangeSelect) rangeSelect.addEventListener("change", e=> initChart(e.target.value));

    async function loadAlerts(){
        try {
            const res = await fetch(`/api/alerts/${patientId}`);
            if(!res.ok) return;
            const data = await res.json();
            const container = document.getElementById("alerts-table");
            if(!container) return;
            container.innerHTML = "";
            if (data.length === 0) { container.innerHTML = "<p class='text-center text-muted py-3'>Không có cảnh báo nào.</p>"; return; }
            data.forEach(a=>{
                const div = document.createElement("div");
                let statusClass = a.status === 'new' ? 'list-group-item-danger' : 'list-group-item-light';
                div.className = "list-group-item " + statusClass;
                div.innerHTML = `<div class="d-flex justify-content-between"><strong>${a.alert_type}</strong><small>${formatDateTime(a.timestamp)}</small></div><p class="mb-0">${a.message}</p>`;
                container.appendChild(div);
            });
        } catch(err){ console.error(err); }
    }

    async function loadHistory(){
        try {
            const res = await fetch(`/api/health/history/${patientId}?range=month`);
            if(!res.ok) return;
            const data = await res.json();
            const tbody = document.getElementById("history-table-body");
            if(!tbody) return;
            tbody.innerHTML = "";
            data.reverse().slice(0, 50).forEach(d=>{
                const tr = document.createElement("tr");
                tr.innerHTML = `<td>${formatValue(d.bpm)}</td><td>${d.a_total ? d.a_total.toFixed(2) : '0.00'}</td><td class="${getStatusClass(d.predicted_status)} fw-bold">${d.predicted_status || 'N/A'}</td><td>${formatDateTime(d.timestamp)}</td><td>${formatValue(d.accel_x)}</td><td>${formatValue(d.accel_y)}</td><td>${formatValue(d.accel_z)}</td>`;
                tbody.appendChild(tr);
            });
        } catch(err){ console.error(err); }
    }

    await loadPatientInfo();
    loadLatestHealth();
    loadAlerts();

    setInterval(() => {
        loadLatestHealth(); 
        loadPatientInfo();  
    }, 3000);
});