# SQL — Complete Interview Prep Guide
> Explained clearly for someone who uses SQL daily — covers basics through advanced
> 4 years experience level: you should know all of this

---

## 1. How a SQL Query Runs — The Order That Matters

When you write a SQL query, you type things in a specific order — SELECT first, then FROM, then WHERE, and so on. But the database does NOT execute your query in the order you wrote it. It follows its own internal execution order. Understanding this order is the single most important thing for avoiding bugs and writing correct queries.

Think of it like cooking a recipe. You might read the recipe title first ("Pasta"), but you don't start with the title — you start by gathering ingredients (FROM), then filtering out the bad ones (WHERE), then grouping them (GROUP BY), and only at the end do you plate it nicely (SELECT, ORDER BY).

**You write:**
```sql
SELECT department, COUNT(*) AS emp_count
FROM employees
WHERE salary > 50000
GROUP BY department
HAVING COUNT(*) > 5
ORDER BY emp_count DESC
LIMIT 10;
```

**Database executes in this order:**
```
1. FROM       -- pick the table
2. JOIN       -- combine tables
3. WHERE      -- filter rows
4. GROUP BY   -- group remaining rows
5. HAVING     -- filter groups
6. SELECT     -- pick columns and compute expressions
7. DISTINCT   -- remove duplicate rows
8. ORDER BY   -- sort
9. LIMIT      -- cut off
```

**Why this matters in practice:**

The most common mistake is trying to use a column alias (that you created in SELECT) inside a WHERE clause. This fails because WHERE runs at step 3, but the alias isn't created until step 6 (SELECT). The database doesn't know what "annual" means yet when it's filtering rows.

```sql
-- FAILS:
SELECT salary * 12 AS annual FROM employees WHERE annual > 600000;
-- "annual" doesn't exist yet at step 3 (WHERE runs before SELECT)

-- FIX:
SELECT salary * 12 AS annual FROM employees WHERE salary * 12 > 600000;
```

However, you CAN use aliases in ORDER BY because ORDER BY runs at step 8, which is after SELECT (step 6). By that point, the alias has already been created.

Another consequence: you can't use window functions in WHERE either — window functions are computed during the SELECT phase, so they don't exist when WHERE is filtering. If you need to filter on a window function result, you must wrap the query in a CTE or subquery and filter in the outer query.

This execution order also explains why HAVING exists separately from WHERE. WHERE filters individual rows before grouping. HAVING filters entire groups after GROUP BY has collapsed rows into groups. You need both because they operate at different stages of the pipeline.

---

## 2. JOINs — All Types With Examples

JOINs are how you combine data from two or more tables. In a well-designed database, information is split across multiple tables (normalization), so JOINs are how you bring that information back together. Almost every real-world query involves at least one JOIN.

The key to understanding JOINs is the ON condition — it tells the database which rows from table A match which rows from table B. Different JOIN types control what happens when a row from one side has no match on the other side.

### Setup — Two Tables

```
employees:                    departments:
| id | name   | dept_id |    | id | dept_name   |
|----|--------|---------|    |----|-------------|
| 1  | Vishal | 10      |    | 10 | Engineering |
| 2  | Raj    | 20      |    | 20 | Marketing   |
| 3  | Priya  | 30      |    | 40 | Finance     |
| 4  | Amit   | NULL    |
```

Notice the deliberate mismatches here — they're what make JOIN examples educational. Priya has dept_id=30, but no department with id=30 exists. Amit has a NULL dept_id (he hasn't been assigned to any department yet). And the Finance department (id=40) exists but has no employees. Each JOIN type handles these mismatches differently.

### INNER JOIN — Only Matching Rows

INNER JOIN is the most common and the strictest type. It only returns rows where the ON condition finds a match on BOTH sides. If a row from either table has no matching partner, that row is completely excluded from the result. Think of it as the intersection of two sets.

```sql
SELECT e.name, d.dept_name
FROM employees e
INNER JOIN departments d ON e.dept_id = d.id;
```
```
| name   | dept_name   |
|--------|-------------|
| Vishal | Engineering |
| Raj    | Marketing   |
```

Priya (dept_id=30, no matching department) is excluded because there's no department with id=30. Amit (dept_id=NULL) is excluded because NULL never equals anything — not even another NULL. Finance (id=40) is excluded because no employee has dept_id=40. Only Vishal and Raj have valid matches on both sides.

**Use when:** You only want records that have valid matches on both sides. This is the right choice for most queries where you need complete information from both tables.

### LEFT JOIN — All Left, Matching Right

LEFT JOIN keeps EVERY row from the left table (the one written first, after FROM), regardless of whether it has a match in the right table. If a left-side row has no match, the right-side columns are filled with NULL. Think of it as "I definitely want all my employees — and if they happen to have a department, show me that too."

```sql
SELECT e.name, d.dept_name
FROM employees e
LEFT JOIN departments d ON e.dept_id = d.id;
```
```
| name   | dept_name   |
|--------|-------------|
| Vishal | Engineering |
| Raj    | Marketing   |
| Priya  | NULL        |  <-- kept even with no match
| Amit   | NULL        |  <-- kept even with no match
```

All four employees appear. Vishal and Raj get their department names. Priya and Amit get NULL for dept_name because their dept_ids don't match any department. Finance still doesn't appear because LEFT JOIN protects the LEFT table (employees), not the right one.

**Use when:** "Show me all employees, and their department if they have one." This is the second most common JOIN type. It's especially useful when the right-side relationship is optional — not every employee must have a department.

A very common pattern is using LEFT JOIN to find records with NO match:
```sql
SELECT e.name FROM employees e
LEFT JOIN departments d ON e.dept_id = d.id
WHERE d.id IS NULL;
-- Returns Priya and Amit -- employees without valid departments
```

### RIGHT JOIN — All Right, Matching Left

RIGHT JOIN is the mirror image of LEFT JOIN. It keeps every row from the right table and fills in NULLs for unmatched left-side rows. All departments would appear, even Finance (with NULL for employee columns).

In practice, most developers simply swap the table order and use LEFT JOIN instead of RIGHT JOIN. It's easier to always think "my main table is on the left" rather than switching between left and right mentally. So you'll rarely see RIGHT JOIN in real code.

### FULL OUTER JOIN — Everything

FULL OUTER JOIN keeps ALL rows from BOTH tables. If a row from either side has no match, the other side's columns are filled with NULL. It's the union of LEFT JOIN and RIGHT JOIN.

```sql
SELECT e.name, d.dept_name
FROM employees e
FULL OUTER JOIN departments d ON e.dept_id = d.id;
```

This returns all employees (including unmatched Priya and Amit with NULL department) AND all departments (including Finance with NULL employee name). Every row from both tables is represented at least once.

**Use when:** You need a complete reconciliation view — for example, comparing data between two systems to find records that exist in one but not the other. This is common in data engineering and auditing.

Note: MySQL does not support FULL OUTER JOIN directly — you'd need to UNION a LEFT JOIN and a RIGHT JOIN.

### CROSS JOIN — Every Combination

CROSS JOIN produces the Cartesian product: every row from table A paired with every row from table B. If table A has 100 rows and table B has 3 rows, you get 300 rows. There's no ON condition because you're not matching — you're combining everything.

```sql
SELECT e.name, s.shift_name
FROM employees e CROSS JOIN shifts s;
```
100 employees x 3 shifts = 300 rows. No ON condition.

**Use when:** You need to generate all possible combinations. For example, pairing every product with every store to find which products are missing from which stores. Or generating a calendar (CROSS JOIN months with years). It's rarely used in normal queries but very useful in reporting and test data generation.

### Self JOIN — Table Joined With Itself

A self JOIN is when you join a table to itself. This happens when a table has a hierarchical or self-referential relationship — the most common example is an employee table where each employee has a manager_id that references another employee's id in the same table.

```sql
-- Find employees and their managers (both in same table)
SELECT e.name AS employee, m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;
```

You're treating the same physical table as two virtual tables by giving them different aliases (e and m). The first alias (e) represents employees, the second (m) represents managers. The ON condition links each employee to their manager row.

**Harder variant:** "Find employees who earn more than their manager."
```sql
SELECT e.name, e.salary, m.name AS manager, m.salary AS mgr_salary
FROM employees e
JOIN employees m ON e.manager_id = m.id
WHERE e.salary > m.salary;
```

This is one of the most frequently asked SQL interview questions. The trick is recognizing that you need a self JOIN and that e and m are just two views of the same table.

### How JOINs Actually Execute (Under the Hood)

Understanding how the database physically performs JOINs helps you understand why indexing matters and why some queries are slow.

**Nested Loop:** The simplest algorithm. For each row in table A, it scans ALL rows in table B looking for matches. This is O(n*m) — if both tables have 1 million rows, that's 1 trillion comparisons. Very slow for large tables, but fine when one table is tiny (say, 10 departments JOIN against 10,000 employees — only 100,000 comparisons).

