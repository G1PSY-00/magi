CREATE TABLE students (
  student_id INT AUTO_INCREMENT PRIMARY KEY,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50) NOT NULL,
  age INT,
  email VARCHAR(100) UNIQUE,
  city VARCHAR(50)
);
CREATE TABLE courses (
  course_id INT AUTO_INCREMENT PRIMARY KEY,
  course_name VARCHAR(80) NOT NULL,
  credits INT NOT NULL DEFAULT 3,
  department VARCHAR(40)
);
CREATE TABLE enrollments (
  enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  course_id INT NOT NULL,
  grade DECIMAL(5,2) NULL,
  enrolled_on DATE,
  FOREIGN KEY (student_id) REFERENCES students(student_id),
  FOREIGN KEY (course_id) REFERENCES courses(course_id)
);
INSERT INTO students (student_id, first_name, last_name, age, email, city) VALUES
 (1,'Maria','Santos',19,'maria.santos@example.com','Cebu'),
 (2,'Juan','Dela Cruz',18,'juan.delacruz@example.com','Naga'),
 (3,'Ana','Reyes',21,'ana.reyes@example.com','Manila'),
 (4,'Carlo','Garcia',17,'carlo.garcia@example.com','Cebu'),
 (5,'Liza','Mendoza',20,'liza.mendoza@example.com','Davao'),
 (6,'Pedro','Ramos',22,'pedro.ramos@example.com','Cebu'),
 (7,'Sofia','Cruz',18,'sofia.cruz@example.com','Naga'),
 (8,'Miguel','Torres',23,'miguel.torres@example.com','Manila'),
 (9,'Isabel','Flores',19,'isabel.flores@example.com','Davao'),
 (10,'Rafael','Aquino',20,'rafael.aquino@example.com','Cebu');
INSERT INTO courses (course_id, course_name, credits, department) VALUES
 (1,'Database Systems',3,'IT'),(2,'Programming 1',3,'IT'),(3,'Calculus',4,'Math'),
 (4,'Statistics',3,'Math'),(5,'Web Development',3,'IT'),(6,'Technical Writing',2,'English');
INSERT INTO enrollments (enrollment_id, student_id, course_id, grade, enrolled_on) VALUES
 (1,1,1,92.50,'2026-01-10'),(2,1,2,88.00,'2026-01-10'),(3,2,1,75.00,'2026-01-11'),
 (4,2,5,81.50,'2026-01-11'),(5,3,3,95.00,'2026-01-12'),(6,3,4,89.00,'2026-01-12'),
 (7,4,2,70.00,'2026-01-13'),(8,5,1,85.00,'2026-01-13'),(9,5,5,90.00,'2026-01-14'),
 (10,6,3,78.00,'2026-01-14'),(11,7,2,NULL,'2026-01-15'),(12,7,5,84.00,'2026-01-15'),
 (13,6,4,80.00,'2026-01-16'),(14,9,1,88.50,'2026-01-16'),(15,9,2,93.00,'2026-01-17'),
 (16,1,5,90.00,'2026-01-17');
