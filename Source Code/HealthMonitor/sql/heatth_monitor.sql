-- ============================
-- DATABASE: health_monitor
-- ============================

CREATE DATABASE IF NOT EXISTS health_monitor;
USE health_monitor;

-- ============================
-- BẢNG QUẢN LÝ (Managers)
-- ============================
CREATE TABLE Managers (
    manager_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    address TEXT,
    date_of_birth DATE,
    title VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================
-- BẢNG BÁC SĨ (Doctors)
-- Mỗi bác sĩ có thể được quản lý bởi 1 quản lý
-- ============================
CREATE TABLE Doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    manager_id INT, -- liên kết đến quản lý
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    address TEXT,
    date_of_birth DATE,
    title VARCHAR(100),
    specialty VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES Managers(manager_id) ON DELETE SET NULL
);

-- ============================
-- BẢNG THIẾT BỊ (Devices)
-- ============================
CREATE TABLE Devices (
    device_id INT AUTO_INCREMENT PRIMARY KEY,
    device_serial VARCHAR(100) NOT NULL UNIQUE,
    status ENUM('online', 'offline', 'error') DEFAULT 'offline',
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================
-- BẢNG BỆNH NHÂN (Patients)
-- Mỗi bệnh nhân có thể được theo dõi bởi 1 bác sĩ
-- và thuộc quyền quản lý của 1 quản lý
-- ============================
CREATE TABLE Patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id INT,
    manager_id INT, -- liên kết đến quản lý
    device_id INT UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    email VARCHAR(255) NOT NULL UNIQUE,
    address TEXT,
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES Doctors(doctor_id) ON DELETE SET NULL,
    FOREIGN KEY (manager_id) REFERENCES Managers(manager_id) ON DELETE SET NULL,
    FOREIGN KEY (device_id) REFERENCES Devices(device_id) ON DELETE SET NULL
);

-- ============================
-- BẢNG DỮ LIỆU SỨC KHỎE (HealthData)
-- ============================
CREATE TABLE HealthData (
    data_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    bpm FLOAT,
    avg_bpm FLOAT,
    ir_value FLOAT,
    accel_x FLOAT,
    accel_y FLOAT,
    accel_z FLOAT,
    a_total FLOAT,
    FOREIGN KEY (patient_id) REFERENCES Patients(patient_id) ON DELETE CASCADE,
    INDEX idx_patient_timestamp (patient_id, timestamp)
);

-- ============================
-- BẢNG CẢNH BÁO (Alerts)
-- ============================
CREATE TABLE Alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    related_data_id BIGINT,
    alert_type VARCHAR(100),
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('new', 'viewed', 'handled') DEFAULT 'new',
    viewed_by_doctor_id INT,
    viewed_at TIMESTAMP NULL,
    FOREIGN KEY (patient_id) REFERENCES Patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (related_data_id) REFERENCES HealthData(data_id) ON DELETE SET NULL,
    FOREIGN KEY (viewed_by_doctor_id) REFERENCES Doctors(doctor_id) ON DELETE SET NULL
);
