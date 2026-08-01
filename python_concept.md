# Python — Complete Interview Prep Guide
> Explained clearly for someone who uses Python daily — covers basics through advanced
> 4 years experience level: you should know all of this

---

## 1. Mutable vs Immutable — The #1 Python Interview Topic

This is the most frequently asked Python interview question because it affects how you write functions, how you debug weird bugs, and how you think about data in Python. If you get this wrong, everything else suffers.

### What It Means

When we say an object is **immutable**, we mean that once it's created, the VALUE stored at that memory address CANNOT be changed. You can assign the variable to a NEW object, but the original object in memory stays the same forever. Integers, floats, strings, tuples, booleans, and frozensets are all immutable.

When we say an object is **mutable**, we mean the VALUE stored at that memory address CAN be modified directly. The object changes in place without creating a new object. Lists, dicts, sets, and instances of your own classes are all mutable.

**Immutable** = once created, value CANNOT change in memory:
`int`, `float`, `str`, `tuple`, `bool`, `frozenset`

**Mutable** = value CAN change in place:
`list`, `dict`, `set`, custom class instances

### Why It Matters — The Aliasing Trap

The biggest practical consequence of mutability is what happens when two variables point to the same object. With immutable objects, there's no risk — even if you "change" one variable, it just points to a new object, and the other variable is unaffected. But with mutable objects, modifying through one variable changes what the other variable sees too, because they're both looking at the same underlying object.

```python
# Immutable (string):
a = "hello"
b = a          # b points to same object
a = "world"    # a now points to NEW object
print(b)       # "hello" -- unchanged

# Mutable (list):
a = [1, 2, 3]
b = a          # b points to SAME list
a.append(4)    # modifies list IN PLACE
print(b)       # [1, 2, 3, 4] -- b sees the change!
```

In the string example, `a = "world"` doesn't modify the string "hello" — it creates a brand new string "world" and makes `a` point to it. The variable `b` still points to the original "hello" object. But in the list example, `a.append(4)` actually modifies the list object that both `a` and `b` are pointing to. There's only ONE list in memory, and both variables see the change.

### Function Arguments

This aliasing behavior is critical when passing arguments to functions. Python doesn't copy objects when passing them to functions — it passes references to the same objects. So if a function modifies a mutable argument, the original variable outside the function is also affected.

```python
def modify(lst, num):
    lst.append(100)    # modifies original (mutable)
    num = num + 1      # creates new int (immutable), original unchanged

my_list = [1, 2, 3]
my_num = 5
modify(my_list, my_num)
print(my_list)   # [1, 2, 3, 100]
print(my_num)    # 5
```

Inside the function, `lst` is not a copy — it's the same list object as `my_list`. When you call `lst.append(100)`, you're appending to the original list. But `num` is an integer (immutable). `num = num + 1` creates a new integer object (6) and makes the local variable `num` point to it. The original `my_num` variable outside the function still points to 5.

Python passes the object reference. For mutable objects, in-place changes affect the original.
For immutable objects, "changes" create new objects — original untouched.

### Default Argument Trap

This is one of the most famous Python gotchas. When you use a mutable object as a default argument, Python creates that default object ONCE when the function is defined, not each time the function is called. So every call that uses the default shares the same list object.

```python
# BUG:
def add_item(item, lst=[]):
    lst.append(item)
    return lst
add_item("a")  # ['a']
add_item("b")  # ['a', 'b']  <-- same list reused!

# FIX:
def add_item(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst
```

The fix uses None as the default (None is immutable and safe) and creates a new list inside the function body each time it's needed. This ensures each call gets its own fresh list.

### Shallow Copy vs Deep Copy

When you need to copy a mutable object to avoid aliasing, you have two choices, and understanding the difference is crucial for nested data structures.

A **shallow copy** creates a new outer container but the items inside are still references to the same objects. A **deep copy** recursively copies everything — the container AND all items at every level of nesting.

```python
import copy
original = [[1, 2], [3, 4]]

shallow = original.copy()       # new outer list, inner lists SHARED
shallow[0].append(99)
print(original)   # [[1, 2, 99], [3, 4]] -- affected!

deep = copy.deepcopy(original)  # everything independent
deep[0].append(88)
print(original)   # [[1, 2, 99], [3, 4]] -- NOT affected
```

The shallow copy created a new outer list, so `shallow` and `original` are different list objects. But the inner lists `[1, 2]` and `[3, 4]` are still shared — both `original[0]` and `shallow[0]` point to the same inner list. When you append 99 to `shallow[0]`, `original[0]` sees it too.

The deep copy recursively copies everything, so modifying `deep[0]` has no effect on `original[0]` — they're completely independent objects at every level.

**Rule of thumb:** Shallow copy is fine for flat structures (list of integers, list of strings — immutable items that can't be changed in place). Deep copy is needed for nested structures (list of lists, list of dicts — mutable items that share references).

---

## 2. Data Structures — When to Use What

Choosing the right data structure is the foundation of efficient programming. Each Python data structure has different strengths, and knowing WHEN to use which one is more important than knowing HOW to use them.

### Lists — Ordered, Mutable, Duplicates OK

A list is Python's general-purpose ordered collection. Under the hood, it's a dynamic array — a contiguous block of pointers in memory. This means accessing any element by index is instant (O(1)), but inserting or deleting at the beginning is slow because every element after the insertion point must be shifted.

```python
fruits = ["apple", "banana", "cherry"]
fruits.append("date")        # O(1) -- end
fruits.insert(0, "avocado")  # O(n) -- shifts everything
fruits.pop()                 # O(1) -- end
fruits.pop(0)                # O(n) -- shifts everything
fruits.remove("banana")     # O(n) -- searches
"cherry" in fruits           # O(n) -- scans
fruits[1]                    # O(1) -- index
```

Under the hood: dynamic array (contiguous pointers), NOT a linked list. When the array is full, Python allocates a new, larger array and copies everything over. The amortized cost of append is O(1) even though occasional resizes are O(n).

**Use lists when:** You need an ordered collection, you'll mostly access by index or iterate through all elements, and you primarily add/remove from the end. Lists are the default choice — use them unless you have a reason to use something else.

### Tuples — Ordered, Immutable, Duplicates OK

Tuples look like lists but can't be modified after creation. This immutability gives them two important properties: they can be used as dictionary keys (lists can't), and they signal to the reader "this data is fixed — it shouldn't change."

```python
point = (3, 7)
single = (42,)    # trailing comma needed!

# Why tuples:
# 1. Signal "this data is fixed"
# 2. Can be dict keys (lists can't)
# 3. Slightly faster than lists
```

Tuples are also used for returning multiple values from a function (`return x, y` creates a tuple), for unpacking assignments (`a, b = 1, 2`), and as records when you need a lightweight, immutable container.

### Dicts — Key-Value, Ordered (3.7+)

Dictionaries are Python's hash map implementation. They store key-value pairs and provide O(1) average-case lookups, insertions, and deletions — making them one of the most efficient data structures available. Since Python 3.7, dicts maintain insertion order (the order you add items is the order you get when iterating).

The O(1) performance comes from hashing: Python computes a hash of the key, uses that hash to calculate a position in an internal array, and stores/retrieves the value at that position. This is why dict keys must be hashable (immutable) — if a key's hash could change after insertion, the dict wouldn't be able to find it again.

```python
user = {"name": "Vishal", "role": "Engineer"}
user["name"]                   # O(1)
user.get("salary", 0)         # O(1), no KeyError
user["location"] = "Noida"    # O(1) insert
del user["role"]               # O(1)
"name" in user                 # O(1) -- checks KEYS

for key, value in user.items():
    print(f"{key}: {value}")
```

**defaultdict** automatically creates a default value for missing keys, eliminating the need to check "if key not in dict" before using it:

