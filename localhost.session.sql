
GRANT ALL PRIVILEGES ON renthouse.* TO 'django_user'@'localhost'; -- Adjust user and host if different

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password VARCHAR(256) NOT NULL,
    full_name VARCHAR(100),
    phone_number VARCHAR(20),
    course VARCHAR(100),        -- for students, can be NULL for tenants
    role ENUM('student', 'tenant', 'admin') DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

CREATE TABLE properties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    house_type VARCHAR(100),
    rent DECIMAL(10,2),
    course VARCHAR(100), -- optional, for course-specific rentals
    address TEXT,
    owner_id INT,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    number_of_rooms INT DEFAULT 1,
    main_image VARCHAR(255) DEFAULT 'https://a0.muscache.com/im/pictures/hosting/Hosting-1278133431787824396/original/ead7f016-e6b4-43b9-a8dd-90149cf93893.jpeg?im_w=960',
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

CREATE TABLE bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT,
    student_id INT,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    scheduled_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(id),
    FOREIGN KEY (student_id) REFERENCES users(id)
);

CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT,
    receiver_id INT,
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id)
);

CREATE TABLE amenities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

INSERT INTO amenities (name) VALUES
('Wifi'),
('TV'),
('Dedicated workspace'),
('Elevator'),
('Free parking on premises'),
('Washer'),
('Pool'),
('Air conditioning'),
('Shared sauna');

-- 5 Students
INSERT INTO users (username, email, password, full_name, phone_number, course, role) VALUES
('ali_student', 'ali.student@example.com', 'hashed_password_s1', 'Ali bin Ahmad', '012-3456789', 'Computer Science', 'student'),
('siti_learns', 'siti.learns@example.com', 'hashed_password_s2', 'Siti Nurhaliza', '011-2345678', 'Business Administration', 'student'),
('raj_studies', 'raj.studies@example.com', 'hashed_password_s3', 'Rajesh Kumar', '013-4567890', 'Mechanical Engineering', 'student'),
('maya_uni', 'maya.uni@example.com', 'hashed_password_s4', 'Maya Abdullah', '019-8765432', 'Mass Communication', 'student'),
('john_edu', 'john.edu@example.com', 'hashed_password_s5', 'John Tan', '016-7654321', 'Graphic Design', 'student');

-- 5 Tenants
INSERT INTO users (username, email, password, full_name, phone_number, course, role) VALUES
('tan_tenant', 'tan.tenant@example.com', 'hashed_password_t1', 'Tan Mei Ling', '017-1234567', NULL, 'tenant'),
('david_rent', 'david.rent@example.com', 'hashed_password_t2', 'David Lee', '010-9876543', NULL, 'tenant'),
('fatimah_home', 'fatimah.home@example.com', 'hashed_password_t3', 'Fatimah Binti Khalid', '014-5432109', NULL, 'tenant'),
('lim_residence', 'lim.residence@example.com', 'hashed_password_t4', 'Lim Chee Hong', '018-2109876', NULL, 'tenant'),
('suresh_place', 'suresh.place@example.com', 'hashed_password_t5', 'Suresh A/L Kumar', '019-3210987', NULL, 'tenant');

INSERT INTO properties (house_type, rent, course, address, owner_id, is_available) VALUES
('Condominium', 2500.00, NULL, 'Unit 12A, The Residences, Jalan Ampang, 50450 Kuala Lumpur', 6, TRUE),
('Apartment', 1800.00, 'Universiti Malaya', 'Block C, Pangsapuri Harmoni, Jalan Universiti, 59100 Kuala Lumpur', 6, TRUE),
('Terrace House', 3200.00, NULL, 'No. 7, Jalan SS2/10, SS2, 47300 Petaling Jaya, Selangor', 7, TRUE),
('Studio', 1200.00, 'Multimedia University (MMU)', 'Cyberia Smarthomes, Persiaran Apevia, 63000 Cyberjaya, Selangor', 7, TRUE),
('Semi-Detached', 4500.00, NULL, 'No. 22, Lorong Perdana 4, Bandar Tun Razak, 56000 Kuala Lumpur', 8, TRUE),
('Condominium', 3000.00, NULL, 'Penthouse B, Arte Mont Kiara, Jalan Sultan Haji Ahmad Shah, 50480 Kuala Lumpur', 8, TRUE),
('Apartment', 1600.00, 'UiTM Shah Alam', 'Vista Alam Serviced Apartment, Seksyen 14, 40000 Shah Alam, Selangor', 9, TRUE),
('Bungalow', 6000.00, NULL, 'Jalan Dato Abdullah Tahir, Century Garden, 80300 Johor Bahru, Johor', 9, FALSE), -- Example of unavailable property
('Condominium', 2800.00, NULL, 'Unit 8-5, Gurney Paragon, Persiaran Gurney, 10250 Georgetown, Penang', 10, TRUE),
('Terrace House', 2000.00, 'Universiti Teknologi Malaysia (UTM)', 'No. 15, Jalan Ilmu 2, Taman Universiti, 81300 Skudai, Johor Bahru, Johor', 10, TRUE);

-- Add 'last_login' column (can be NULL initially)
ALTER TABLE users
ADD COLUMN last_login DATETIME(6) NULL;

-- Add 'is_superuser' column (BOOLEAN, NOT NULL, default FALSE/0)
ALTER TABLE users
ADD COLUMN is_superuser BOOLEAN NOT NULL DEFAULT 0;

-- Add 'is_staff' column (BOOLEAN, NOT NULL, default FALSE/0)
ALTER TABLE users
ADD COLUMN is_staff BOOLEAN NOT NULL DEFAULT 0;

-- Add 'is_active' column (BOOLEAN, NOT NULL, default TRUE/1)
ALTER TABLE users
ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1;