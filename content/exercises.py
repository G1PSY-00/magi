"""Practice exercises and exam questions, plus one registry used by every part of the app."""
from content.lessons import LESSONS

TOPIC_CATEGORY = {
    "Basics": "Fundamentals", "SELECT": "Fundamentals", "WHERE": "Fundamentals", "ORDER BY": "Fundamentals",
    "INSERT": "Fundamentals", "UPDATE": "Fundamentals", "DELETE": "Fundamentals",
    "Aggregates": "Intermediate", "GROUP BY": "Intermediate", "Constraints": "Intermediate", "Keys": "Intermediate",
    "JOIN": "Advanced", "Subqueries": "Advanced", "CTE": "Advanced", "Window Functions": "Advanced",
    "Transactions": "Advanced", "ACID": "Advanced", "Indexes": "Advanced", "Projects": "Real-World Projects",
}
TOPIC_LESSON = {"Keys": "constraints", "ACID": "transactions", "Indexes": "constraints", "CTE": "cte-window",
                "DELETE": "update-delete", "Projects": "project-student-db"}
for _l in LESSONS:
    TOPIC_LESSON.setdefault(_l["topic"], _l["slug"])


def ex(id, topic, level, scenario, prompt, solution, hints=(), expl="", kind="select", check=None, challenge=False):
    return dict(id=id, type="challenge" if challenge else "query", topic=topic, level=level, scenario=scenario,
                prompt=prompt, solution=solution, kind=kind, check=check, hints=list(hints), explanation=expl)


