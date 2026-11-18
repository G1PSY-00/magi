CREATE TABLE departments (
  dept_id INT AUTO_INCREMENT PRIMARY KEY,
  dept_name VARCHAR(50) NOT NULL,
  location VARCHAR(50)
);
CREATE TABLE employees (
  emp_id INT AUTO_INCREMENT PRIMARY KEY,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50) NOT NULL,
  dept_id INT,
  manager_id INT NULL,
  job_title VARCHAR(60),
  salary DECIMAL(10,2) NOT NULL,
  hire_date DATE,
  FOREIGN KEY (dept_id) REFERENCES departments(dept_id),
  FOREIGN KEY (manager_id) REFERENCES employees(emp_id)
);
INSERT INTO departments VALUES (1,'Engineering','Cebu'),(2,'Sales','Manila'),(3,'HR','Cebu'),(4,'Research','Davao');
INSERT INTO employees (emp_id, first_name, last_name, dept_id, manager_id, job_title, salary, hire_date) VALUES
 (1,'Elena','Vargas',1,NULL,'CTO',150000,'2015-03-01'),
 (2,'Marco','Lim',1,1,'Senior Developer',95000,'2017-06-15'),
 (3,'Grace','Tan',1,2,'Developer',70000,'2020-01-10'),
 (4,'Paolo','Uy',1,2,'Developer',68000,'2021-09-01'),
 (5,'Nina','Cortez',2,1,'Sales Manager',85000,'2016-11-20'),
 (6,'Dante','Silva',2,5,'Sales Rep',45000,'2022-02-14'),
 (7,'Rhea','Bautista',2,5,'Sales Rep',47000,'2021-07-05'),
 (8,'Oscar','Navarro',3,1,'HR Manager',72000,'2018-04-23'),
 (9,'Tessa','Go',3,8,'HR Assistant',38000,'2023-05-08'),
 (10,'Victor','Pineda',2,5,'Sales Rep',46000,'2023-01-16');