**Hash Join:** The database builds a hash table from the smaller table (load all its join-key values into a hash map). Then it scans the larger table, and for each row, does a hash lookup to find matches. This is much faster than nested loop for large tables with equality conditions. It's O(n+m) — each table is scanned once.

**Sort-Merge Join:** Both tables are sorted by the join key, then they're merged together like a zipper. The database walks through both sorted lists simultaneously, matching as it goes. This is efficient when both sides are already sorted (by an index) or when the data is very large and the database can sort it efficiently.

You don't choose the algorithm — the query optimizer does. But understanding this helps you know why putting an index on the join column matters (it makes sort-merge possible and can speed up nested loop dramatically).

### Interview Tip: "What JOIN for X?"

- "Show all orders with customer info" = INNER JOIN (you only want orders that have a customer)
- "Show all customers, even those with no orders" = LEFT JOIN (you want every customer regardless)
- "Find customers who never ordered" = LEFT JOIN + WHERE right side IS NULL (find the gaps)
- "Find unmatched records from both sides" = FULL OUTER JOIN (reconciliation/audit)

---

## 3. GROUP BY and Aggregations

GROUP BY is one of SQL's most powerful features. It takes a set of rows and collapses them into groups based on one or more columns. Within each group, aggregate functions (COUNT, SUM, AVG, etc.) compute a single summary value.

Think of it like sorting papers into piles. If you GROUP BY department, you're putting all Engineering employees in one pile, all Marketing employees in another pile. Then you can count how many papers are in each pile (COUNT), or find the average value written on each pile's papers (AVG).

### The Basics

```sql
SELECT department, COUNT(*) AS headcount, AVG(salary) AS avg_salary
FROM employees
GROUP BY department;
```

If there are 5 distinct departments, you get exactly 5 output rows — one per group. Each row summarizes all the employees in that department.