```python
from collections import defaultdict
word_count = defaultdict(int)
for word in words:
    word_count[word] += 1    # no KeyError on first access
```

Without defaultdict, the first time you encounter a new word, `word_count[word]` would raise a KeyError because the key doesn't exist yet. defaultdict(int) automatically creates the key with a default value of 0 (since int() returns 0).

**Counter** is a specialized dict for counting things:

```python
from collections import Counter
c = Counter("abracadabra")   # {'a': 5, 'b': 2, ...}
c.most_common(3)
```

### Sets — Unordered, No Duplicates

Sets are like dicts with only keys (no values). They use the same hashing mechanism, so lookups are O(1). Sets automatically remove duplicates, and they support mathematical set operations like intersection, union, and difference.

```python
tags = {"python", "flask", "python"}   # duplicate removed
tags.add("docker")      # O(1)
"python" in tags         # O(1) -- fast!

a = {1, 2, 3, 4}
b = {3, 4, 5, 6}
a & b    # {3, 4}        intersection
a | b    # {1,2,3,4,5,6} union
a - b    # {1, 2}        difference
```

**Use sets when:** You need to check membership frequently (is this element in the collection?), you need to eliminate duplicates, or you need set math (intersection, union). Converting a list to a set and back is a common pattern for deduplication: `unique = list(set(items))` — though this loses ordering. To preserve order, use `list(dict.fromkeys(items))`.

### Deque — Fast at Both Ends

Python's list is fast at the right end (append, pop) but slow at the left end (insert(0), pop(0)) because shifting all elements is O(n). The deque (double-ended queue) from the collections module solves this — it's O(1) at BOTH ends.

```python
from collections import deque
dq = deque([1, 2, 3])
dq.append(4)        # O(1) right
dq.appendleft(0)    # O(1) left  (list is O(n) here!)
dq.pop()             # O(1) right
dq.popleft()         # O(1) left  (list is O(n) here!)
```

Under the hood, deque is implemented as a doubly-linked list of fixed-size blocks, which is why it's efficient at both ends but O(n) for random access (`dq[500]` requires traversing blocks).

**Use deque for:** Queues (FIFO — add right, remove left), BFS in graph algorithms, sliding window problems, and any situation where you need to add/remove from both ends efficiently.

### Time Complexity Cheat Sheet

Understanding these complexities tells you which operations are fast and which are slow for each data structure. O(1) means instant regardless of size. O(n) means the time grows linearly with the number of elements.

| Operation | List | Dict | Set |
|-----------|------|------|-----|
| Access by index | O(1) | -- | -- |
| Lookup/search | O(n) | O(1) | O(1) |
| Insert end | O(1) | O(1) | O(1) |
| Insert start | O(n) | -- | -- |
| Delete | O(n) | O(1) | O(1) |

The key takeaway: if you need to search or check membership frequently, use a dict or set (O(1)) instead of a list (O(n)). This is the single most impactful optimization in Python programming.

---

## 3. Comprehensions and Generators

### List Comprehension

List comprehensions are a concise way to create lists by applying an expression to each item in an iterable, optionally filtering items with a condition. They're more readable and faster than equivalent for-loop code because the iteration happens at C speed inside Python's internals.

```python
squares = [x**2 for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
```

The general pattern is `[expression for item in iterable if condition]`. The condition is optional. You can also nest comprehensions for working with multi-dimensional data, though more than one level of nesting hurts readability: `[cell for row in matrix for cell in row]` flattens a 2D matrix.

### Dict and Set Comprehensions

The same concept works for dicts and sets, just with different brackets:

```python
word_lens = {w: len(w) for w in ["hello", "world"]}
unique_lens = {len(w) for w in ["hello", "world", "hi"]}
```

Dict comprehensions use `{key: value for ...}` and are great for transforming or inverting dictionaries. Set comprehensions use `{value for ...}` and automatically handle deduplication.

### Generator Expression — Lazy, Memory Efficient

A generator expression looks exactly like a list comprehension but uses parentheses instead of brackets. The crucial difference is that it doesn't create the entire result in memory at once — it produces values one at a time, on demand (lazily). This is essential when working with large datasets.

```python
# List comprehension -- entire list in memory:
squares = [x**2 for x in range(1_000_000)]

# Generator expression -- one at a time, almost zero memory:
squares = (x**2 for x in range(1_000_000))
total = sum(x**2 for x in range(1_000_000))  # efficient
```

With the list comprehension, Python creates a list of 1 million integers in memory, which takes ~8 MB. With the generator expression, Python computes each square one at a time, passes it to `sum()`, and discards it before computing the next. Memory usage stays constant regardless of the input size.

**Use generators when:** You're processing large datasets, you only need to iterate through the values once, or you're chaining multiple processing steps (pipeline pattern). Use list comprehensions when you need random access to the results, need to iterate multiple times, or the dataset is small.

---

## 4. Functions — Deep Dive

### *args and **kwargs

These let a function accept any number of arguments. `*args` collects extra positional arguments into a tuple, and `**kwargs` collects extra keyword arguments into a dictionary. This is how Python achieves flexible function signatures.

```python
def func(*args, **kwargs):
    print(args)     # tuple of positional args
    print(kwargs)   # dict of keyword args

func(1, 2, name="Vishal")
# (1, 2)
# {'name': 'Vishal'}
```

`*args` and `**kwargs` are conventions — you could name them `*numbers` and `**options`, but `*args`/`**kwargs` is what everyone expects. They're commonly used in decorator wrappers (to accept any function's arguments) and in functions that delegate to other functions.

### Unpacking

The `*` and `**` operators also work in reverse — they unpack sequences and dicts into function arguments:

```python
nums = [1, 2, 3]
add(*nums)           # add(1, 2, 3)

config = {"a": 1, "b": 2}
func(**config)       # func(a=1, b=2)
```

This is incredibly useful when you have data in a collection and need to pass it as individual arguments to a function.

### Lambda

Lambda functions are small, anonymous, single-expression functions. They're most useful as throwaway functions for `sorted()`, `filter()`, and `map()`:

```python
sorted(users, key=lambda u: u["age"])
evens = list(filter(lambda x: x % 2 == 0, numbers))
```

Lambdas can only contain a single expression (not statements like `if-else` blocks or assignments). If your lambda is getting complex, use a regular `def` function instead — readability matters more than conciseness.

### First-Class Functions

In Python, functions are objects. You can assign them to variables, pass them as arguments to other functions, return them from functions, and store them in data structures. This is what "first-class" means — functions are treated like any other value.

```python
# Assign to variable:
op = len; op("hello")  # 5

# Pass as argument:
sorted(names, key=len)

# Return from function:
def make_multiplier(n):
    return lambda x: x * n
double = make_multiplier(2)
double(5)  # 10
```

This concept is the foundation of decorators, callbacks, and functional programming patterns in Python.

### Closures — Functions That Remember

A closure is an inner function that "remembers" the variables from its enclosing function, even after that enclosing function has finished executing. The inner function "closes over" the variables it references.

```python
def make_counter():
    count = 0
    def increment():
        nonlocal count    # use outer variable, don't create new local
        count += 1
        return count
    return increment

counter = make_counter()
counter()  # 1
counter()  # 2
counter()  # 3
```

When `make_counter()` returns, normally the local variable `count` would be garbage collected. But because `increment` references `count`, Python keeps it alive as long as `increment` exists. Each call to `counter()` accesses and modifies the same `count` variable.

**Without `nonlocal`:** `count += 1` would try to create a new local variable (because assignment creates a local variable in Python), and it would fail with `UnboundLocalError` because you'd be reading `count` before the local version was assigned.

Closures are the mechanism that makes decorators work — the wrapper function closes over the original function.

### map, filter, reduce

These are functional programming tools that apply functions to iterables:

