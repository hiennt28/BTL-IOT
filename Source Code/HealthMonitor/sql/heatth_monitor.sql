-- bước đầu tạo database tên là health_monitor
-- Bảng Quản lý (Managers)
CREATE TABLE Managers (
    manager_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL, -- họ và tên
    email VARCHAR(255) NOT NULL UNIQUE, -- email
    password_hash VARCHAR(255) NOT NULL, -- mật khẩu
    phone_number VARCHAR(20), -- số điện thoại
    address TEXT, -- địa chỉ
    date_of_birth DATE, -- ngày tháng năm sinh
    title VARCHAR(100), -- chức danh
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Bác sĩ (Doctors)
CREATE TABLE Doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    manager_id INT, -- Mỗi bác sĩ thuộc về một người quản lý
    full_name VARCHAR(255) NOT NULL, -- họ và tên
    email VARCHAR(255) NOT NULL UNIQUE, -- email
    password_hash VARCHAR(255) NOT NULL, -- mật khẩu
    phone_number VARCHAR(20), -- số điện thoại
    address TEXT, -- địa chỉ
    date_of_birth DATE, -- ngày tháng năm sinh
    title VARCHAR(100), -- chức danh
    specialty VARCHAR(100), -- khoa chuyên môn
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES Managers(manager_id) ON DELETE SET NULL
);

-- Bảng Thiết bị (Devices)
CREATE TABLE Devices (
    device_id INT AUTO_INCREMENT PRIMARY KEY,
    device_serial VARCHAR(100) NOT NULL UNIQUE, -- mã định danh thiết bị vật lý
    status ENUM('online', 'offline', 'error') DEFAULT 'offline', -- trạng thái thiết bị
    last_seen TIMESTAMP, -- lần cuối hoạt động
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Bệnh nhân (Patients)
CREATE TABLE Patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id INT, -- bác sĩ theo dõi
    manager_id INT, -- quản lý phụ trách
    device_id INT UNIQUE, -- thiết bị gắn kèm (1-1)
    full_name VARCHAR(255) NOT NULL, -- họ và tên
    password_hash VARCHAR(255) NOT NULL, -- mật khẩu
    phone_number VARCHAR(20), -- số điện thoại
    address TEXT, -- địa chỉ
    date_of_birth DATE, -- ngày tháng năm sinh
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES Doctors(doctor_id) ON DELETE SET NULL,
    FOREIGN KEY (manager_id) REFERENCES Managers(manager_id) ON DELETE SET NULL,
    FOREIGN KEY (device_id) REFERENCES Devices(device_id) ON DELETE SET NULL
);

-- Bảng Dữ liệu Sức khỏe (HealthData)
CREATE TABLE HealthData (
    data_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    bpm FLOAT, -- nhịp tim hiện tại
    avg_bpm FLOAT, -- nhịp tim trung bình
    ir_value FLOAT, -- giá trị hồng ngoại
    accel_x FLOAT, -- gia tốc trục X
    accel_y FLOAT, -- gia tốc trục Y
    accel_z FLOAT, -- gia tốc trục Z
    a_total FLOAT, -- độ lớn gia tốc tổng hợp
    FOREIGN KEY (patient_id) REFERENCES Patients(patient_id) ON DELETE CASCADE,
    INDEX idx_patient_timestamp (patient_id, timestamp)
);

-- Bảng Cảnh báo (Alerts)
CREATE TABLE Alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    related_data_id BIGINT,
    alert_type VARCHAR(100), -- loại cảnh báo
    message TEXT, -- nội dung chi tiết
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('new', 'viewed', 'handled') DEFAULT 'new', -- trạng thái cảnh báo
    viewed_by_doctor_id INT,
    viewed_at TIMESTAMP NULL,
    FOREIGN KEY (patient_id) REFERENCES Patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (related_data_id) REFERENCES HealthData(data_id) ON DELETE SET NULL,
    FOREIGN KEY (viewed_by_doctor_id) REFERENCES Doctors(doctor_id) ON DELETE SET NULL
);
