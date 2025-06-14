-If first time run this project, please create database and user first, not recommend to change any statement below as its already configured same as in settings.py

-- Connect to MySQL as root or a user with CREATE DATABASE privileges
CREATE DATABASE renthouse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create a user (if not already existing) and grant privileges
CREATE USER 'django_user'@'localhost' IDENTIFIED BY '123';
GRANT ALL PRIVILEGES ON renthouse.* TO 'django_user'@'localhost';
FLUSH PRIVILEGES;

-run this migration to create table inside database

python manage.py migrate

-create a superuser if want to access admin dashboard

python manage.py createsuperuser

STEPS TO IMPORT DATA USING MYSQL WORKBENCH

-OPEN MYSQL WORKBENCH
-LOGIN USING USERS 
-SELECT ADMINISTRATION>DATA IMPORT
-INSIDE IMPORT OPTIONS CHOOSE IMPORT FROM SELF-CONTAINED FILE
-select default target schema to renthouse
-scroll down then click start import