```python
list(map(str.upper, ["hello", "world"]))     # ['HELLO', 'WORLD']
list(filter(lambda x: x > 0, [-1, 2, -3]))  # [2]

from functools import reduce
reduce(lambda acc, x: acc + x, [1,2,3,4])   # 10
```

`map` applies a function to every element. `filter` keeps only elements where the function returns True. `reduce` accumulates a result by applying a function cumulatively (left to right).

List comprehensions are usually preferred for readability in Python — they're considered more "Pythonic":
```python
[s.upper() for s in ["hello", "world"]]
[x for x in [-1, 2, -3] if x > 0]
```

However, `map` can be slightly faster than a list comprehension when using a built-in function (like `str.upper`) because it avoids creating a lambda or calling a Python function per element.

---

## 5. Decorators

Decorators are one of Python's most powerful features and a very common interview topic. They let you modify or extend a function's behavior without changing its source code.

### What a Decorator Does

At its core, a decorator is a function that takes a function as input and returns a new function that usually wraps the original with some additional behavior. The `@` syntax is just syntactic sugar (a shortcut).

```python
@my_decorator
def func(): pass
# Same as: func = my_decorator(func)
```

When you write `@my_decorator` above a function, Python calls `my_decorator(func)` and replaces the original `func` with whatever `my_decorator` returns. This returned value is usually a wrapper function that calls the original function plus some extra logic.

### Building One

Here's a practical decorator that measures how long a function takes to execute:

```python
import time
from functools import wraps

def timer(func):
    @wraps(func)    # preserves original name/docstring
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time()-start:.4f}s")
        return result
    return wrapper

@timer
def slow(): time.sleep(1)
slow()  # "slow took 1.0012s"
```

The `@wraps(func)` decorator from functools is important — without it, the wrapped function's `__name__` would be "wrapper" instead of "slow", and its docstring would be lost. `@wraps` copies the original function's metadata onto the wrapper.

The `*args, **kwargs` in the wrapper signature means the decorator works with ANY function regardless of its arguments. The wrapper accepts whatever arguments the original function accepts, passes them through, captures the result, and returns it.

### Decorators With Arguments

Sometimes you want to configure the decorator itself — like specifying how many times to repeat, or what log level to use. This requires an extra layer of nesting: a function that returns the decorator, which returns the wrapper.

```python
def repeat(n):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def greet(): print("Hello!")
greet()  # prints "Hello!" three times
```

Three levels of nesting: `repeat(3)` is called immediately and returns `decorator`. Then `decorator` wraps `greet` into `wrapper`. This is confusing at first, but the pattern is always the same — if you need to pass arguments to a decorator, add one outer function.

### Built-in @lru_cache — Memoization

`lru_cache` is a built-in decorator that caches (remembers) the return values of a function based on its arguments. If you call the function with the same arguments again, it returns the cached result instead of recomputing. This turns exponentially slow recursive functions into fast ones.

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def fibonacci(n):
    if n < 2: return n
    return fibonacci(n-1) + fibonacci(n-2)