**The Golden Rule:** Every column in your SELECT must either be listed in GROUP BY or wrapped inside an aggregate function. This is because GROUP BY collapses many rows into one, so the database needs to know how to represent each column. A column in GROUP BY keeps its value (it's the same for all rows in the group by definition). A column in an aggregate gets computed (like COUNT or AVG). But a column that's neither? The database doesn't know which row's value to pick, so it's an error.

```sql
-- FAILS:
SELECT department, name, COUNT(*) FROM employees GROUP BY department;
-- Which "name" from the group? There are many employees per department. Ambiguous.
```

### WHERE vs HAVING — Two Filtering Stages

This distinction is fundamental and frequently asked in interviews. WHERE and HAVING both filter data, but they operate at different stages of query execution.

**WHERE** filters individual rows BEFORE grouping. It runs at step 3 in the execution order, before GROUP BY (step 4). It operates on raw row values and cannot use aggregate functions — because the groups haven't been formed yet, so there's nothing to aggregate.

**HAVING** filters groups AFTER grouping. It runs at step 5, after GROUP BY (step 4). It operates on grouped results and CAN use aggregate functions — because by this point, groups exist and aggregates have been computed.

```sql
SELECT department, COUNT(*) AS cnt
FROM employees
WHERE salary > 50000          -- gate 1: only keep high earners
GROUP BY department
HAVING COUNT(*) > 5;          -- gate 2: only keep big departments
```

In this query, WHERE first removes all employees earning 50K or less. Then GROUP BY groups the remaining employees by department. Then HAVING removes any department that has 5 or fewer remaining employees. The two filters work together but at different stages.

**Performance tip:** Always filter with WHERE when possible, not HAVING. WHERE reduces the number of rows before grouping, which means less work for the GROUP BY operation. Filtering 10 million rows down to 100K with WHERE, then grouping, is much faster than grouping all 10 million rows and then filtering groups with HAVING.

### Aggregate Functions — What Each One Does

Aggregate functions take a set of values (all values in a group) and return a single value. They are the whole reason GROUP BY exists.

| Function | What It Does | How It Handles NULL |
|----------|------|---------------|
| COUNT(*) | Counts all rows in the group, including rows with NULL values in any column. Use this when you want to know "how many rows exist" regardless of their content. | Includes NULLs |
| COUNT(col) | Counts only the rows where the specified column is NOT NULL. This is different from COUNT(*) and catches people off guard. If 10 rows exist but 3 have NULL in that column, COUNT(col) returns 7. | Skips NULLs |
| COUNT(DISTINCT col) | Counts unique non-NULL values in the column. Duplicate values are counted only once, and NULLs are ignored entirely. | Skips NULLs |
| SUM(col) | Adds up all non-NULL values. If every value is NULL, returns NULL (not 0). | Skips NULLs |
| AVG(col) | Computes the average of non-NULL values. This is the most dangerous one — see below. | Skips NULLs (trap!) |
| MIN(col) / MAX(col) | Returns the smallest or largest non-NULL value. Works on numbers, strings (alphabetical order), and dates. | Skips NULLs |

**The AVG trap — this catches experienced developers:**

AVG skips NULL values in BOTH the sum and the count. So if you have values [100, 200, NULL, 400], AVG computes (100+200+400)/3 = 233. It does NOT compute (100+200+0+400)/4 = 175. The NULL is not treated as zero — it's treated as "this row doesn't participate in the calculation at all."

This matters a lot in practice. If bonus is NULL for employees who don't get a bonus, AVG(bonus) gives you the average bonus among employees who DO get one — not the average across all employees. If you want to treat NULL as 0, you must explicitly say so: `AVG(COALESCE(salary, 0))` = 175.

### ROLLUP and CUBE — Automatic Subtotals

These are extensions to GROUP BY that automatically generate subtotals and grand totals in a single query, without needing multiple queries or UNION ALL.

**ROLLUP** generates hierarchical subtotals. It creates groupings from the most detailed level up to a grand total, following the order of columns you specify.

```sql
SELECT region, city, SUM(sales)
FROM orders
GROUP BY ROLLUP(region, city);
```

This produces three levels: (1) sales per city within each region (detailed), (2) sales per region (subtotal — city is NULL), (3) grand total (both region and city are NULL). It rolls up from right to left in the column list.

**CUBE** generates subtotals for ALL possible combinations of the grouped columns, not just the hierarchy.

```sql
GROUP BY CUBE(region, city)
```

This produces: per city+region, per region only (city NULL), per city only (region NULL), AND grand total. It's like ROLLUP but also gives you cross-cutting summaries.

These are very useful for building summary reports where you need totals at multiple levels — something that would otherwise require multiple queries UNIONed together.

---

## 4. Subqueries

A subquery is a query nested inside another query. It's like asking a question where the answer depends on another question you need to ask first. The inner query runs, produces a result, and that result is used by the outer query.

Subqueries can appear in three places: in the WHERE clause (most common), in the FROM clause (called a derived table), or in the SELECT clause (called a scalar subquery). Each has different rules about what it can return.

### Simple Subquery

The simplest kind runs once, produces a single value, and the outer query uses that value.

```sql
SELECT name, salary FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);
```

The inner query calculates the average salary across all employees — let's say it's 75,000. The outer query then becomes effectively `WHERE salary > 75000`. This is called a "non-correlated" subquery because the inner query is completely independent — it doesn't reference anything from the outer query.

### Subquery in FROM (Derived Table)

You can use a subquery in the FROM clause as if it were a table. The result of the subquery becomes a temporary table that the outer query can SELECT from, JOIN with, or filter.

```sql
SELECT dept, avg_sal
FROM (
    SELECT department AS dept, AVG(salary) AS avg_sal
    FROM employees GROUP BY department
) AS dept_averages
WHERE avg_sal > 80000;
```

This is useful when you need to perform aggregation first and then filter or join on the aggregated results. The inner query creates a summary table of department averages, and the outer query filters that summary. Note that you MUST give the derived table an alias (here, `dept_averages`).

### Correlated Subquery — Runs Per Row

A correlated subquery references a column from the outer query, which means it can't run independently. The database must re-execute the inner query for EVERY row of the outer query, substituting the current outer row's values each time. This can be very slow on large tables.

```sql
SELECT name, salary FROM employees e
WHERE salary > (
    SELECT AVG(salary) FROM employees WHERE dept_id = e.dept_id
);
```

Notice the `e.dept_id` reference to the outer query. For each employee, the database asks "what's the average salary in THIS employee's department?" and checks if this employee earns more than that average. If you have 10,000 employees, this inner query runs 10,000 times.

**Better rewrite with CTE:** Correlated subqueries are often a performance red flag. You can usually rewrite them as JOINs or CTEs, which allow the database to compute the result more efficiently — typically once instead of per-row.

```sql
WITH dept_avg AS (
    SELECT dept_id, AVG(salary) AS avg_sal FROM employees GROUP BY dept_id
)
SELECT e.name, e.salary
FROM employees e JOIN dept_avg d ON e.dept_id = d.dept_id
WHERE e.salary > d.avg_sal;
```

This computes department averages once (in the CTE), then joins. Much faster on large datasets.

### EXISTS — Check If Rows Exist

EXISTS is a special subquery construct that returns TRUE if the subquery returns at least one row, and FALSE if it returns zero rows. It doesn't care about the actual data — just whether any rows exist.

```sql
SELECT c.name FROM customers c
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id);
```

This finds customers who have at least one order. The SELECT 1 is a convention — since EXISTS only checks for row existence, the actual column doesn't matter. EXISTS is often faster than IN because it can stop searching as soon as it finds the first match, while IN must build the complete list.

---

## 5. CTEs and Recursive CTEs

CTE stands for Common Table Expression. It's a way to write a named temporary result set that you can reference within your main query. Think of it as creating a temporary view that only exists for the duration of your query.

CTEs solve the readability problem of deeply nested subqueries. Instead of having query-within-query-within-query (which is hard to read and debug), you break the logic into named steps that read top-to-bottom like a recipe.

### Basic CTE

```sql
WITH high_earners AS (
    SELECT name, department, salary FROM employees WHERE salary > 100000
)
SELECT department, COUNT(*) FROM high_earners GROUP BY department;
```

The `WITH high_earners AS (...)` part creates a temporary named result. Then the main query uses it as if it were a table. You can think of the CTE as a variable that holds a table's worth of data.

**Why CTEs beat nested subqueries:** Imagine you need to use the same filtered dataset in multiple places in your query. With subqueries, you'd have to copy-paste the inner query each time. With a CTE, you define it once and reference it by name multiple times. This makes the query shorter, cleaner, and less error-prone.

### Multiple CTEs

You can chain multiple CTEs together, where each one can reference the ones defined before it. This lets you build complex logic step by step:

```sql
WITH
    dept_stats AS (
        SELECT dept_id, AVG(salary) AS avg_sal, COUNT(*) AS cnt
        FROM employees GROUP BY dept_id
    ),
    big_depts AS (
        SELECT dept_id FROM dept_stats WHERE cnt > 10
    )
SELECT e.name FROM employees e
JOIN big_depts b ON e.dept_id = b.dept_id;
```

Step 1 computes department statistics. Step 2 filters to only large departments. Step 3 (the main query) finds employees in those large departments. Each step is simple and easy to understand on its own.

### Recursive CTE — For Hierarchical Data

A recursive CTE is a special type that references itself. It's designed for hierarchical or tree-structured data — like an org chart, a category tree, or a bill of materials. The recursion starts with a base case (the root of the tree) and repeatedly expands by finding children, grandchildren, and so on until no more rows are found.

"Find all reports under a manager, at any depth."

```sql
WITH RECURSIVE org_tree AS (
    -- Base case: the starting manager
    SELECT id, name, manager_id, 1 AS level
    FROM employees WHERE id = 100

    UNION ALL

    -- Recursive case: people who report to someone already in the tree
    SELECT e.id, e.name, e.manager_id, t.level + 1
    FROM employees e
    JOIN org_tree t ON e.manager_id = t.id
)
SELECT * FROM org_tree ORDER BY level;
```

How this executes: First, the base case finds employee 100 (the starting manager). Then the recursive part finds everyone whose manager_id equals an id that's already in the result set. Those new people are added to the result set. Then it runs again, finding people who report to those newly added people. This repeats until no new rows are found.

The `level` column tracks how deep in the hierarchy each person is. Level 1 is the starting manager, level 2 is their direct reports, level 3 is the reports of those reports, and so on.

This is essential for tree structures stored in a single table with parent references — which is one of the most common ways to store hierarchical data in relational databases. Without recursive CTEs, you'd need to write multiple queries or use application code to traverse the tree.

---

## 6. Window Functions

Window functions are one of the most powerful features in SQL, and they're a favorite in interviews because they separate "I know SQL" from "I really know SQL." They let you perform calculations across a set of rows that are somehow related to the current row — without collapsing those rows into a single output row the way GROUP BY does.

### The Core Concept

The fundamental difference between window functions and GROUP BY is this: GROUP BY collapses rows into groups and gives you one output row per group. Window functions compute a value based on a group of rows but keep every individual row in the output. This means you can have a column showing each employee's salary AND a column showing their department's average salary — side by side, on every row.

```sql
SELECT name, department, salary,
       AVG(salary) OVER(PARTITION BY department) AS dept_avg
FROM employees;
```

Every employee row stays intact. Each one gets an additional column showing the average salary of everyone in their department. Vishal in Engineering sees Engineering's average. Raj in Marketing sees Marketing's average. No rows are lost.

### OVER() — The Window Definition

The OVER() clause defines the "window" — which rows the function should consider for its calculation. You can think of it as an invisible group that each row looks through.

```sql
-- No partition = entire table is the window:
SUM(salary) OVER()
-- Every row sees the total salary of ALL employees.

-- PARTITION BY = window per group:
AVG(salary) OVER(PARTITION BY department)
-- Each row sees the average salary of its own department only.

-- ORDER BY = running calculation:
SUM(salary) OVER(ORDER BY hire_date)
-- Each row sees the cumulative sum of salaries from the earliest hire date up to and including the current row. This is a running total.

-- Both combined:
ROW_NUMBER() OVER(PARTITION BY department ORDER BY salary DESC)
-- Within each department, assigns numbers 1, 2, 3... based on salary rank.
```

### Essential Window Functions — What Each One Does

**ROW_NUMBER()** assigns a unique sequential number to each row within its partition. Even if two rows have the same value (a tie), they get different numbers — the database picks an arbitrary order for the tie. Produces: 1, 2, 3, 4. Use when you need exactly one result per group (like "the single highest-paid employee per department").

**RANK()** is like ROW_NUMBER but handles ties by giving tied rows the same rank and then skipping the next number(s). If two people are tied for 2nd place, they both get rank 2, and the next person gets rank 4 (not 3, because two spots were used). Produces: 1, 2, 2, 4. Use when ties matter and you want to reflect the "position gap."

**DENSE_RANK()** is like RANK but without the gap after ties. If two people tie for 2nd, they both get rank 2, and the next person gets rank 3 (not 4). Produces: 1, 2, 2, 3. Use when you want consecutive ranking numbers regardless of ties — for example, "find the 3rd highest salary" where DENSE_RANK ensures you don't skip salary levels.

**NTILE(n)** divides the rows in each partition into n approximately equal groups (buckets) and assigns each row a bucket number from 1 to n. NTILE(4) divides into quartiles. Useful for percentile analysis or distributing work evenly.

**LAG(col, n) and LEAD(col, n)** are used to access values from other rows relative to the current row. LAG looks at previous rows (n rows back), and LEAD looks at upcoming rows (n rows ahead). This is incredibly useful for time-series analysis — comparing each month's revenue to the previous month, or finding the gap between consecutive events.

```sql
SELECT month, revenue,
       LAG(revenue, 1) OVER(ORDER BY month) AS prev_month,
       revenue - LAG(revenue, 1) OVER(ORDER BY month) AS mom_change
FROM monthly_sales;
```

This gives you each month's revenue, the previous month's revenue, and the month-over-month change — all without a self JOIN.

### Frame Specification (Advanced)

By default, when you use ORDER BY in a window function, the frame (the set of rows the function considers) goes "from the start of the partition to the current row." But you can customize this boundary.

The frame specification lets you define a sliding window of rows around the current row. This is essential for moving averages, sliding totals, and other rolling calculations.

```sql
-- Moving average of last 3 rows (current row + 2 before it):
AVG(salary) OVER(ORDER BY hire_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)

-- Running total from start to end of entire partition:
SUM(amount) OVER(PARTITION BY dept ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)

-- 7-day moving average (3 before, current, 3 after):
AVG(amount) OVER(ORDER BY date ROWS BETWEEN 3 PRECEDING AND 3 FOLLOWING)
```

**ROWS vs RANGE:** ROWS counts physical row positions (row 1, row 2, row 3). RANGE groups rows with the same ORDER BY value together. The difference matters when there are ties in the ORDER BY column. For most practical purposes, ROWS is more intuitive and predictable.

### Top N Per Group — The Classic Pattern

This is probably the single most asked window function interview question: "Find the top 3 highest-paid employees in each department."

```sql
WITH ranked AS (
    SELECT name, department, salary,
           ROW_NUMBER() OVER(PARTITION BY department ORDER BY salary DESC) AS rn
    FROM employees
)
SELECT * FROM ranked WHERE rn <= 3;
```

Step 1 (CTE): Within each department partition, rank employees by salary (highest first). The highest paid gets rn=1, second highest gets rn=2, etc. Step 2 (outer query): Filter to only keep rows where rn is 1, 2, or 3 — the top 3 per department.

Why not just `WHERE rn <= 3` in the CTE directly? Because window functions are computed during SELECT (step 6), and WHERE runs before SELECT (step 3). So you can't filter on a window function result in the same query — you need the CTE/subquery wrapper.

---

## 7. NULL Handling

NULL is one of the most misunderstood concepts in SQL. NULL does not mean zero. NULL does not mean empty string. NULL means "unknown" or "not applicable" — the value simply isn't there. And this "unknown" nature has consequences that trip up even experienced developers.

### NULL Arithmetic and Comparisons

Any arithmetic or comparison involving NULL produces NULL (unknown). This is called "three-valued logic" — instead of just TRUE and FALSE, SQL has TRUE, FALSE, and NULL (unknown).

```sql
WHERE bonus = NULL;      -- WRONG! Returns nothing
-- NULL = NULL evaluates to NULL (unknown), not TRUE.
-- The WHERE clause only keeps rows where the condition is TRUE.

WHERE bonus IS NULL;     -- Correct
-- IS NULL is the special operator designed to check for NULL.

WHERE bonus != 100;
-- Does NOT return rows where bonus IS NULL
-- Because NULL != 100 -> NULL (unknown) -> row excluded
-- WHERE only keeps TRUE rows; NULL rows are dropped just like FALSE rows.
```

This means if you write `WHERE status != 'ACTIVE'`, you will NOT get rows where status is NULL. NULL != 'ACTIVE' is not TRUE — it's NULL. To include those rows, you need: `WHERE status != 'ACTIVE' OR status IS NULL`.

NULL also propagates through calculations: `100 + NULL = NULL`, `NULL * 5 = NULL`. Any math with an unknown value gives an unknown result.

### COALESCE, ISNULL, NVL

These functions let you replace NULL with a default value.

```sql
COALESCE(bonus, 0)               -- Returns bonus if not NULL, otherwise returns 0.
                                 -- Standard SQL, works in PostgreSQL, MySQL, SQL Server, Oracle.
                                 -- Can take multiple arguments: COALESCE(a, b, c) returns the first non-NULL.
ISNULL(bonus, 0)                 -- SQL Server only, takes exactly 2 arguments.
NVL(bonus, 0)                    -- Oracle only.
NULLIF(orders_count, 0)          -- Returns NULL if the value equals 0. Very useful to prevent
                                 -- divide-by-zero errors: revenue / NULLIF(orders_count, 0)
                                 -- If orders_count is 0, this becomes revenue / NULL = NULL (safe)
                                 -- instead of revenue / 0 (error).
```

**Best practice:** Always use COALESCE — it's standard SQL that works across all databases, and it's the most flexible because it can take multiple arguments.

### NOT IN vs NOT EXISTS — The NULL Trap

This is one of the most dangerous traps in SQL and a frequent interview question. It has to do with how NOT IN handles NULL values in the subquery result.

```sql
-- DANGEROUS:
WHERE id NOT IN (SELECT customer_id FROM orders);
-- If ANY customer_id in the orders table is NULL, this WHERE clause
-- returns ZERO ROWS. Not some rows — ZERO rows. For every row.
-- Because: id NOT IN (1, 2, NULL) -> id != 1 AND id != 2 AND id != NULL
-- The last condition (id != NULL) is always NULL (unknown).
-- TRUE AND TRUE AND NULL = NULL -> row excluded. Every single row.

-- SAFE:
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id);
-- EXISTS checks for row existence, not value equality.
-- NULLs in customer_id don't cause this problem because the
-- ON condition simply won't match (NULL = c.id is NULL/unknown, not TRUE).
```

**Rule:** Always prefer NOT EXISTS over NOT IN when the subquery column could contain NULLs. This is such a common bug that many style guides recommend always using NOT EXISTS regardless.

---

## 8. Indexes

An index is a separate data structure that the database maintains alongside your table. Its purpose is to speed up data retrieval by providing a shortcut to find rows without scanning the entire table.

### What an Index Is — The Textbook Analogy

The best analogy is a textbook index at the back of a book. Without the index, to find every page that mentions "Kafka," you'd have to read every single page of the book — that's a full table scan. With the index, you look up "Kafka" in the alphabetical index, see "pages 45, 78, 230," and jump directly to those pages. That's what a database index does.

Technically, most indexes use a B-Tree (balanced tree) data structure. The values are stored in sorted order in a tree where each node branches into many children. Looking up a value requires traversing only 3-4 levels of the tree, even for millions of rows. That's O(log n) instead of O(n).

Without index: scan all 10 million rows. O(n).
With index: 3-4 lookups in the tree. O(log n).

### Types of Indexes

**B-Tree (default):** The standard index type in virtually all databases. It stores values in sorted order, which makes it efficient for equality checks (`=`), range comparisons (`>`, `<`, `BETWEEN`), prefix matching (`LIKE 'prefix%'`), and sorting (`ORDER BY`). When you say "CREATE INDEX" without specifying a type, you get a B-Tree.

**Composite (multi-column) index:** An index on multiple columns. The order of columns matters critically because of the "leftmost prefix rule."

```sql
CREATE INDEX idx ON transactions(account_id, txn_date);
```

This index is sorted first by account_id, then by txn_date within each account_id. It can efficiently serve queries that filter by: account_id alone, or account_id AND txn_date. But it CANNOT efficiently serve queries that filter by txn_date alone — because the index is not sorted by txn_date globally, only within each account_id. Think of a phone book sorted by last name, then first name — you can find all "Kharbanda" entries quickly, but finding all "Vishal" entries (any last name) requires scanning the whole book.

**Covering index:** A special case where the index contains ALL the columns a query needs. When this happens, the database can answer the query entirely from the index without ever looking at the actual table data (no "bookmark lookup"). This is the fastest possible query execution.

**Clustered vs Non-Clustered (SQL Server concept):**
- **Clustered index:** The table data itself is physically sorted according to this index. Only ONE per table (because data can only be physically arranged one way). Think of a dictionary — the words ARE arranged alphabetically; the "index" IS the data.
- **Non-Clustered index:** A separate structure with pointers back to the actual data rows. You can have many per table. Think of a textbook index — it's a separate section at the back that points to pages in the main content.

### What Kills Index Performance

Certain patterns prevent the database from using an index, even if one exists on the column. These are called "index-killing" patterns:

```sql
WHERE YEAR(created_at) = 2023    -- Applying a FUNCTION to the column means the database
                                 -- can't use the index. It would need to compute YEAR()
                                 -- for every row first, defeating the purpose.
WHERE created_at >= '2023-01-01' AND created_at < '2024-01-01'  -- This is the correct way.
                                 -- The raw column value is compared directly.

WHERE name LIKE '%kumar'   -- LEADING wildcard means the database can't use the sorted
                           -- index to narrow down results. It must scan everything.
WHERE name LIKE 'kumar%'   -- TRAILING wildcard works with B-Tree because the index
                           -- can find the starting position of 'kumar...'

WHERE account_id = 12345   -- If account_id is a VARCHAR column but you pass an integer,
                           -- the database may need to convert every row's value,
                           -- preventing index use (implicit type casting).
WHERE account_id = '12345' -- Matching types = index can be used.
```

### When NOT to Create Indexes

Indexes aren't free — they cost disk space and slow down writes (INSERT, UPDATE, DELETE) because every write must also update every relevant index. So you should NOT index:

- **Small tables** (hundreds of rows): A full scan is so fast that the overhead of an index lookup is actually slower.
- **Columns never used in WHERE, JOIN, or ORDER BY**: If you never search or sort by a column, an index on it is pure waste.
- **Tables with very heavy writes and few reads**: Every INSERT updates all indexes. If you're bulk-loading millions of rows, indexes slow you down significantly.
- **Low-cardinality columns** (like gender with 2 values, or boolean flags): An index that eliminates only half the rows doesn't save much compared to a full scan.

---

## 9. EXPLAIN / EXPLAIN ANALYZE — Reading Execution Plans

EXPLAIN is like an X-ray for your SQL query. It shows you exactly what the database plans to do (or did) to execute your query — which tables it scans, what indexes it uses, how it joins tables, and how much work each step takes. This is how you diagnose slow queries.

```sql
EXPLAIN ANALYZE
SELECT e.name, d.dept_name
FROM employees e
JOIN departments d ON e.dept_id = d.id
WHERE e.salary > 100000;
```

**EXPLAIN** alone shows the plan without running the query (what the database WOULD do). **EXPLAIN ANALYZE** actually runs the query and shows both the planned and actual execution metrics. Use EXPLAIN for dangerous queries (you don't want to accidentally execute a slow query), and EXPLAIN ANALYZE for detailed performance diagnosis.

### What to Look For in the Output

| What You See | What It Means | Should You Worry? |
|---|---|---|
| Seq Scan / Table Scan | The database is reading every single row in the table from start to finish. No index is being used. | Yes, if the table is large. Small tables are fine with seq scans. |
| Index Scan / Index Seek | The database is using an index to jump directly to the relevant rows. This is what you want to see for filtered queries on large tables. | No — this is good. |
| Hash Join | The database built a hash table from the smaller table and is probing it with the larger table. This is the most efficient join method for large equality-based joins. | No — this is usually optimal. |
| Nested Loop | For each row in one table, the database is scanning the other table for matches. This is O(n*m) and can be very slow if both tables are large. | Yes, if both sides are large. Fine if one side is small. |
| Sort | The database is sorting data, possibly for ORDER BY or for a sort-merge join. If the data is too large for memory, it spills to disk, which is very slow. | Depends on the dataset size. Watch for "external sort" or "disk sort." |
| Actual rows >> Estimated rows | The database's statistics are outdated. It estimated 100 rows but actually found 100,000. This means it may have chosen a bad plan. | Yes — run ANALYZE to update statistics. |

**When to check execution plans:**
- When a query is unexpectedly slow — EXPLAIN shows you the bottleneck
- After adding or removing indexes — verify the database is actually using your new index
- Before deploying a new query to production — catch potential performance issues early
- When the same query suddenly gets slow — statistics might be stale, or data distribution changed

---

## 10. Transactions and ACID

A transaction is a group of SQL statements that must either ALL succeed or ALL fail together. There's no middle ground — no partial completion. This is fundamental to data integrity.

### Why Transactions Exist — The Bank Transfer Problem

Imagine transferring $1000 from Account A to Account B. This requires two operations: deducting from A and adding to B. What if the system crashes between the two operations?

```sql
UPDATE accounts SET balance = balance - 1000 WHERE id = 'A';
-- CRASH HERE -- power failure, disk error, anything
UPDATE accounts SET balance = balance + 1000 WHERE id = 'B';
```

Without transactions, Account A lost $1000, but Account B never received it. The money vanished. Transactions prevent this:

```sql
BEGIN TRANSACTION;
    UPDATE accounts SET balance = balance - 1000 WHERE id = 'A';
    UPDATE accounts SET balance = balance + 1000 WHERE id = 'B';
COMMIT;
```

If anything goes wrong between BEGIN and COMMIT, the entire transaction is rolled back — Account A gets its $1000 back as if nothing happened. Either BOTH updates happen, or NEITHER does.

### ACID Properties — The Four Guarantees

ACID is an acronym for the four properties that every transaction must have. This is a very common interview question — you should be able to explain each one with an example.

**Atomicity (All or Nothing):** A transaction is a single, indivisible unit of work. If any part of the transaction fails, ALL changes are rolled back. In the bank example, if the second UPDATE fails, the first UPDATE is also undone. You never end up with money that disappeared or appeared from nowhere.

**Consistency (Rules Are Never Broken):** A transaction takes the database from one valid state to another valid state. All constraints, foreign keys, checks, and triggers are satisfied before AND after the transaction. If a transaction would violate a constraint (like making a balance negative when there's a CHECK constraint), the entire transaction is rejected.

**Isolation (Transactions Don't Interfere):** Even when multiple transactions run at the same time (concurrently), each transaction behaves as if it's the only one running. Transaction A doesn't see Transaction B's half-completed changes. The exact level of isolation is configurable (see isolation levels below).

**Durability (Committed Data Survives Crashes):** Once a transaction is committed (you see the COMMIT succeed), the changes are permanent. Even if the server crashes one millisecond after COMMIT, when it restarts, your changes will still be there. Databases achieve this by writing to a transaction log (WAL — Write-Ahead Log) on disk before confirming the commit.

### Isolation Levels — The Trade-Off Between Safety and Speed

Isolation levels control how much one transaction can see of another concurrent transaction's changes. Higher isolation is safer but slower (more locking and blocking). Lower isolation is faster but allows certain anomalies.

**READ UNCOMMITTED (lowest, rarely used):** A transaction can see uncommitted changes from other transactions. This is called a "dirty read" — you might read data that gets rolled back and never actually existed. Almost no production system uses this because the data is unreliable.

**READ COMMITTED (PostgreSQL default, most common):** A transaction only sees data that has been committed by other transactions. This eliminates dirty reads. However, if you read the same row twice within your transaction, and someone committed a change to that row between your two reads, you'll see different values. This is called a "non-repeatable read." For most applications, this is perfectly fine.

**REPEATABLE READ (MySQL default):** Once your transaction reads a row, re-reading it always returns the same value, even if other transactions modify and commit changes to that row. This eliminates non-repeatable reads. However, if another transaction inserts NEW rows that match your query's WHERE clause, those new rows might appear in your result on re-query. These "ghost" new rows are called "phantom reads."

**SERIALIZABLE (highest, slowest):** Transactions behave as if they executed one after another in some serial order, with no overlap. This eliminates all anomalies — dirty reads, non-repeatable reads, and phantom reads. But the database achieves this by aggressively locking or detecting conflicts, which can lead to more transaction failures (the database may abort and retry transactions).

**Practical guidance:** READ COMMITTED is fine for 90% of applications. Use REPEATABLE READ or SERIALIZABLE when you're doing multi-step financial calculations where reading inconsistent data would cause errors — for example, checking a balance and then debiting, where you need the balance to stay stable between the check and the debit.

### Deadlocks — When Transactions Block Each Other

A deadlock occurs when two or more transactions are each waiting for a resource held by the other, creating a circular dependency where nobody can proceed.

Transaction 1: Locks row A, then tries to lock row B (held by Transaction 2) -> waits.
Transaction 2: Locks row B, then tries to lock row A (held by Transaction 1) -> waits.
Both are stuck forever — each is waiting for the other to release.

**How the database handles it:** All major databases have deadlock detection. The database periodically checks for circular wait patterns. When it finds one, it picks one transaction as the "victim," rolls it back (releasing its locks), and lets the other proceed. Your application receives an error and should retry the rolled-back transaction.

**How to prevent deadlocks:** The most effective strategy is to always lock resources in a consistent order. If every transaction always locks row A before row B (for example, by always processing rows in ascending ID order), the circular dependency can never form.

### Optimistic vs Pessimistic Locking — Two Philosophies

These are two different strategies for handling concurrent access to the same data.

**Pessimistic locking — "I expect conflicts, so I'll prevent them upfront."**

```sql
SELECT * FROM products WHERE id = 1 FOR UPDATE;  -- locks the row NOW
-- No one else can modify this row until your transaction finishes
UPDATE products SET stock = stock - 1 WHERE id = 1;
COMMIT;  -- lock released
```

The moment you SELECT with FOR UPDATE, the database locks that row. Any other transaction trying to read (with FOR UPDATE) or modify that row will WAIT until you COMMIT or ROLLBACK. This guarantees safety but can create bottlenecks — if your transaction takes 5 seconds, everyone else waits 5 seconds.

**Use when:** Conflicts are frequent, or the cost of a conflict is very high (financial transactions).

**Optimistic locking — "I assume conflicts are rare, so I'll check at the end."**

```sql
-- Step 1: Read current state, including a version number
SELECT id, stock, version FROM products WHERE id = 1;  -- stock=10, version=3

-- Step 2: Do your work (maybe show a UI, make calculations, etc.)

-- Step 3: Update, but ONLY if no one else changed it since you read it
UPDATE products SET stock = 9, version = 4 WHERE id = 1 AND version = 3;
-- If 0 rows affected -> someone else already changed it -> RETRY from Step 1
```

No locks are held during your thinking/processing time. You just check at the end whether someone else modified the data. If they did (version changed), you retry. If not, your update succeeds.

**Use when:** Conflicts are rare — which is true for most web applications where thousands of users are editing different records simultaneously. Only a tiny fraction of requests involve the same row at the same time.

---

## 11. Normalization

Normalization is the process of organizing a database to reduce data redundancy (the same information stored in multiple places) and eliminate certain types of data anomalies (insert, update, and delete anomalies). You do this by breaking one large table into smaller, related tables.

### Why Normalize?

Imagine a single table storing orders with customer info repeated on every row:

```
| order_id | customer_name | customer_address   | product | amount |
|----------|---------------|--------------------|---------|--------|
| 1        | Vishal        | 123 MG Road, Noida | Laptop  | 50000  |
| 2        | Vishal        | 123 MG Road, Noida | Mouse   | 500    |
```

Vishal's name and address are stored twice (once per order). If Vishal moves, you need to update EVERY row — miss one and you have inconsistent data. If you delete both orders, you lose Vishal's address entirely, even though you just wanted to delete orders. These are update anomalies, insert anomalies, and delete anomalies.

### 1NF — First Normal Form: Atomic Values, No Repeating Groups

Each cell should contain a single value (not a comma-separated list or an array), and each row should be unique.

Bad: `| Vishal | Math, Physics, CS |` — one cell contains multiple values.
Good: Three rows, one per course, each with a single value in the course column.

The idea is that every piece of data should be independently queryable. If courses are comma-separated in one cell, you can't easily find "all students taking Physics" with a simple WHERE clause.

### 2NF — Second Normal Form: Full Dependency on the Key

Every non-key column must depend on the ENTIRE primary key, not just part of it. This only applies when you have a composite primary key (a key made of multiple columns).

If your key is (student_id, course_id), and you have a column student_name, that name depends only on student_id — it has nothing to do with course_id. So student_name should be moved to a separate students table with student_id as the key.

### 3NF — Third Normal Form: No Transitive Dependencies

Every non-key column must depend DIRECTLY on the primary key, not on another non-key column.

If an employees table has: employee_id -> dept_id -> dept_name, then dept_name depends on dept_id (not directly on employee_id). Move dept_name to a departments table. The employee table keeps only dept_id as a foreign key.

A common way to remember: "Every non-key column must provide a fact about the key, the whole key, and nothing but the key."

### When to Denormalize — Breaking the Rules on Purpose

Normalization reduces redundancy but increases the number of JOINs needed to reconstruct complete information. For analytical/reporting workloads (OLAP), this JOIN overhead can be unacceptable when querying billions of rows.

In these cases, you intentionally denormalize — duplicating data across tables to avoid JOINs and speed up reads. This is exactly what your star schema at Azure Synapse does — a central fact table (transactions) surrounded by dimension tables (customer, product, date), with some data duplicated for query performance.

The trade-off is clear: normalized = less storage, easier updates, more JOINs. Denormalized = more storage, harder updates, fewer JOINs, faster reads.

---

## 12. Constraints

Constraints are rules that the database enforces on your data. They're your last line of defense against bad data — even if your application has a bug that lets invalid data through, constraints will catch it at the database level. This is why constraints are critical for data integrity.

**PRIMARY KEY** — Uniquely identifies each row in the table. Must be unique AND not null. Only one primary key per table (though it can span multiple columns as a composite PK). The database automatically creates an index on the primary key. Think of it as the "ID card" of each row.

**FOREIGN KEY** — A column that references the primary key of another table. It ensures referential integrity — you can't insert an order with customer_id = 999 if no customer with id = 999 exists. It creates a relationship between tables and prevents "orphan" records (orders that point to non-existent customers).

**UNIQUE** — Ensures no two rows have the same value in this column (or combination of columns). Unlike PRIMARY KEY, UNIQUE allows NULL values (and in most databases, multiple NULLs are allowed because NULL != NULL). Use for things like email addresses — they should be unique but aren't the primary identifier.

**NOT NULL** — Prevents the column from containing NULL values. Every row must have an actual value in this column. Use for mandatory fields like names, dates, or amounts where "unknown" isn't acceptable.

**CHECK** — Enforces a custom rule that every row must satisfy: `CHECK (salary >= 0)` prevents negative salaries, `CHECK (status IN ('ACTIVE', 'INACTIVE'))` restricts to allowed values. The database rejects any INSERT or UPDATE that violates the check.

**DEFAULT** — Specifies a value to use when none is provided during INSERT: `DEFAULT CURRENT_TIMESTAMP` for created_at, `DEFAULT 'PENDING'` for status. This isn't really a constraint (it doesn't restrict data) but is often discussed alongside constraints.

### CASCADE on Foreign Keys — What Happens When the Parent Is Deleted

When a foreign key relationship exists and you try to delete a parent row (a customer who has orders), the database needs to know what to do with the child rows (those orders). This is configured with ON DELETE and ON UPDATE actions:

```sql
REFERENCES customers(id) ON DELETE CASCADE
```

- **CASCADE:** Automatically delete all child rows when the parent is deleted. Delete a customer → all their orders are deleted too. Convenient but dangerous — a single DELETE can cascade through many tables.
- **SET NULL:** Set the foreign key column to NULL in child rows. The orders remain but lose their customer reference. Only works if the FK column allows NULL.
- **RESTRICT / NO ACTION:** Block the deletion entirely. You cannot delete a customer who has orders. You must delete the orders first. This is the safest option and the default in most databases.

### Referential Integrity — The Bigger Picture

Referential integrity means that every foreign key value in a child table must correspond to an existing primary key value in the parent table. No orphans. No dangling references. The database enforces this automatically through foreign key constraints.

Without referential integrity, you could end up with orders pointing to customers that were deleted, employees assigned to departments that don't exist, or any number of data inconsistencies that are extremely hard to clean up after the fact.

---

## 13. Views and Materialized Views

### View — A Saved Query (Virtual Table)

A view is essentially a named SELECT query that you can use as if it were a table. It doesn't store any data itself — every time you query the view, it executes the underlying SELECT statement in real time. Think of it as a saved shortcut or an alias for a complex query.

```sql
CREATE VIEW active_customers AS
SELECT id, name FROM customers WHERE status = 'ACTIVE';

-- Now you can do:
SELECT * FROM active_customers;
-- Which is identical to running the underlying query.
```

**Why views are useful:**

1. **Simplification:** If you have a complex query that joins 5 tables, you can save it as a view. Anyone querying the view writes a simple SELECT, hiding the complexity.
2. **Security:** You can grant a user access to a view that shows only certain columns or filtered rows, without giving them access to the full underlying table. For example, a view that shows employee names and departments but hides salaries.
3. **Consistency:** If 20 reports all need the same base query, define it as a view once. If the logic changes, update the view — all 20 reports automatically use the updated logic.

Views are not materialized — they don't cache results. If the underlying table has 10 million rows, querying the view scans 10 million rows every time.

### Materialized View — Pre-Computed and Stored

A materialized view is like a regular view except it actually executes the query and stores the results physically on disk. When you query a materialized view, it reads the pre-computed results instead of re-running the underlying query. This makes reads extremely fast — as fast as reading a regular table.

```sql
CREATE MATERIALIZED VIEW monthly_summary AS
SELECT DATE_TRUNC('month', date) AS month, SUM(amount) AS total
FROM orders GROUP BY 1;
```

The trade-off is staleness: since the data is pre-computed, it can become outdated when the underlying data changes. You need to explicitly refresh it:

```sql
REFRESH MATERIALIZED VIEW monthly_summary;
```

**When to use materialized views:** When a query is expensive (scanning millions of rows, heavy aggregations, multiple JOINs), is queried frequently (many users run the same report), and doesn't need to be real-time (yesterday's summary is fine). Dashboard queries, executive reports, and analytics aggregations are perfect use cases.

---

## 14. Stored Procedures, Functions, Triggers, and Cursors

These are programmable database objects — they let you write procedural logic (if/else, loops, variables) inside the database itself rather than in application code.

**Function:** Takes input parameters, performs computation, and returns a single value (or a table). Can be used inside a SELECT statement just like a built-in function (SUM, AVG, etc.). Functions should NOT have side effects — they shouldn't modify data, only compute and return.

```sql
CREATE FUNCTION calc_tax(amount DECIMAL) RETURNS DECIMAL AS $$
BEGIN RETURN amount * 0.18; END;
$$ LANGUAGE plpgsql;

SELECT name, calc_tax(salary) FROM employees;
```

**Procedure:** Performs a series of actions (INSERT, UPDATE, DELETE). Unlike functions, procedures CAN modify data and perform transactions. They're called separately with CALL, not used inside SELECT.

```sql
CREATE PROCEDURE transfer_money(sender INT, receiver INT, amt DECIMAL) AS $$
BEGIN
    UPDATE accounts SET balance = balance - amt WHERE id = sender;
    UPDATE accounts SET balance = balance + amt WHERE id = receiver;
END;
$$ LANGUAGE plpgsql;

CALL transfer_money(1, 2, 1000);
```

Procedures are useful for encapsulating complex multi-step business logic in the database. However, modern applications often prefer to put this logic in application code (Python, Java) because it's easier to test, debug, and version control.

### Triggers — Automatic Reactions to Data Changes

A trigger is a piece of code that automatically executes when a specific event occurs on a table (INSERT, UPDATE, or DELETE). You don't call triggers manually — they fire automatically. They're like event listeners for your database.

```sql
CREATE TRIGGER audit_salary AFTER UPDATE ON employees
FOR EACH ROW WHEN (OLD.salary != NEW.salary)
EXECUTE FUNCTION log_salary_change();
```

This trigger fires after every UPDATE on the employees table, but only when the salary column actually changed. It calls a function that logs the old and new salary values to an audit table.

**Common uses:** Audit logging (tracking who changed what and when), auto-updating timestamps (setting `updated_at` on every UPDATE), enforcing complex business rules that can't be expressed as simple CHECK constraints, and maintaining derived/summary data.

**Why triggers are often avoided in modern systems:** They add hidden logic — when you read an UPDATE statement, you don't see that 3 triggers will also fire. This makes debugging very difficult. They slow down writes because every INSERT/UPDATE/DELETE has extra work. Cascading triggers (trigger A fires trigger B which fires trigger C) can be nearly impossible to reason about. Modern alternative: event-driven architecture (like Debezium + Kafka, which you used at XenonStack) — explicit, visible, and testable.

### Cursors — Row-by-Row Processing

A cursor lets you iterate through query results one row at a time, like a for-loop in Python. You declare a cursor, open it, fetch rows one at a time, process each row, and then close it.

**Almost always a bad idea.** SQL is designed for set-based operations — one UPDATE statement that affects 10,000 rows is 10-100x faster than a cursor loop that updates one row at a time. The only acceptable use case is when each row requires an external action that can't be expressed in SQL — like sending an email per row or calling an API per row. Even then, it's usually better to SELECT the rows into application code and handle them there.

---

## 15. Advanced Concepts

### MERGE / UPSERT — Insert-or-Update in One Statement

MERGE (also called UPSERT) combines INSERT and UPDATE into a single atomic statement. If the target row exists, update it. If it doesn't exist, insert it. This eliminates the need for "check if exists, then insert or update" logic, which is both verbose and prone to race conditions.

```sql
-- SQL Server / Azure Synapse:
MERGE INTO target USING source ON target.id = source.id
WHEN MATCHED THEN UPDATE SET amount = source.amount
WHEN NOT MATCHED THEN INSERT (id, amount) VALUES (source.id, source.amount);

-- PostgreSQL:
INSERT INTO target (id, amount) VALUES (1, 500)
ON CONFLICT (id) DO UPDATE SET amount = EXCLUDED.amount;
```

This is directly relevant to your XenonStack work: when loading data from Kafka into Azure Synapse, the same event might be processed more than once (at-least-once delivery). Without UPSERT, duplicate processing creates duplicate rows. With UPSERT, processing the same event twice produces the same result (idempotency) — the row is simply updated with the same values.

### Partitioning — Splitting Large Tables Into Manageable Pieces

When a table grows to hundreds of millions or billions of rows, even indexed queries become slow because the indexes themselves are enormous. Partitioning solves this by physically splitting one logical table into multiple smaller physical tables (partitions), each holding a subset of the data.

```sql
CREATE TABLE transactions (
    id BIGINT, amount DECIMAL, txn_date DATE
) PARTITION BY RANGE (txn_date);

CREATE TABLE txn_2023_q1 PARTITION OF transactions
    FOR VALUES FROM ('2023-01-01') TO ('2023-04-01');
```

**Partition pruning** is the key benefit: When you query `WHERE txn_date = '2023-02-15'`, the database knows that this date falls in Q1 2023, so it only scans the txn_2023_q1 partition — it completely skips all other partitions. Instead of scanning a billion-row table, you might scan a 50-million-row partition.

**Other benefits:** You can drop an entire partition instantly to archive old data (instead of DELETE which is slow and generates tons of log). Maintenance operations (VACUUM, ANALYZE, rebuilding indexes) can run on individual partitions without affecting the whole table.

### Sharding — Splitting Across Servers

Partitioning splits a table within one database server. Sharding goes further — it splits data across multiple independent database servers (shards), each on its own hardware. This provides horizontal scalability beyond what a single server can handle.

For example, shard by customer_id: customers A-M are on Server 1 (shard 1), customers N-Z are on Server 2 (shard 2). Each shard is a fully independent database.

The challenge with sharding is that cross-shard queries are very expensive or impossible. If you need to JOIN data across shards, you'd need to query both shards separately and combine results in application code. This is why the choice of shard key (which column to shard by) is one of the most important architectural decisions.

### SQL Injection — Security You Must Know

SQL injection is when an attacker manipulates user input to alter your SQL query. It's one of the most common and dangerous web vulnerabilities.

```python
# VULNERABLE (never do this):
query = f"SELECT * FROM users WHERE name = '{user_input}'"
# If user_input = "'; DROP TABLE users; --"
# The query becomes: SELECT * FROM users WHERE name = ''; DROP TABLE users; --'
# Your table is gone.

# SAFE (parameterized query):
cursor.execute("SELECT * FROM users WHERE name = %s", (user_input,))
```

With parameterized queries, the database treats the parameter as DATA, not as SQL code. Even if the user types `'; DROP TABLE users; --`, the database searches for a user literally named that string. The SQL structure can never be altered by user input.

**Rule:** NEVER concatenate user input into SQL strings. ALWAYS use parameterized queries or an ORM's query builder.

### CHAR vs VARCHAR vs TEXT

**CHAR(10):** Fixed-length string. ALWAYS stores exactly 10 characters, padding with spaces if the value is shorter. Use for truly fixed-length codes like country codes ('IN', 'US'), or ISO currency codes ('INR', 'USD'). Wastes space if values are shorter than the specified length.

**VARCHAR(100):** Variable-length string up to 100 characters. Only stores as many characters as needed (no padding). This is the right choice for most string columns — names, emails, addresses, descriptions. You specify a maximum length as a safety limit.

**TEXT:** Variable-length string with no practical upper limit. In PostgreSQL, TEXT and VARCHAR are essentially identical in performance — the only difference is that VARCHAR has an optional length check. In SQL Server, TEXT is deprecated in favor of VARCHAR(MAX).

### Collation — How Text Is Compared and Sorted

Collation defines the rules for comparing and sorting text: Is 'A' equal to 'a'? Does 'ñ' sort between 'n' and 'o'? Different collations answer these questions differently.

**CI (Case Insensitive):** 'Vishal' = 'vishal' = 'VISHAL'. This is what most applications want.
**CS (Case Sensitive):** 'Vishal' ≠ 'vishal'. Use when case matters (passwords, codes).

If your database uses a case-sensitive collation and you run `WHERE email = 'Vishal@email.com'`, it won't find the row `vishal@email.com`. You'd need to use `WHERE LOWER(email) = LOWER('Vishal@email.com')` or change the collation.

### Aggregate vs Scalar Functions

**Scalar function:** Takes ONE input value and returns ONE output value. Examples: UPPER('hello') -> 'HELLO', ROUND(3.14159, 2) -> 3.14, COALESCE(NULL, 'default') -> 'default'. You can use scalar functions in SELECT, WHERE, or anywhere a value is expected.

**Aggregate function:** Takes MANY input values (a set of rows) and returns ONE output value. Examples: SUM(salary), COUNT(*), AVG(score). They collapse multiple rows into a single result and are used with GROUP BY.

---

## 16. Common Interview Query Patterns

These are the patterns that appear most frequently in SQL coding interviews. Each one tests a specific concept.

### Find Duplicates

This tests your understanding of GROUP BY and HAVING. The idea is to group rows by the column that should be unique, count how many rows are in each group, and keep only groups with more than one row (duplicates).

```sql
SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1;
```

### Delete Duplicates (Keep One)

This takes the previous pattern further — now you need to actually remove the duplicates while keeping one copy. The trick is to use ROW_NUMBER within each group and delete all rows except the first (rn=1).

```sql
WITH ranked AS (
    SELECT id, ROW_NUMBER() OVER(PARTITION BY email ORDER BY id) AS rn FROM users
)
DELETE FROM users WHERE id IN (SELECT id FROM ranked WHERE rn > 1);
```

ORDER BY id ensures you keep the row with the smallest id (the "original") and delete the rest.

### Nth Highest Salary

A perennial interview favorite. The trick is using DENSE_RANK (not RANK or ROW_NUMBER) because DENSE_RANK handles ties correctly — if two people have the same salary, they share the same rank, and the next distinct salary gets the next rank number.

```sql
WITH ranked AS (
    SELECT DISTINCT salary, DENSE_RANK() OVER(ORDER BY salary DESC) AS rnk FROM employees
)
SELECT salary FROM ranked WHERE rnk = 3;
```

If you used ROW_NUMBER, two people with the same salary would get different row numbers, and you might miss the true "3rd highest salary." If you used RANK, ties would cause gaps (1, 2, 2, 4), and there might be no rank 3.

### Employees Earning More Than Manager

This tests self JOIN understanding. Both the employee and the manager are in the same table, linked by manager_id.

```sql
SELECT e.name FROM employees e
JOIN employees m ON e.manager_id = m.id
WHERE e.salary > m.salary;
```

### Employees Above Department Average

This tests your ability to combine aggregation with row-level comparison. You can't do this in one simple query because you need to compare each employee's salary against their department's average — which is an aggregated value.

```sql
WITH dept_avg AS (
    SELECT dept_id, AVG(salary) AS avg_sal FROM employees GROUP BY dept_id
)
SELECT e.name, e.salary, d.avg_sal
FROM employees e JOIN dept_avg d ON e.dept_id = d.dept_id
WHERE e.salary > d.avg_sal;
```

### Running Total

This tests window functions. The ORDER BY in the window definition creates a cumulative sum — each row shows the total of all amounts from the first row up to the current row.

```sql
SELECT date, amount, SUM(amount) OVER(ORDER BY date) AS running_total FROM orders;
```

### Year-Over-Year Comparison

This tests LAG with a larger offset. LAG(revenue, 12) looks 12 months back — the same month last year.

```sql
WITH monthly AS (
    SELECT DATE_TRUNC('month', order_date) AS month, SUM(amount) AS revenue
    FROM orders GROUP BY 1
)
SELECT month, revenue,
       LAG(revenue, 12) OVER(ORDER BY month) AS same_month_last_year,
       revenue - LAG(revenue, 12) OVER(ORDER BY month) AS yoy_change
FROM monthly;
```

### Customers With No Orders

This tests LEFT JOIN + IS NULL pattern — one of the most practical patterns in real work. You want to find the gaps — records in one table that have no corresponding records in another.

```sql
SELECT c.name FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
WHERE o.id IS NULL;
```

LEFT JOIN keeps all customers. For those with no orders, all order columns are NULL. The WHERE clause then filters to keep only those NULL rows.

### Pivot / Conditional Aggregation

This tests CASE WHEN inside aggregate functions — a technique for turning rows into columns. Instead of having separate rows for each gender, you create separate columns.

```sql
SELECT department,
       COUNT(CASE WHEN gender = 'M' THEN 1 END) AS male,
       COUNT(CASE WHEN gender = 'F' THEN 1 END) AS female
FROM employees GROUP BY department;
```

The CASE WHEN returns 1 when the condition is true and NULL otherwise (implicitly). COUNT skips NULLs, so it only counts the matching rows.

### Gaps and Islands (Consecutive Streaks)

This is an advanced pattern that tests creative use of window functions. The goal is to find consecutive sequences (islands) in data — like finding users who logged in 3 or more days in a row.

```sql
WITH numbered AS (
    SELECT user_id, login_date,
           login_date - INTERVAL '1 day' * ROW_NUMBER() OVER(
               PARTITION BY user_id ORDER BY login_date) AS grp
    FROM logins
)
SELECT user_id, MIN(login_date) AS start, MAX(login_date) AS end,
       COUNT(*) AS streak
FROM numbered GROUP BY user_id, grp HAVING COUNT(*) >= 3;
```

The trick: for consecutive dates, subtracting an incrementing number produces the same value. Dates Jan 1, Jan 2, Jan 3 minus row numbers 1, 2, 3 all give Dec 31. That's the "grp" value. Consecutive dates in the same group means they form a streak.

### Median (No Built-In in Standard SQL)

Finding the median (middle value) is surprisingly hard in SQL because there's no standard MEDIAN function. The approach uses ROW_NUMBER to find the middle position(s) and averages them.

```sql
WITH ordered AS (
    SELECT salary, ROW_NUMBER() OVER(ORDER BY salary) AS rn,
           COUNT(*) OVER() AS total FROM employees
)
SELECT AVG(salary) AS median FROM ordered
WHERE rn IN (FLOOR((total+1)/2.0), CEIL((total+1)/2.0));
```

For an odd number of rows, FLOOR and CEIL give the same position (the true middle). For an even number, they give the two middle positions, and AVG averages them.

---

## 17. Theory Questions — What Interviewers Expect You to Explain

These are conceptual questions that don't involve writing code but test your understanding of SQL fundamentals. Interviewers want you to explain these in your own words, not just give one-line definitions.

**DDL vs DML vs DCL vs TCL:**
DDL (Data Definition Language) deals with the structure of the database — creating, modifying, and deleting tables and schemas. Commands: CREATE TABLE, ALTER TABLE, DROP TABLE, TRUNCATE. These change what the database looks like.
DML (Data Manipulation Language) deals with the data inside the tables — reading and modifying rows. Commands: SELECT, INSERT, UPDATE, DELETE. These change what's stored in the database.
DCL (Data Control Language) deals with permissions and access control. Commands: GRANT (give someone permission to do something), REVOKE (take that permission away).
TCL (Transaction Control Language) deals with transaction management. Commands: BEGIN, COMMIT (make changes permanent), ROLLBACK (undo changes), SAVEPOINT (create a restore point within a transaction).

**Primary Key vs Foreign Key:**
A Primary Key uniquely identifies each row in a table. Every value must be unique and not NULL. It's like a Social Security Number or Aadhaar number — no two rows can have the same one, and every row must have one. A table can have only ONE primary key (though it can span multiple columns).
A Foreign Key is a column in one table that references the primary key of another table. It creates a relationship between the two tables. For example, an order's customer_id is a foreign key pointing to the customers table's id (primary key). The database enforces that the referenced row must exist — you can't create an order for a non-existent customer.

**Composite Key:** A primary key or unique key made up of two or more columns together. Neither column alone is unique, but their combination is. For example, (student_id, course_id) in an enrollment table — a student can enroll in many courses, and a course has many students, but each student enrolls in each course only once.

**Surrogate vs Natural Key:** A surrogate key is an artificially generated identifier with no business meaning — like an auto-increment integer ID or a UUID. A natural key uses real-world data that is inherently unique — like an email address or Social Security Number. Surrogate keys are preferred because natural keys can change (people change email addresses), can be complex (multi-column natural keys), and can have format issues. Surrogate keys are simple, immutable, and system-controlled.

**UNION vs JOIN:** These are completely different operations that serve different purposes. JOIN combines columns horizontally — it takes columns from table A and columns from table B and puts them side by side on the same row, linked by a matching condition. UNION stacks rows vertically — it takes the rows from query A and the rows from query B and puts them one after another into a single result set. The queries in a UNION must have the same number of columns with compatible types.

**DELETE vs TRUNCATE vs DROP:**
DELETE removes specific rows (with WHERE clause) or all rows (without WHERE). It's slow on large tables because it logs each deleted row for potential rollback. You can filter which rows to delete, and it fires triggers.
TRUNCATE removes ALL rows instantly by deallocating the data pages rather than deleting row by row. Much faster than DELETE for clearing a table. Cannot filter (no WHERE clause). Doesn't fire row-level triggers. In most databases, it's minimally logged and may not be rollbackable.
DROP removes the entire table — not just the data but the table definition itself. After DROP, the table no longer exists. You'd need to re-CREATE it.

**CASE WHEN — SQL's If-Else:**
CASE WHEN is how you implement conditional logic in SQL. It evaluates conditions in order and returns the value of the first matching condition, just like if/elif/else in Python. You can use it in SELECT (to compute conditional columns), in WHERE (to apply conditional filters), in ORDER BY (to sort by custom logic), and inside aggregate functions (for conditional counting/summing).

**DISTINCT:** Removes duplicate rows from the result set. If your query returns the same row values multiple times (because of JOINs or the data itself), DISTINCT ensures each unique combination appears only once. Performance note: DISTINCT requires the database to sort or hash the results to find duplicates, so it adds overhead. If your query shouldn't produce duplicates, fix the query rather than masking the problem with DISTINCT.

**EXISTS vs IN:**
EXISTS checks whether a subquery returns at least one row. It stops searching as soon as it finds the first match, which makes it efficient for large subquery results. The database only needs to know "does at least one matching row exist?" — not "what are all the matching rows?"
IN checks whether a value is in a list (or in the result of a subquery). It typically evaluates the entire subquery to build the complete list.
NOT EXISTS handles NULLs correctly (because it checks for row existence, not value equality). NOT IN can return zero rows unexpectedly if any value in the list is NULL. Always prefer NOT EXISTS when NULLs might be present.

---

## 18. SQL Connected to Your Resume

Understanding how SQL concepts map to your actual work experience helps you give concrete interview answers instead of textbook definitions.

| What You Did | SQL Concepts Involved |
|---|---|
| Kafka -> Synapse loading | You used MERGE/UPSERT statements for idempotent data loading — ensuring that processing the same Kafka message twice doesn't create duplicate rows. This is critical for at-least-once delivery guarantees. |
| Data quality checks | You wrote COUNT queries to verify row counts between source and target, checked for unexpected NULLs with IS NULL conditions, and compared aggregates (SUM, AVG) across pipeline stages to ensure data wasn't lost or duplicated during ETL. |
| Power BI dashboards | You created views and pre-aggregated tables that Power BI could query efficiently. DirectQuery mode sends SQL queries to the database on every interaction, so query performance directly affected dashboard responsiveness. |
| PySpark pipelines | Spark DataFrame operations map directly to SQL: filter() = WHERE, groupBy().agg() = GROUP BY, join() = JOIN, select() = SELECT. Understanding SQL helps you write better Spark code because the concepts are identical. |
| Flask/FastAPI APIs | Your API endpoints execute SQL queries (directly or through SQLAlchemy ORM) to read and write data. Understanding indexes, query optimization, and transactions is essential for building performant, reliable APIs. |
| Synapse +20% performance | You achieved this through HASH distribution (choosing the right distribution key to minimize data movement), date-based partitioning (enabling partition pruning for time-range queries), and pre-aggregation (materializing frequently queried summaries to avoid expensive runtime aggregations). |

---

*Last updated: August 2026*
