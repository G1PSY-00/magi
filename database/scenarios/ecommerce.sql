CREATE TABLE customers (
  customer_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL,
  email VARCHAR(100) UNIQUE,
  country VARCHAR(40)
);
CREATE TABLE products (
  product_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL,
  category VARCHAR(40),
  price DECIMAL(8,2) NOT NULL,
  stock INT NOT NULL DEFAULT 0
);
CREATE TABLE orders (
  order_id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  order_date DATE NOT NULL,
  status VARCHAR(20) NOT NULL,
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
CREATE TABLE order_items (
  item_id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL,
  FOREIGN KEY (order_id) REFERENCES orders(order_id),
  FOREIGN KEY (product_id) REFERENCES products(product_id)
);
INSERT INTO customers VALUES
 (1,'Alice Cruz','alice@example.com','Philippines'),(2,'Ben Park','ben@example.com','Korea'),
 (3,'Chloe Tan','chloe@example.com','Singapore'),(4,'Daniel Smith','daniel@example.com','USA'),
 (5,'Emi Sato','emi@example.com','Japan'),(6,'Farah Khan','farah@example.com','Philippines');
INSERT INTO products VALUES
 (1,'Wireless Mouse','Accessories',15.99,120),(2,'Mechanical Keyboard','Accessories',59.90,45),
 (3,'USB-C Hub','Accessories',29.50,80),(4,'Laptop Stand','Office',24.00,60),
 (5,'Monitor 24in','Electronics',149.99,25),(6,'Webcam HD','Electronics',39.99,0),
 (7,'Desk Lamp','Office',19.95,70),(8,'Notebook Pack','Office',8.50,200);
INSERT INTO orders VALUES
 (1,1,'2026-01-05','delivered'),(2,2,'2026-01-12','delivered'),(3,1,'2026-02-03','shipped'),
 (4,3,'2026-02-14','delivered'),(5,4,'2026-03-01','cancelled'),(6,5,'2026-03-09','pending'),
 (7,2,'2026-03-20','delivered'),(8,3,'2026-04-02','shipped');
INSERT INTO order_items VALUES
 (1,1,1,2),(2,1,2,1),(3,2,5,1),(4,3,3,3),(5,3,8,5),(6,4,4,2),(7,4,7,1),
 (8,5,6,1),(9,6,2,1),(10,6,1,1),(11,7,8,10),(12,8,5,1),(13,8,3,2);