fibonacci(100)  # instant (without cache: impossibly slow)
```

Without caching, `fibonacci(100)` would make about 2^100 function calls (the same subproblems computed over and over). With caching, each unique input is computed only once and cached — total of about 100 calls. LRU stands for "Least Recently Used" — when the cache is full, the least recently used entries are evicted.

### Practical Decorators

Decorators are used extensively in frameworks and production code. Here's a retry decorator that automatically retries a function if it raises an exception:

```python
# Retry on failure:
def retry(max_attempts=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try: return func(*args, **kwargs)
                except Exception:
                    if attempt == max_attempts - 1: raise
        return wrapper
    return decorator

@retry(max_attempts=3)
def call_api(): ...
```

Other common real-world decorators: `@app.route()` in Flask (registers URL handlers), `@login_required` (checks authentication), `@property` (makes a method behave like an attribute), `@staticmethod` / `@classmethod` (changes method binding).

---

## 6. OOP — Complete Guide

Object-Oriented Programming is how Python organizes code into reusable, structured components. A class is a blueprint for creating objects, and an object is a specific instance of that blueprint with its own data.

### Basic Class

```python
class Employee:
    company = "Tech Mahindra"    # class variable (shared)

    def __init__(self, name, role, salary):
        self.name = name         # instance variable (unique)
        self.role = role
        self.salary = salary

    def annual_salary(self):
        return self.salary * 12

    def __str__(self):
        return f"{self.name} ({self.role})"

    def __repr__(self):
        return f"Employee('{self.name}', '{self.role}', {self.salary})"
```

**Class variable vs instance variable:** `company` is shared by ALL instances — changing it affects every employee. Instance variables (set with `self.something` in `__init__`) are unique to each object. This distinction matters because accidentally using a mutable class variable (like a list) means all instances share and modify the same list.

**`__init__`** is NOT a constructor — it's an initializer. The actual constructor is `__new__` (which allocates memory). `__init__` sets up the initial state of an already-created object. But for practical purposes, think of `__init__` as "what happens when you create a new instance."

### Inheritance and super()

Inheritance lets one class (child) inherit attributes and methods from another class (parent). The child can add new behavior or override existing behavior. This is how you reuse code without duplicating it.

```python
class Animal:
    def __init__(self, name):
        self.name = name
    def speak(self):
        raise NotImplementedError

class Dog(Animal):
    def speak(self):
        return f"{self.name}: Woof!"

class Manager(Employee):
    def __init__(self, name, role, salary, team_size):
        super().__init__(name, role, salary)  # MUST call parent init
        self.team_size = team_size
```

`super()` calls the parent class's method. In `Manager.__init__`, `super().__init__(name, role, salary)` calls `Employee.__init__` to set up the base employee attributes (name, role, salary), then `self.team_size = team_size` adds the manager-specific attribute. Without `super()`, the parent's `__init__` wouldn't run, and the Manager object would be missing name, role, and salary.

### The 4 Pillars (Interview Answers)

Interviewers love asking "What are the 4 pillars of OOP?" You need to explain each one clearly with examples, not just list them.

**Encapsulation** is the practice of bundling data (attributes) and the methods that operate on that data into a single unit (class), and controlling access to the internal state. The idea is that the outside world shouldn't directly poke at an object's internal data — it should go through methods that validate and control access.

```python
class Account:
    def __init__(self, balance):
        self._balance = balance     # convention: don't access from outside
    def deposit(self, amount):
        if amount > 0: self._balance += amount
```

The `_balance` prefix is a convention (not enforcement) that says "this is private — don't touch it directly." The `deposit` method is the controlled interface — it validates that the amount is positive before modifying the balance. Without encapsulation, any code could do `account._balance = -1000`, bypassing validation.

Python uses name conventions (`_private`, `__mangled`) rather than strict access control (like Java's `private` keyword). This is "we're all consenting adults" philosophy — Python trusts you to follow conventions.

**Inheritance** lets a child class reuse and extend a parent class's code. Dog inherits Animal's `__init__` and adds its own `speak` implementation. This avoids duplicating code — if 10 animal types all need a name, you define it once in Animal.

**Polymorphism** means "same interface, different behavior." You can call `.speak()` on any animal — Dog says "Woof", Cat says "Meow", Snake says "Hiss" — without knowing or caring which type it is. Your code works with the abstract concept (Animal) rather than specific implementations.

```python
def make_speak(animal):
    print(animal.speak())  # works for Dog, Cat, anything with .speak()
```

Python achieves polymorphism through "duck typing" — if an object has a `.speak()` method, you can call it. You don't need to check the type or have a common base class. "If it walks like a duck and quacks like a duck, it's a duck."

**Abstraction** defines WHAT something does without specifying HOW. An abstract class provides a contract — "any subclass MUST implement these methods" — without providing the implementation.

```python
from abc import ABC, abstractmethod
class Database(ABC):
    @abstractmethod
    def connect(self): pass
    @abstractmethod
    def execute(self, query): pass
# Can't instantiate Database directly -- must implement all abstract methods
```

You can't create a `Database()` object directly — it's abstract. You must create a concrete subclass (like `PostgreSQL(Database)`) that implements `connect()` and `execute()`. This ensures that all database implementations have a consistent interface.

### Multiple Inheritance and MRO

Python supports multiple inheritance — a class can inherit from more than one parent. This raises the question: if two parents both have a method with the same name, which one gets called?

```python
class A:
    def greet(self): return "A"
class B:
    def greet(self): return "B"
class C(A, B):
    pass

c = C()
c.greet()     # "A" -- Python checks C -> A -> B -> object (left to right)
C.__mro__     # (C, A, B, object)
```

MRO (Method Resolution Order) is the algorithm Python uses to determine which parent's method to call. It uses a system called C3 linearization that basically goes left to right through the inheritance chain, depth-first but avoiding diamonds. You can inspect the order with `ClassName.__mro__`.

In practice, multiple inheritance is used cautiously. "Mixins" — small classes that add a single specific behavior — are the accepted pattern. Inheriting from two large, complex classes usually leads to confusion.

### @classmethod vs @staticmethod

These are two special method types that change what the method receives as its first argument.

```python
class Employee:
    raise_rate = 1.05

    @classmethod
    def from_string(cls, s):    # gets class, not instance
        name, salary = s.split("-")
        return cls(name, "Engineer", int(salary))

    @staticmethod
    def is_workday(day):        # gets nothing
        return day.weekday() < 5

emp = Employee.from_string("Vishal-80000")  # alternative constructor
```

**@classmethod** receives the class itself (`cls`) as the first argument instead of an instance (`self`). This is primarily used for "alternative constructors" — different ways to create an instance. `from_string` creates an Employee from a string instead of from separate arguments. It uses `cls(...)` instead of `Employee(...)` so that subclasses inherit the factory method correctly.

**@staticmethod** receives nothing — no `self`, no `cls`. It's essentially a regular function that belongs to the class logically but doesn't need access to the instance or the class. It's used for utility functions that are related to the class's domain but don't need any class state.

### Dunder Methods — Customizing Object Behavior

Dunder (double-underscore) methods let you define how your objects behave with Python's built-in operations and syntax. When you write `a + b`, Python actually calls `a.__add__(b)`. When you write `len(obj)`, Python calls `obj.__len__()`. By implementing these methods, you can make your custom objects work naturally with Python's syntax.

```python
class Vector:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __repr__(self):       return f"Vector({self.x}, {self.y})"
    def __str__(self):        return f"({self.x}, {self.y})"
    def __add__(self, other): return Vector(self.x+other.x, self.y+other.y)
    def __eq__(self, other):  return self.x==other.x and self.y==other.y
    def __len__(self):        return int((self.x**2 + self.y**2)**0.5)
    def __getitem__(self, i): return (self.x, self.y)[i]
    def __hash__(self):       return hash((self.x, self.y))
    def __call__(self):       return (self.x, self.y)

v1 = Vector(1, 2)
v2 = Vector(3, 4)
print(v1 + v2)   # (4, 6)
v1()              # (1, 2) -- callable object
```

**Key dunders and when Python calls them:**

| Method | Triggered By | What It's For |
|--------|-------------|---------------|
| `__init__` | `MyClass()` | Initialize a new instance with starting values |
| `__str__` | `print(obj)`, `str(obj)` | Human-readable string (for users, logs) |
| `__repr__` | debugger, `repr(obj)`, REPL | Unambiguous string (for developers, debugging) |
| `__eq__` | `==` | Define when two instances are considered equal |
| `__lt__`, `__gt__` | `<`, `>` | Enable comparison and sorting |
| `__hash__` | `hash()`, dict key, set | Make instances usable as dict keys or in sets |
| `__len__` | `len()` | Define what "length" means for your object |
| `__getitem__` | `obj[i]` | Make your object subscriptable (like a list) |
| `__iter__` | `for x in obj` | Make your object iterable in for loops |
| `__call__` | `obj()` | Make your object callable like a function |
| `__enter__`, `__exit__` | `with obj` | Make your object work with context managers |
| `__add__` | `+` | Define addition behavior |

### `__init__` vs `__new__`

`__new__` is the actual constructor — it allocates memory and creates the object. `__init__` is the initializer — it receives the already-created object and sets its attributes. In normal usage, you only override `__init__`. `__new__` is overridden only in special cases like singletons (ensuring only one instance exists) or when creating instances of immutable types.

```python
class Singleton:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

a = Singleton()
b = Singleton()
a is b  # True -- same object
```

`__new__` checks if an instance already exists. If so, it returns the existing one. If not, it creates a new one and stores it. Every subsequent `Singleton()` call returns the same object.

---

## 7. Iterators and Generators

Iterators and generators are how Python handles sequences of data efficiently. They're the machinery behind every `for` loop, and understanding them unlocks memory-efficient processing of large datasets.

### The Iterator Protocol

Every time you write a `for` loop in Python, behind the scenes, Python is using the iterator protocol. It calls `iter()` on the object to get an iterator, then repeatedly calls `next()` on that iterator to get values one at a time until `StopIteration` is raised.

```python
nums = [1, 2, 3]
it = iter(nums)     # get iterator
next(it)            # 1
next(it)            # 2
next(it)            # 3
next(it)            # StopIteration
```

This is exactly what `for num in nums` does — it just hides the `iter()` and `next()` calls and catches `StopIteration` automatically.

### Custom Iterator

To make your own class iterable, you implement two dunder methods: `__iter__` (returns the iterator object, usually `self`) and `__next__` (returns the next value or raises `StopIteration` when done).

```python
class Countdown:
    def __init__(self, start):
        self.current = start
    def __iter__(self):
        return self
    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        self.current -= 1
        return self.current + 1

for n in Countdown(5): print(n)  # 5, 4, 3, 2, 1
```

### Generators — Easy Iterators

Generators are the easy way to create iterators. Instead of writing a class with `__iter__` and `__next__`, you write a function with `yield`. Python automatically handles all the iterator protocol details.

```python
def countdown(n):
    while n > 0:
        yield n    # pause, return value, resume on next call
        n -= 1

for n in countdown(5): print(n)  # 5, 4, 3, 2, 1
```

The `yield` keyword is the magic. When Python hits `yield`, it pauses the function, returns the yielded value to the caller, and remembers exactly where it was — which line it was on, what all the local variables were, everything. When `next()` is called again, the function resumes from exactly where it paused and continues until it hits the next `yield`.

This is fundamentally different from `return`: `return` ends the function permanently. `yield` suspends it temporarily and can resume.

### Why Generators Matter — Memory Efficiency

The killer feature of generators is memory efficiency. A generator produces values one at a time and discards each value after it's consumed. This means you can process gigabytes of data with only kilobytes of memory.

```python
# BAD: loads entire file into memory
lines = open("10gb.txt").readlines()

# GOOD: one line at a time
def read_lines(path):
    with open(path) as f:
        for line in f:
            yield line.strip()

for line in read_lines("10gb.txt"):
    if "ERROR" in line: print(line)
```

The list approach loads all 10 GB into memory, likely crashing your program. The generator approach reads one line, processes it, discards it, then reads the next. Memory usage stays constant at a few kilobytes regardless of file size.

### Generator Pipeline — Chain Processing

You can chain multiple generators together, where each one processes and passes data to the next. Only one item exists in memory at any point — each generator processes and yields one item before pulling the next from the previous generator.

```python
def read_logs(path):
    with open(path) as f:
        for line in f: yield line.strip()

def filter_errors(lines):
    for line in lines:
        if "ERROR" in line: yield line

def extract_timestamp(lines):
    for line in lines:
        yield line.split(" ")[0]

# Chain -- only ONE line in memory at any point:
logs = read_logs("app.log")
errors = filter_errors(logs)
timestamps = extract_timestamp(errors)
for ts in timestamps: print(ts)
```

This is the same concept as Unix pipes: `cat app.log | grep ERROR | cut -d' ' -f1`. Each step processes one item and passes it to the next step. Data flows through the pipeline one item at a time, not in batches.

This is directly relevant to your data engineering work — Spark and Kafka use the same pipeline concept, just distributed across multiple machines.

---

## 8. Exception Handling

Exception handling is how Python deals with errors — situations where something goes wrong during execution. Instead of crashing immediately, you can catch the error, handle it gracefully, and continue running.

### Full Pattern

Python's exception handling has four parts, each with a specific purpose:

```python
try:
    result = risky_operation()
except ValueError as e:
    print(f"Bad value: {e}")
except (TypeError, KeyError) as e:
    print(f"Other: {e}")
except Exception as e:
    print(f"Unexpected: {e}")
else:
    print(f"Success: {result}")   # only if NO exception
finally:
    cleanup()                      # ALWAYS runs
```

**try:** Contains the code that might fail. If an exception occurs, Python immediately jumps to the matching except block.
**except:** Catches specific exception types. Python checks each except block in order and executes the first one that matches. Always catch specific exceptions first (ValueError) before general ones (Exception). Catching bare `Exception` as a fallback is OK but catching `BaseException` is not (it would catch SystemExit and KeyboardInterrupt, which you don't want).
**else:** Runs ONLY if the try block completed without any exception. This is useful for code that should run on success but shouldn't be inside the try block (because you don't want to accidentally catch its exceptions).
**finally:** Runs NO MATTER WHAT — whether an exception occurred, was caught, or wasn't caught. Used for cleanup that must happen regardless: closing files, releasing locks, disconnecting from databases.

### Custom Exceptions

When built-in exceptions don't adequately describe your error, create custom ones. This makes error handling more precise — callers can catch your specific exception without catching unrelated errors.

```python
class InsufficientFundsError(Exception):
    def __init__(self, balance, amount):
        super().__init__(f"Cannot withdraw {amount}: only {balance} available")
        self.balance = balance
        self.amount = amount
```

Always inherit from `Exception`, not `BaseException`. `BaseException` includes `SystemExit`, `KeyboardInterrupt`, and `GeneratorExit` — system-level events that shouldn't be caught by normal error handling. By inheriting from `Exception`, your custom exceptions are caught by `except Exception` but won't interfere with system events.

Adding attributes (like `balance` and `amount`) lets the caller inspect the error details and potentially recover — for example, showing the user how much they can actually withdraw.

### EAFP vs LBYL — Two Philosophies

Python community favors "Easier to Ask Forgiveness than Permission" (EAFP) over "Look Before You Leap" (LBYL). The idea is: instead of checking whether something will work before doing it, just try it and handle the failure if it occurs.

```python
# LBYL (Look Before You Leap):
if "key" in d: value = d["key"]

# EAFP (Ask Forgiveness -- Pythonic):
try: value = d["key"]
except KeyError: value = default

# Best for simple cases:
value = d.get("key", default)
```

EAFP is preferred in Python because: (1) in the common case where the key exists, it avoids the overhead of checking first, (2) it handles race conditions (the key could be deleted between the check and the access), and (3) it's often cleaner code. But for simple cases, built-in methods like `dict.get()` are best.

---

## 9. Context Managers

Context managers ensure that setup and cleanup code always runs, even if an error occurs. The most common example is file handling — you want to guarantee the file is closed, regardless of what happens while you're reading it.

```python
# Guarantees cleanup even on error:
with open("data.txt") as f:
    data = f.read()
# f.close() called automatically
```

Without the `with` statement, if an exception occurs between `f = open(...)` and `f.close()`, the file stays open (a resource leak). The `with` statement guarantees that `__exit__` (which calls `close()`) runs no matter what — even if the code inside raises an exception.

### Custom Context Manager with Decorator

The `contextmanager` decorator from contextlib lets you create context managers using a generator function, which is much simpler than implementing a class:

```python
from contextlib import contextmanager

@contextmanager
def timer(label):
    start = time.time()
    yield    # code inside "with" runs here
    print(f"{label}: {time.time()-start:.2f}s")

with timer("query"):
    result = db.execute("SELECT ...")
```

Everything before `yield` is the setup (enters the context). The `yield` is where the `with` block's body executes. Everything after `yield` is the cleanup (exits the context). If you need to handle exceptions during cleanup, wrap the yield in a try/finally.

### Custom Context Manager with Class

For more control, implement `__enter__` and `__exit__` dunder methods:

```python
class DBConnection:
    def __init__(self, conn_str):
        self.conn_str = conn_str
    def __enter__(self):
        self.conn = connect(self.conn_str)
        return self.conn
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        return False  # don't suppress exceptions
```

`__enter__` runs when entering the `with` block and its return value is assigned to the variable after `as`. `__exit__` runs when leaving the `with` block — always, even on exception. The three arguments (`exc_type`, `exc_val`, `exc_tb`) contain exception info if one occurred, or are all None if everything went fine. Returning `False` (or nothing) means exceptions propagate normally. Returning `True` would suppress the exception (rarely wanted).

---

## 10. GIL, Threading, Multiprocessing, and Async

This topic is critical for understanding Python's concurrency model and why certain things are fast or slow. It's a very popular interview question for experienced Python developers.

### The GIL — Global Interpreter Lock

The GIL is a mutex (lock) in CPython (the standard Python interpreter) that allows only ONE thread to execute Python bytecode at any given time. Even if your computer has 16 CPU cores, only one thread can run Python code at a time.

This exists because CPython's memory management (reference counting) is not thread-safe. If two threads simultaneously modified a reference count, it could get corrupted, leading to memory leaks or crashes. The GIL is a simple solution: just let one thread run at a time, and all reference count operations are safe.

### What This Means for Your Code

The GIL only blocks Python bytecode execution. It does NOT block I/O operations. When a thread is waiting for a network response, a disk read, or a database query, it releases the GIL, allowing other threads to run. This is why the GIL's impact depends on whether your work is I/O-bound or CPU-bound.

**IO-bound (network, disk, DB) — threading works great:**
While thread 1 waits for a network response (GIL released), thread 2 can run Python code. 10 threads making API calls run almost 10x faster than one thread, because 90% of the time is spent waiting (GIL released), not computing (GIL held).

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=10) as pool:
    results = list(pool.map(fetch_url, urls))
```

**CPU-bound (computation) — threading doesn't help, use multiprocessing:**
If your code is doing heavy computation (math, data processing, encryption), the GIL prevents true parallel execution. 10 threads doing CPU work will NOT be faster than 1 thread — they'll just take turns, one at a time.

The solution is multiprocessing: each process has its OWN Python interpreter with its OWN GIL. Multiple processes truly run in parallel on multiple CPU cores.

```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(heavy_compute, data_chunks))
```

The trade-off: processes don't share memory (each has its own copy), so passing data between processes involves serialization (pickling), which adds overhead. Use multiprocessing when the computation is heavy enough to outweigh this overhead.

### async/await — Cooperative Multitasking

Async is a third concurrency model that's different from both threading and multiprocessing. It uses a single thread with an event loop. Coroutines (async functions) cooperatively yield control when they hit an `await` (an I/O wait), allowing the event loop to switch to another coroutine. No GIL issue because there's only one thread. No context switching overhead because coroutines are lighter than threads.

```python
import asyncio
import aiohttp

async def fetch(session, url):
    async with session.get(url) as resp:
        return await resp.text()

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)

asyncio.run(main())
```

Async can handle 10,000+ concurrent connections on a single thread because the overhead per coroutine is tiny (a few hundred bytes of state) compared to threads (MB of stack space each).

**FastAPI uses asyncio** — that's why your endpoints can be `async def`. When one request is waiting for a database query, the event loop serves another request. This is how FastAPI achieves high throughput with minimal resources.

### Quick Decision Table

| Task Type | Use This | Why |
|------|-----|-----|
| API calls, DB queries, file I/O | `ThreadPoolExecutor` or `asyncio` | GIL is released during I/O waits, so threads or coroutines can run concurrently |
| Heavy computation (math, image processing) | `ProcessPoolExecutor` | Separate process = separate GIL = true parallel execution on multiple CPU cores |
| 1000+ concurrent network connections | `asyncio` | Single thread, minimal overhead per connection, handles massive concurrency efficiently |
| Simple scripts, small datasets | Just use synchronous code | Concurrency adds complexity; only use it when you need the performance |

---

## 11. Memory Management

Understanding how Python manages memory helps you write more efficient code and debug memory-related issues like memory leaks.

### Reference Counting — The First Line of Defense

Every Python object has an internal counter tracking how many variables (references) point to it. When you create a new reference to an object, the count goes up. When a reference is deleted or goes out of scope, the count goes down. When the count reaches zero, the object is immediately freed — no waiting, no garbage collection needed.

```python
a = [1, 2, 3]    # ref count = 1
b = a             # ref count = 2
del a             # ref count = 1
del b             # ref count = 0 -> freed immediately
```

This is why most Python objects are cleaned up immediately when they're no longer needed — reference counting handles 95% of memory management without any explicit action from the programmer.

### Circular References — The Problem

Reference counting has one weakness: circular references. When two objects reference each other, their reference counts never reach zero, even when no external code can access them.

```python
class Node:
    def __init__(self): self.next = None
a, b = Node(), Node()
a.next = b
b.next = a    # circular!
del a; del b
# Both still have ref count 1 (each references the other)
# Reference counting alone can't free them
```

After `del a; del b`, no code can access these objects, but their reference counts are both 1 (each referencing the other). Reference counting alone can't detect this — it would be a memory leak.

### Generational Garbage Collector — The Safety Net

Python's garbage collector (GC) supplements reference counting by detecting and cleaning up circular references. It periodically scans objects to find cycles (groups of objects that reference each other but are unreachable from outside).

The GC uses a generational approach based on the observation that most objects die young (temporary variables, intermediate calculations). It divides objects into three generations:

- **Gen 0 (young):** Newly created objects. Scanned very frequently because most objects are short-lived.
- **Gen 1 (middle-aged):** Objects that survived one Gen 0 scan. Scanned less often.
- **Gen 2 (old):** Long-lived objects that survived multiple scans. Rarely scanned because long-lived objects tend to stay alive.

This generational approach is efficient because scanning all objects every time would be slow for programs with millions of objects. By scanning young objects frequently and old objects rarely, the GC stays fast while still catching circular references.

### String Interning — An Optimization

Python caches (interns) small strings and integers to save memory. When you create a small string like "hello", Python checks if an identical string already exists in its intern cache. If so, it reuses the existing object instead of creating a new one.

```python
a = "hello"
b = "hello"
a is b    # True -- Python reuses the same small string object

a = "hello world!"
b = "hello world!"
a is b    # May be False -- not always interned
```

Simple strings (identifiers, small strings without special characters) are typically interned. Complex strings may or may not be, depending on the Python implementation and context.

**Important rule:** Always use `==` for string comparison (checks value equality). Only use `is` with `None` (which is a singleton — there's always exactly one None object). Using `is` for string comparison works sometimes (when strings happen to be interned) but fails unpredictably.

---

## 12. Dataclasses, Properties, and Slots

These are three important tools for creating classes that are clean, efficient, and well-structured.

### Dataclasses (3.7+)

Dataclasses automatically generate boilerplate methods (`__init__`, `__repr__`, `__eq__`) based on class attributes you define. They eliminate the tedious and error-prone task of writing these methods manually for classes that are primarily data containers.

```python
from dataclasses import dataclass, field

@dataclass
class Employee:
    name: str
    role: str
    salary: float
    skills: list = field(default_factory=list)
    # __init__, __repr__, __eq__ auto-generated!

emp = Employee("Vishal", "Engineer", 80000)
print(emp)  # Employee(name='Vishal', role='Engineer', salary=80000, skills=[])

@dataclass(frozen=True)  # immutable
class Point:
    x: float
    y: float
```

Note the `field(default_factory=list)` for the mutable default — this avoids the mutable default argument trap. Each instance gets its own fresh list. If you wrote `skills: list = []`, all instances would share the same list (the same bug as the function default argument trap).

`frozen=True` makes instances immutable — you can't change attributes after creation, and instances become hashable (usable as dict keys or in sets).

### Properties — Controlled Attribute Access

Properties let you define methods that behave like attributes. From the outside, you use `obj.radius` (simple attribute access), but internally, Python calls a method that can validate, compute, or restrict the value.

```python
class Circle:
    def __init__(self, radius):
        self._radius = radius

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        if value < 0: raise ValueError("Negative radius")
        self._radius = value

    @property
    def area(self):
        return 3.14159 * self._radius ** 2  # computed on access

c = Circle(5)
c.radius = 10     # calls setter with validation
print(c.area)     # computed, not stored
```

The `@property` decorator turns `radius()` into a read method that's called when you access `c.radius`. The `@radius.setter` decorator turns the setter method into a write method that's called when you assign `c.radius = 10`. This gives you validation (negative radius raises an error) while keeping the simple attribute syntax.

The `area` property is a computed property — it doesn't store a value but calculates it from `_radius` every time you access it. This ensures the area is always consistent with the current radius.

### __slots__ — Memory Optimization

By default, every Python instance stores its attributes in a `__dict__` dictionary. This is flexible (you can add any attribute at any time) but costs ~100 bytes per instance. When you have millions of instances, this adds up.

```python
class Regular:
    def __init__(self, x, y):
        self.x = x; self.y = y
# Each instance has __dict__ (~100 bytes overhead)

class Slotted:
    __slots__ = ('x', 'y')
    def __init__(self, x, y):
        self.x = x; self.y = y
# No __dict__, ~40% less memory per instance
# Can't add new attributes dynamically
```

`__slots__` tells Python exactly which attributes an instance will have. Python allocates a fixed-size struct instead of a dict, saving significant memory. The trade-off is that you lose the ability to add arbitrary attributes at runtime (`obj.new_attr = 42` would fail).

**Use when:** You have millions of instances of a simple class (like points in a game, nodes in a graph, or records from a data pipeline) and memory usage matters.

---

## 13. Modules, Packages, and Imports

Understanding how Python's import system works is essential for organizing code in professional projects.

### How Imports Work

```python
import os                          # access as os.path.join()
from os.path import join           # access as join()
from os.path import join as pjoin  # alias
from os import *                   # NEVER in production (namespace pollution)
```

When you `import os`, Python searches for the module in several locations (current directory, installed packages, standard library), loads it, executes its top-level code, and creates a module object that you access with `os.something`. The module is only loaded ONCE — subsequent imports reuse the cached module.

`from os import *` imports every public name from the module into your current namespace. This is dangerous because it can overwrite existing names silently (if `os` has a function named the same as your variable), and you lose track of where names came from.

### Module vs Package vs Library

**Module** = one `.py` file. It's the smallest unit of Python code organization. When you `import myfile`, you're importing a module.

**Package** = a directory containing an `__init__.py` file and other modules. The `__init__.py` file is what tells Python "this directory is a Python package, not just a folder." A package can contain sub-packages (nested directories with their own `__init__.py`).

**Library** = an informal term for a collection of packages that you install and use. Flask, requests, pandas — these are libraries, each containing multiple packages and modules.

### `__name__ == "__main__"`

This is one of the most common Python patterns and it controls whether code runs when the file is executed directly vs. when it's imported by another file.

```python
if __name__ == "__main__":
    # Runs only when executed directly: python myfile.py
    # Does NOT run when imported by another file
    main()
```

When Python runs a file directly, it sets that file's `__name__` variable to `"__main__"`. When the file is imported by another file, `__name__` is set to the module's name instead. This lets you put test code, demo code, or the entry point inside the guard, keeping it out of the way when the module is used as a library.

### `__init__.py` — Package Initialization

`__init__.py` runs when the package is imported. It can be empty (just marking the directory as a package) or it can define what names are available when someone imports the package.

```python
# mypackage/__init__.py
from .module_a import ImportantClass
from .module_b import useful_function

# Users can now do: from mypackage import ImportantClass
```

By importing names in `__init__.py`, you create a cleaner public API. Users don't need to know your internal module structure — they just import from the package directly.

---

## 14. Type Hinting

Type hints tell both humans and tools what types a function expects and returns. They were introduced in Python 3.5 and have become increasingly important for professional Python development.

```python
def greet(name: str, times: int = 1) -> str:
    return (name + "! ") * times

def process(items: list[dict[str, int]]) -> None: ...

from typing import Optional, Union
def find(key: str) -> Optional[str]: ...       # str or None
def parse(data: Union[str, bytes]) -> dict: ... # str or bytes
```

**The key thing to understand:** Type hints are documentation only — Python does NOT enforce them at runtime. If you annotate a function as taking `int` and pass a string, Python won't stop you. No error at runtime. Type hints are checked by static analysis tools like mypy and Pylance (the tool you use in VS Code).

Why use them despite no runtime enforcement?

1. **Documentation:** When you see `def get_user(id: int) -> Optional[User]`, you immediately know: it takes an integer ID and returns either a User object or None. No need to read the function body.
2. **IDE support:** Your editor can provide better autocomplete, flag type errors before you run the code, and help with refactoring.
3. **Bug prevention:** Static type checkers can catch entire categories of bugs (passing wrong types, forgetting to handle None returns) before the code ever runs.
4. **Team collaboration:** In a codebase with many developers, type hints make the code self-documenting and reduce the "what type does this return?" questions.

For Python 3.10+, you can use `int | str` instead of `Union[int, str]` and `str | None` instead of `Optional[str]`.

---

## 15. Advanced Concepts

These topics come up in senior-level interviews and demonstrate deep Python knowledge.

### Metaclasses — Classes of Classes

In Python, everything is an object — including classes themselves. A class is an instance of its metaclass, just as an object is an instance of its class. The default metaclass is `type`. A custom metaclass lets you control how classes are created, validated, or modified.

```python
class MyMeta(type):
    def __new__(mcs, name, bases, namespace):
        print(f"Creating class: {name}")
        return super().__new__(mcs, name, bases, namespace)

class MyClass(metaclass=MyMeta):
    pass
# Prints: "Creating class: MyClass"
```

When Python encounters `class MyClass(metaclass=MyMeta)`, it calls `MyMeta.__new__` instead of `type.__new__` to create the class object. This gives you a hook to inspect, modify, or validate the class before it's created.

**Practical uses:** Django uses metaclasses to turn model class definitions into database table mappings. ORMs use metaclasses to register models. ABC (Abstract Base Classes) uses metaclasses to enforce abstract method implementation. But for most application code, you'll never need to write a metaclass.

**Interview answer:** "Metaclasses control class creation. They're used by frameworks like Django and SQLAlchemy to add magic behavior to class definitions. Regular application code almost never needs them — they're a framework author's tool."

### `__getattr__` vs `__getattribute__`

Both methods are called when you access an attribute on an object, but at different stages:

**`__getattribute__`** is called for EVERY attribute access, before Python even checks if the attribute exists. This is the entry point for ALL attribute access. Overriding it is dangerous because you can accidentally break basic operations (even `self.x` inside `__getattribute__` would cause infinite recursion).

**`__getattr__`** is called ONLY when the normal attribute lookup FAILS — when the attribute doesn't exist on the instance or its class. It's a fallback handler, like a "catch-all" for missing attributes.

```python
class Proxy:
    def __getattr__(self, name):
        return f"No attribute '{name}', returning fallback"

p = Proxy()
p.anything  # "No attribute 'anything', returning fallback"
```

**When to use which:** Override `__getattr__` for fallback/default behavior (most cases). Avoid `__getattribute__` unless you're building a proxy, logging layer, or ORM field access system — and even then, be very careful about infinite recursion.

### Monkey Patching

Monkey patching means modifying a class, module, or object at runtime — adding, replacing, or removing attributes/methods after they've been defined. Python allows this because classes and modules are mutable objects.

```python
class Dog:
    def speak(self): return "Woof"

Dog.speak = lambda self: "Meow"  # runtime change
Dog().speak()  # "Meow"
```

**In practice:** Monkey patching is used primarily in testing — replacing a real database call with a mock during unit tests. Python's `unittest.mock.patch` is a structured way to do monkey patching safely (it automatically restores the original after the test).

**In production code:** Monkey patching is generally dangerous because it makes code hard to reason about (the class definition says one thing, but runtime behavior is different), and it can break when libraries update. Avoid it outside of testing.

### Walrus Operator `:=` (3.8+)

The walrus operator assigns a value to a variable as part of an expression. This lets you avoid computing the same value twice — once to check it, and once to use it.

```python
# Without walrus: input() called twice, or needs a separate line
line = input()
while line != "quit":
    process(line)
    line = input()

# With walrus: cleaner
while (line := input()) != "quit":
    process(line)

# In comprehensions: avoid computing expensive() twice
results = [y for x in data if (y := expensive(x)) > threshold]
```

The walrus operator is a readability improvement for specific patterns — it's not meant to be used everywhere. Use it when you need to both test a value and use it in the same expression.

### The Global and Nonlocal Keywords

These keywords are needed when you want to modify variables that exist in an outer scope. Without them, assignment inside a function creates a NEW local variable instead of modifying the outer one.

```python
counter = 0
def increment():
    global counter    # without this, counter += 1 fails
    counter += 1

def make_counter():
    count = 0
    def inc():
        nonlocal count  # refers to enclosing scope variable
        count += 1
        return count
    return inc
```

**`global`** tells Python that `counter` refers to the module-level variable, not a new local variable. Without it, `counter += 1` would fail because Python sees the assignment and treats `counter` as a local variable that hasn't been defined yet.

**`nonlocal`** does the same thing but for enclosing function scopes (closures). Without it, `count += 1` inside `inc()` would fail the same way.

In general, avoid `global` — it creates hidden dependencies between functions and module-level state, making code hard to test and reason about. `nonlocal` is more acceptable because it's contained within a closure.

---

## 16. Useful Built-in Functions and Patterns

These are the tools and patterns you'll use every day in Python. Knowing them makes your code more concise and Pythonic.

### enumerate, zip, any, all

**enumerate** gives you both the index and the value when iterating. It eliminates the need for manual index tracking with a counter variable:

```python
for i, fruit in enumerate(fruits, start=1):
    print(f"{i}: {fruit}")
```

**zip** combines multiple iterables element by element. It pairs the first item of each iterable, then the second, and so on. It stops at the shortest iterable:

```python
for name, score in zip(names, scores):
    print(f"{name}: {score}")

score_map = dict(zip(names, scores))
```

**all** and **any** test conditions across an iterable. `all` returns True only if EVERY element satisfies the condition. `any` returns True if at least ONE element does. They short-circuit — `any` stops at the first True, `all` stops at the first False:

```python
all(x > 0 for x in nums)    # True if ALL positive
any(x > 100 for x in nums)  # True if ANY > 100
```

### sorted with key

The `key` parameter lets you sort by a computed value rather than the elements themselves. The key function is called once per element, and sorting is done based on the return values:

```python
sorted(words, key=len)
sorted(users, key=lambda u: u["age"], reverse=True)
```

### String Handling

```python
f"{name} is {age}"          # f-string (always use this)
f"{3.14159:.2f}"            # "3.14"
f"{1000000:,}"              # "1,000,000"

s.strip(); s.lower(); s.upper()
s.split(","); ",".join(items)
s.startswith("He"); s.endswith("!")
s.replace("old", "new")
```

**Concatenation performance — an important gotcha:**
```python
# SLOW: creates new string each time -> O(n^2)
result = ""
for w in words: result += w

# FAST: one allocation -> O(n)
result = "".join(words)
```

Because strings are immutable, `result += w` creates a brand new string each iteration by copying the entire existing `result` plus the new word. With 1000 words, this copies approximately 1+2+3+...+1000 = 500,000 characters total. `"".join(words)` calculates the total length first, allocates memory once, and copies each word exactly once — much faster.

### File Handling

```python
with open("file.txt") as f:
    content = f.read()           # entire file
    # or: for line in f:          # line by line (memory efficient)

with open("out.txt", "w") as f:
    f.write("data\n")

import json
data = json.load(open("config.json"))
json.dump(data, open("out.json", "w"), indent=2)
```

Always use `with` statements for file handling — it guarantees the file is closed even if an exception occurs. For large files, iterate line by line (`for line in f`) instead of reading the entire file into memory (`f.read()`).

### One-Liners — Pythonic Patterns

These are idiomatic Python patterns that experienced developers use regularly:

```python
a, b = b, a                              # swap without temp variable
flat = [x for sub in nested for x in sub] # flatten nested list
reversed_s = s[::-1]                      # reverse string
unique = list(dict.fromkeys(items))       # dedupe, keep order
merged = dict1 | dict2                    # merge dicts (3.9+)
longest = max(words, key=len)             # max by criterion
```

---

## 17. Interview Questions — What Interviewers Expect You to Explain

These are the most frequently asked conceptual Python questions. For each one, you should be able to explain it clearly in your own words with an example.

### "`is` vs `==`?"
`==` compares values — it checks if two objects have the same content. `is` compares identity — it checks if two variables point to the exact same object in memory (same memory address). Use `==` for almost everything. Use `is` only with `None` (because `None` is a singleton — there's exactly one `None` object in Python, so `x is None` is checking "does x point to that one None object?").

### "LEGB scoping?"
When Python encounters a variable name, it searches for it in four scopes in this order: Local (inside the current function), Enclosing (in the enclosing function, for closures), Global (at the module level), Built-in (Python's built-in names like `len`, `print`, `range`). Python uses the first match it finds. If the name isn't found in any scope, you get a `NameError`.

### "`__str__` vs `__repr__`?"
`__str__` is for end users — it produces a human-readable, friendly string. It's called by `print()` and `str()`. `__repr__` is for developers — it produces an unambiguous string that ideally could recreate the object. It's called by the debugger, the REPL, and `repr()`. If you only implement one, implement `__repr__` — Python falls back to `__repr__` when `__str__` isn't defined, but not vice versa.

### "What is duck typing?"
Duck typing is Python's approach to type checking: "If it walks like a duck and quacks like a duck, it IS a duck." Instead of checking an object's type before using it, Python just tries to use it. If the object has the right methods, it works; if not, you get an error. This means you can pass any object to a function as long as it has the methods the function calls — no inheritance or interface declaration required.

### "Virtual environment?"
A virtual environment is an isolated Python installation for a specific project. It has its own copy of the Python interpreter and its own set of installed packages, separate from the system Python and from other projects. This prevents package version conflicts — Project A can use Flask 2.0 while Project B uses Flask 3.0, without interference. Created with `python -m venv myenv`, activated with `myenv\Scripts\activate` (Windows) or `source myenv/bin/activate` (Linux/Mac).

### "`append` vs `extend`?"
`append` adds its argument as a SINGLE element to the end of the list. `extend` iterates through its argument and adds EACH element individually.
```python
a.append([3, 4])   # [1, 2, [3, 4]]  -- adds one element (the list itself)
a.extend([3, 4])   # [1, 2, 3, 4]    -- adds each element (3 and 4 separately)
```

### "How to handle missing dict keys?"
Three approaches, each for different situations:
```python
d.get("key", default)         # returns default if missing, dict unchanged
d.setdefault("key", default)  # returns default if missing AND inserts it into the dict
defaultdict(int)               # auto-creates default values on first access
```
`get` is for reading without side effects. `setdefault` is for reading with auto-creation. `defaultdict` is for counters and collectors where every access should auto-create.

### "`yield` vs `return`?"
`return` ends the function permanently and sends back a single value. The function's local state is destroyed. `yield` pauses the function temporarily and sends back a value. The function's state (local variables, execution position) is preserved. When `next()` is called, the function resumes from exactly where it paused. A function with `yield` is called a generator — it produces values lazily, one at a time, instead of creating all values at once.

### "What is `@wraps`?"
`@wraps(func)` from functools is used inside decorators to preserve the original function's metadata (name, docstring, module, signature) on the wrapper function. Without it, after decorating, `func.__name__` would show "wrapper" instead of the real function name, and `help(func)` would show the wrapper's docstring. This matters for debugging, logging, and documentation tools.

### "List vs tuple?"
List is mutable (you can modify it after creation) — use when data changes over time, like a shopping cart or a collection you're building up. Tuple is immutable (fixed after creation) — use for data that shouldn't change, like coordinates, database records, or function return values with multiple items. Tuples can be used as dictionary keys (because they're hashable); lists cannot.

### "What is GIL?"
The Global Interpreter Lock is a mutex in CPython that allows only one thread to execute Python bytecode at a time. This means Python threads can't achieve true CPU parallelism, even on multi-core machines. For I/O-bound work (network calls, database queries), use threads — the GIL is released during I/O waits. For CPU-bound work (computation), use multiprocessing — each process has its own GIL. For high-concurrency I/O, use asyncio — single-threaded event loop with cooperative multitasking.

---

## 18. Python Connected to Your Resume

Understanding how Python concepts map to your real work experience helps you give concrete, specific answers in interviews.

| What You Did | Python Concepts Involved |
|---|---|
| PySpark pipelines | You used DataFrames (similar to SQL), lambda functions for transformations, UDFs (User Defined Functions) for custom logic that Spark's built-in functions couldn't handle, and closures for passing configuration into UDF functions. Understanding lazy evaluation (Spark transformations aren't executed until an action is called) maps directly to Python generators. |
| Flask/FastAPI services | Decorators are the foundation of Flask/FastAPI — `@app.route()` registers URL handlers, custom decorators handle authentication and logging. FastAPI uses async/await for non-blocking I/O, type hints for automatic request validation, and Pydantic models (dataclass-like) for serialization. |
| Kafka consumers | Stream processing uses generators and iterator patterns — consuming messages one at a time, processing them, and committing offsets. Error handling with try/except ensures a single bad message doesn't crash the entire consumer. |
| Airflow DAGs | PythonOperator wraps regular Python functions as DAG tasks. XCom (cross-communication) passes data between tasks using serialization. Task dependencies use Python operators. Understanding modules and packages is essential for organizing DAG files. |
| CI/CD scripts | The `subprocess` module for running external commands, `os` and `pathlib` for file system operations, `json` for config files, and context managers for temporary file handling. |
| Regex packet parsing | The `re` module for pattern matching, compiled patterns (`re.compile`) for performance, named groups for readability, and the distinction between `re.match` (start of string) vs `re.search` (anywhere in string). |
| Code obfuscation | Understanding of Python's AST (Abstract Syntax Tree) module, bytecode compilation, and how Python code is parsed and executed. This is deep Python internals knowledge. |
| Data quality | pytest for test frameworks, assertions for validation, fixtures for test setup, and parameterized tests for testing multiple inputs with the same logic. |

---

*Last updated: August 2026*