EXERCISES = [
 ex("P01", "SELECT", 1, "school", "Display all students.", "SELECT * FROM students", ["SELECT * FROM table"], "* selects all columns."),
 ex("P02", "SELECT", 1, "school", "Show first_name and last_name of every student.", "SELECT first_name, last_name FROM students", ["List two columns separated by a comma."], "Only the requested columns are selected."),
 ex("P03", "SELECT", 1, "school", "List each city only once (no duplicates).", "SELECT DISTINCT city FROM students", ["DISTINCT removes repeats."], "DISTINCT collapses duplicate rows."),
 ex("P04", "WHERE", 1, "school", "Find students older than 18. Return first_name and age.", "SELECT first_name, age FROM students WHERE age > 18", ["Use WHERE age > 18"], "WHERE keeps only rows where the condition is true."),
 ex("P05", "WHERE", 2, "school", "Find students from Cebu who are 20 or older. Return first_name and last_name.", "SELECT first_name, last_name FROM students WHERE city = 'Cebu' AND age >= 20", ["Combine two conditions with AND.", "Text needs quotes."], "Both conditions must be true."),
 ex("P06", "ORDER BY", 1, "school", "List students alphabetically by last_name. Return last_name and first_name.", "SELECT last_name, first_name FROM students ORDER BY last_name", ["ORDER BY last_name"], "ORDER BY sorts ascending by default."),
 ex("P07", "Aggregates", 2, "school", "Count the total number of students.", "SELECT COUNT(*) FROM students", ["COUNT(*)"], "COUNT(*) counts rows."),
 ex("P08", "Aggregates", 2, "school", "Find the average grade across all enrollments (do not round).", "SELECT AVG(grade) FROM enrollments", ["AVG(column)"], "AVG ignores NULL grades."),
 ex("P09", "GROUP BY", 2, "school", "Count students per city. Return city and the count.", "SELECT city, COUNT(*) FROM students GROUP BY city", ["GROUP BY city"], "One row per city with its count."),
 ex("P10", "GROUP BY", 3, "school", "Return course_id for courses with more than 3 enrollments.", "SELECT course_id FROM enrollments GROUP BY course_id HAVING COUNT(*) > 3", ["Group by course_id, then HAVING."], "HAVING filters groups after counting."),
 ex("P11", "JOIN", 3, "school", "Return each student's first_name with each course_name they are enrolled in.", "SELECT s.first_name, c.course_name FROM students s JOIN enrollments e ON s.student_id=e.student_id JOIN courses c ON c.course_id=e.course_id", ["Three tables, two ON conditions."], "enrollments links students to courses."),
 ex("P12", "JOIN", 3, "school", "Find students with no enrollment record. Return first_name and last_name.", "SELECT s.first_name, s.last_name FROM students s LEFT JOIN enrollments e ON s.student_id=e.student_id WHERE e.student_id IS NULL", ["LEFT JOIN then IS NULL.", "NOT EXISTS also works."], "Unmatched left rows have NULL on the right."),
 ex("P13", "GROUP BY", 4, "school", "For each course show course_name and its average grade, only courses averaging above 85 (do not round).", "SELECT c.course_name, AVG(e.grade) FROM courses c JOIN enrollments e ON e.course_id=c.course_id GROUP BY c.course_id, c.course_name HAVING AVG(e.grade) > 85", ["JOIN, GROUP BY, HAVING."], "HAVING filters the averages.", challenge=True),
 ex("P14", "Window Functions", 5, "school", "Return student_id, course_id, grade and the RANK() of the grade within each course, highest grade first.", "SELECT student_id, course_id, grade, RANK() OVER (PARTITION BY course_id ORDER BY grade DESC) FROM enrollments", ["RANK() OVER (PARTITION BY ... ORDER BY ...)"], "PARTITION BY restarts the ranking per course.", challenge=True),
 ex("P15", "INSERT", 1, "school", "Insert a student: Lara Navarro, age 20, email lara.navarro@example.com, city Cebu.", "INSERT INTO students (first_name,last_name,age,email,city) VALUES ('Lara','Navarro',20,'lara.navarro@example.com','Cebu')", ["INSERT INTO table (cols) VALUES (...)"], "The table state is compared.", kind="dml", check="SELECT first_name,last_name,age,email,city FROM students ORDER BY email"),
 ex("P16", "UPDATE", 1, "school", "Change the city of student_id 4 to 'Naga'.", "UPDATE students SET city='Naga' WHERE student_id=4", ["Do not forget WHERE."], "Only one row changes.", kind="dml", check="SELECT student_id, city FROM students ORDER BY student_id"),
 ex("P17", "DELETE", 1, "school", "Delete the enrollment with enrollment_id 7.", "DELETE FROM enrollments WHERE enrollment_id=7", ["DELETE FROM table WHERE ..."], "WHERE limits the delete to one row.", kind="dml", check="SELECT enrollment_id FROM enrollments ORDER BY enrollment_id"),
 ex("P18", "WHERE", 1, "employees", "Show first_name and salary of employees earning more than 70000.", "SELECT first_name, salary FROM employees WHERE salary > 70000", ["WHERE salary > 70000"], "Numbers need no quotes."),
 ex("P19", "JOIN", 3, "employees", "Show dept_name and the number of employees in each department, including departments with none.", "SELECT d.dept_name, COUNT(e.emp_id) FROM departments d LEFT JOIN employees e ON e.dept_id=d.dept_id GROUP BY d.dept_id, d.dept_name", ["LEFT JOIN from departments.", "COUNT(e.emp_id), not COUNT(*)."], "COUNT of a right-side column ignores NULL, so Research shows 0."),
 ex("P20", "JOIN", 4, "employees", "Show each employee's first_name and their manager's first_name. Employees without a manager must still appear.", "SELECT e.first_name, m.first_name FROM employees e LEFT JOIN employees m ON e.manager_id=m.emp_id", ["Join the table to itself with two aliases."], "A self join treats one table as two roles.", challenge=True),
 ex("P21", "Subqueries", 3, "employees", "Show first_name of employees earning more than the company average salary.", "SELECT first_name FROM employees WHERE salary > (SELECT AVG(salary) FROM employees)", ["Put SELECT AVG(salary) in parentheses."], "The inner query returns one value."),
 ex("P22", "UPDATE", 3, "employees", "Give all Sales Reps (job_title = 'Sales Rep') a 10% raise.", "UPDATE employees SET salary = salary * 1.10 WHERE job_title='Sales Rep'", ["SET salary = salary * 1.10"], "The state of salaries is compared.", kind="dml", check="SELECT emp_id, ROUND(salary,2) FROM employees ORDER BY emp_id"),
 ex("P23", "WHERE", 1, "ecommerce", "List products costing less than 20, cheapest first. Return name and price.", "SELECT name, price FROM products WHERE price < 20 ORDER BY price", ["WHERE then ORDER BY."], "Filter first, sort second."),
 ex("P24", "JOIN", 3, "ecommerce", "Return each product name with the total quantity sold.", "SELECT p.name, SUM(oi.quantity) FROM products p JOIN order_items oi ON oi.product_id=p.product_id GROUP BY p.product_id, p.name", ["JOIN, SUM, GROUP BY."], "Products never sold are excluded by the inner join."),
 ex("P25", "Subqueries", 3, "ecommerce", "Return names of customers who never placed an order.", "SELECT name FROM customers WHERE customer_id NOT IN (SELECT customer_id FROM orders)", ["NOT IN (subquery), LEFT JOIN or NOT EXISTS all work."], "Customers without matching orders are returned."),
 ex("P26", "CTE", 5, "ecommerce", "Using a CTE, return name and total spending (quantity * price) of customers whose spending on non-cancelled orders exceeds 100.", "WITH spend AS (SELECT o.customer_id, SUM(oi.quantity*p.price) AS total FROM orders o JOIN order_items oi ON oi.order_id=o.order_id JOIN products p ON p.product_id=oi.product_id WHERE o.status <> 'cancelled' GROUP BY o.customer_id) SELECT c.name, s.total FROM customers c JOIN spend s ON s.customer_id=c.customer_id WHERE s.total > 100", ["WITH spend AS ( ... ) SELECT ... FROM spend"], "The CTE names the per-customer totals first.", challenge=True),
 ex("P27", "JOIN", 4, "ecommerce", "Return the total revenue (quantity * price) of orders with status 'delivered'.", "SELECT SUM(oi.quantity*p.price) FROM orders o JOIN order_items oi ON oi.order_id=o.order_id JOIN products p ON p.product_id=oi.product_id WHERE o.status='delivered'", ["Three tables."], "SUM over the joined rows.", challenge=True),
 ex("P28", "Aggregates", 2, "ecommerce", "Count the products that are out of stock (stock = 0).", "SELECT COUNT(*) FROM products WHERE stock = 0", ["COUNT(*) with WHERE."], "WHERE runs before COUNT."),
]


