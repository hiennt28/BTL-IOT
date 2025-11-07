document.addEventListener("DOMContentLoaded", async () => {
    const user = JSON.parse(localStorage.getItem("user"));
    if (!user) { window.location.href="/login.html"; return; }
    const patientId = user.patient_id;

    // Sidebar tab switching
    document.querySelectorAll("#sidebar .nav-link").forEach(link => {
        link.addEventListener("click", e => {
            e.preventDefault();
            document.querySelectorAll("#sidebar .nav-link").forEach(l=>l.classList.remove("active"));
            link.classList.add("active");
            document.querySelectorAll(".tab-content").forEach(t=>t.classList.add("d-none"));
            document.getElementById("tab-" + link.dataset.tab).classList.remove("d-none");
        });
    });

    // Logout
    document.getElementById("logoutBtn").addEventListener("click", ()=> {
        localStorage.removeItem("user");
        window.location.href="/login.html";
    });

    // 1️⃣ Load thông tin cá nhân
    async function loadPatientInfo() {
        try {
            const res = await fetch(`/api/patients/${patientId}`);
            if(!res.ok) throw new Error("Không tìm thấy bệnh nhân!");
            const data = await res.json();
            document.getElementById("full_name").innerText = data.full_name;
            document.getElementById("email").innerText = data.email;
            document.getElementById("phone_number").innerText = data.phone_number;
            document.getElementById("address").innerText = data.address;
            document.getElementById("date_of_birth").innerText = data.date_of_birth;
        } catch(err) { console.error("Lỗi khi lấy dữ liệu bệnh nhân!", err); }
    }
    loadPatientInfo();

    // 1️⃣.1 Popup modal cập nhật thông tin
    document.getElementById("update-info-btn").addEventListener("click", ()=> {
        document.getElementById("modalFullName").value = document.getElementById("full_name").innerText;
        document.getElementById("modalPhone").value = document.getElementById("phone_number").innerText;
        document.getElementById("modalAddress").value = document.getElementById("address").innerText;
        document.getElementById("modalDOB").value = document.getElementById("date_of_birth").innerText;

        const modal = new bootstrap.Modal(document.getElementById('updateInfoModal'));
        modal.show();
    });

    document.getElementById("saveInfoBtn").addEventListener("click", async ()=> {
        const full_name = document.getElementById("modalFullName").value;
        const phone_number = document.getElementById("modalPhone").value;
        const address = document.getElementById("modalAddress").value;
        const date_of_birth = document.getElementById("modalDOB").value;

        try {
            const res = await fetch(`/api/patients/update/${patientId}`, {
                method:"PUT",
                headers:{"Content-Type":"application/json"},
                body: JSON.stringify({full_name, phone_number, address, date_of_birth})
            });
            if(!res.ok) throw new Error("Cập nhật thất bại!");
            loadPatientInfo();
            bootstrap.Modal.getInstance(document.getElementById('updateInfoModal')).hide();
        } catch(err) { alert(err.message); }
    });

    // 2️⃣ Load dữ liệu realtime health
    async function loadLatestHealth(){
        try {
            const res = await fetch(`/api/health/latest/${patientId}`);
            if(!res.ok) return;
            const data = await res.json();
            document.getElementById("bpm_val").innerText = data.bpm;
            document.getElementById("ir_val").innerText = data.ir_value;
            document.getElementById("accel_x_val").innerText = data.accel_x;
            document.getElementById("accel_y_val").innerText = data.accel_y;
            document.getElementById("accel_z_val").innerText = data.accel_z;
            document.getElementById("a_total_val").innerText = data.a_total;
        } catch(err) { console.error(err); }
    }
    loadLatestHealth(); setInterval(loadLatestHealth,5000);

    // 3️⃣ Load chart
    let bpmChart;
    async function loadChart(range="day"){
        try {
            const res = await fetch(`/api/health/history/${patientId}?range=${range}`);
            if(!res.ok) return;
            const data = await res.json();
            const ctx = document.getElementById("bpmChart").getContext("2d");
            const labels = data.map(d=>new Date(d.timestamp).toLocaleString());
            const bpmValues = data.map(d=>d.bpm);
            if(bpmChart) bpmChart.destroy();
            bpmChart = new Chart(ctx,{
                type:"line",
                data:{labels,datasets:[{label:"BPM",data:bpmValues,borderColor:"red",fill:false}]},
                options:{responsive:true,maintainAspectRatio:false}
            });
        } catch(err){ console.error(err); }
    }
    loadChart();
    document.getElementById("chart-range").addEventListener("change", e=> loadChart(e.target.value));

    // 4️⃣ Load alerts
    async function loadAlerts(){
        try {
            const res = await fetch(`/api/alerts/${patientId}`);
            if(!res.ok) return;
            const data = await res.json();
            const container = document.getElementById("alerts-table");
            container.innerHTML = "";
            data.forEach(a=>{
                const div = document.createElement("div");
                div.className = "list-group-item " + (a.status=="new"?"list-group-item-danger":"list-group-item-secondary");
                div.innerHTML = `<strong>${a.alert_type}</strong>: ${a.message} <small class="text-muted">${a.timestamp}</small>`;
                container.appendChild(div);
            });
        } catch(err){ console.error(err); }
    }
    loadAlerts();

    // 5️⃣ Load history
    async function loadHistory(){
        try {
            const res = await fetch(`/api/health/history/${patientId}?range=month`);
            if(!res.ok) return;
            const data = await res.json();
            const tbody = document.getElementById("history-table-body");
            tbody.innerHTML = "";
            data.forEach(d=>{
                const tr = document.createElement("tr");
                tr.innerHTML = `<td>${d.bpm}</td><td>${d.ir_value}</td><td>${d.accel_x}</td><td>${d.accel_y}</td><td>${d.accel_z}</td><td>${d.a_total}</td><td>${d.timestamp}</td>`;
                tbody.appendChild(tr);
            });
        } catch(err){ console.error(err); }
    }
    loadHistory();
});