def mcq(id, topic, level, prompt, options, answer, expl, query=None, type="mcq"):
    return dict(id=id, type=type, topic=topic, level=level, prompt=prompt, query=query, options=options, answer=answer, explanation=expl)


QUESTIONS = [
 mcq("M01", "SELECT", 1, "Which clause names the table you read from?", ["WHERE", "FROM", "ORDER BY", "LIMIT"], 1, "FROM names the table."),
 mcq("M02", "WHERE", 1, "Which test finds rows whose grade is missing?", ["grade = NULL", "grade IS NULL", "grade = ''", "grade == 0"], 1, "NULL needs IS NULL."),
 mcq("M03", "Keys", 2, "What does a PRIMARY KEY guarantee?", ["Unique, non-NULL values", "Sorted rows", "Faster INSERTs", "Encrypted data"], 0, "It uniquely identifies each row."),
 mcq("M04", "Keys", 2, "What does a FOREIGN KEY enforce?", ["Column order", "Matching rows exist in the referenced table", "Unique text", "Faster joins automatically"], 1, "Referential integrity."),
 mcq("M05", "JOIN", 3, "Which JOIN keeps all rows of the left table even without a match?", ["INNER JOIN", "LEFT JOIN", "CROSS JOIN", "SELF JOIN"], 1, "LEFT JOIN keeps unmatched left rows."),
 mcq("M06", "GROUP BY", 2, "Which clause filters groups after aggregation?", ["WHERE", "HAVING", "ORDER BY", "DISTINCT"], 1, "HAVING filters aggregated groups."),
 mcq("M07", "ORDER BY", 1, "What is the default sort direction of ORDER BY?", ["ASC", "DESC", "Random", "By primary key"], 0, "ASC is the default."),
 mcq("M08", "Transactions", 3, "Which statement undoes uncommitted changes?", ["COMMIT", "ROLLBACK", "SAVE", "UNDO"], 1, "ROLLBACK cancels the transaction."),
 mcq("M09", "Constraints", 2, "What does AUTO_INCREMENT do?", ["Sorts a column", "Generates the next number automatically", "Makes a column optional", "Duplicates rows"], 1, "MySQL supplies the next integer."),
 mcq("M10", "Subqueries", 3, "A correlated subquery...", ["Runs once before everything", "References the outer query and re-runs per row", "Cannot use WHERE", "Only works with UNION"], 1, "It depends on the outer row."),
 mcq("M11", "ACID", 3, "What does the A in ACID stand for?", ["Accuracy", "Atomicity", "Availability", "Aggregation"], 1, "Atomicity: all or nothing."),
 mcq("M12", "Indexes", 3, "What is the main benefit of an index?", ["Faster lookups on indexed columns", "Less disk space", "Automatic backups", "Stronger passwords"], 0, "Indexes speed up searches, at a small cost on writes."),
 mcq("M13", "WHERE", 2, "Which pattern matches names starting with A?", ["LIKE '%A'", "LIKE 'A%'", "= 'A*'", "LIKE '_A'"], 1, "% means any characters after A."),
 mcq("M14", "Window Functions", 4, "Which function gives tied rows the same rank and leaves gaps afterwards?", ["ROW_NUMBER()", "RANK()", "DENSE_RANK()", "NTILE()"], 1, "RANK leaves gaps; DENSE_RANK does not."),
 mcq("O01", "WHERE", 1, "What does this query return?", ["3", "4", "5", "10"], 1, "Students from Cebu: Maria, Carlo, Pedro, Rafael = 4.", "SELECT COUNT(*) FROM students WHERE city = 'Cebu';", "predict"),
 mcq("O02", "WHERE", 2, "What does this query return?", ["4", "5", "6", "8"], 2, "Ages 18, 19 and 20 appear 6 times.", "SELECT COUNT(*) FROM students WHERE age BETWEEN 18 AND 20;", "predict"),
 mcq("O03", "SELECT", 2, "What does this query return?", ["3", "4", "10", "5"], 1, "Cebu, Naga, Manila and Davao are 4 distinct cities.", "SELECT COUNT(DISTINCT city) FROM students;", "predict"),
 mcq("O04", "Aggregates", 2, "What does this query return?", ["22", "23", "21", "19"], 1, "The oldest student is 23.", "SELECT MAX(age) FROM students;", "predict"),
]
for _q in QUESTIONS:
    if _q["type"] == "predict":
        _q["scenario"] = "school"


def dbg(id, topic, level, broken, solution, expl, hints):
    return dict(id=id, type="debug", topic=topic, level=level, scenario="school", prompt="This query is broken. Fix it so it does what the comment says.",
                query=broken, solution=solution, kind="select", check=None, hints=hints, explanation=expl)


DEBUG = [
 dbg("D01", "SELECT", 1, "-- show first names\nSELCT first_name FROM students;", "SELECT first_name FROM students", "SELECT was misspelled.", ["Check keyword spelling."]),
 dbg("D02", "WHERE", 1, "-- students from Cebu\nSELECT * FROM students WHERE city = Cebu;", "SELECT * FROM students WHERE city = 'Cebu'", "Text values need single quotes.", ["Text needs quotes."]),
 dbg("D03", "GROUP BY", 2, "-- students per city\nSELECT city, COUNT(*) FROM students;", "SELECT city, COUNT(*) FROM students GROUP BY city", "A plain column next to an aggregate needs GROUP BY.", ["Add GROUP BY."]),
 dbg("D04", "WHERE", 2, "-- enrollments without a grade\nSELECT * FROM enrollments WHERE grade = NULL;", "SELECT * FROM enrollments WHERE grade IS NULL", "= NULL is never true; use IS NULL.", ["How do you test NULL?"]),
]

REGISTRY = {}
for _e in EXERCISES + DEBUG:
    REGISTRY[_e["id"]] = _e
for _q in QUESTIONS:
    REGISTRY[_q["id"]] = _q
for _l in LESSONS:
    REGISTRY[_l["exercise"]["id"]] = dict(_l["exercise"], type="lesson", lesson=_l["slug"])

ALL_TOPICS = sorted({q["topic"] for q in REGISTRY.values() if not q["id"].startswith("L:")}, key=lambda t: (list(TOPIC_CATEGORY).index(t) if t in TOPIC_CATEGORY else 99))
SECRET_KEYS = ("solution", "answer", "explanation", "check")


def public(q):
    """Question as sent to the browser: no solutions or answers."""
    return {k: v for k, v in q.items() if k not in SECRET_KEYS and k != "hints"} | {"hint_count": len(q.get("hints", []))}
