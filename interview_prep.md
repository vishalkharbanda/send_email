# Everything Else — Complete Interview Prep
> Covers all remaining topics a 4-year Backend Engineer should know
> DSA, System Design, REST APIs, Git, Docker, Linux, Design Patterns, Networking, OS, Behavioral

---

# PART 1: DATA STRUCTURES & ALGORITHMS (DSA)

DSA is the foundation of coding interviews. Even for backend roles, you'll almost certainly face at least one coding round. The good news: you don't need to be a competitive programmer. You need to recognize patterns and apply them. Most interview problems are variations of 10-15 core patterns.

---

## 1. Arrays and Strings

### Arrays — The Foundation

An array is a contiguous block of memory where elements are stored one after another. Because the elements are contiguous, accessing any element by index is instant — the computer just calculates the memory address as `start + index * element_size`. In Python, `list` is a dynamic array — it automatically grows when you add elements (by allocating a bigger block of memory and copying everything over).

Arrays are the most fundamental data structure and the basis of countless interview problems. Most array problems boil down to one of three patterns: two pointers, sliding window, or hash map lookup.

**Two Pointer Pattern:**

The two pointer technique works on sorted arrays. You place one pointer at the start and one at the end, then move them toward each other based on some condition. This avoids the brute force approach of checking every pair (which would be O(n²)) and gives you O(n) instead.

```python
# Check if sorted array has two numbers that sum to target:
def two_sum_sorted(nums, target):
    left, right = 0, len(nums) - 1
    while left < right:
        total = nums[left] + nums[right]
        if total == target: return [left, right]
        elif total < target: left += 1
        else: right -= 1
    return []
```

Why this works: since the array is sorted, the left pointer points to the smallest remaining value and the right pointer points to the largest. If their sum is too small, the only way to increase it is to move the left pointer right (to a bigger number). If the sum is too big, move the right pointer left (to a smaller number). You're guaranteed to find the pair if it exists, and you scan the array only once.

**Sliding Window Pattern:**

The sliding window technique is used when you need to find something among all contiguous subarrays of a fixed size (or sometimes variable size). Instead of recomputing the sum/count for each subarray from scratch, you "slide" the window by adding the new element on the right and removing the old element on the left. This turns an O(n×k) brute force into O(n).

```python
# Maximum sum of any k consecutive elements:
def max_sum_subarray(nums, k):
    window_sum = sum(nums[:k])
    max_sum = window_sum
    for i in range(k, len(nums)):
        window_sum += nums[i] - nums[i-k]  # slide: add right, remove left
        max_sum = max(max_sum, window_sum)
    return max_sum
```

Think of it like a window frame that you slide across the array. At each position, you only change what enters and leaves the window — you don't recalculate everything inside.

**Kadane's Algorithm — Maximum Subarray Sum:**

This is a classic problem: find the contiguous subarray with the largest sum. The key insight is that at each element, you have two choices: either extend the current subarray (add this element to the running sum), or start a new subarray from this element. You start fresh when the running sum has become negative — a negative prefix can only hurt the total.

```python
def max_subarray(nums):
    current_sum = max_sum = nums[0]
    for num in nums[1:]:
        current_sum = max(num, current_sum + num)  # extend or start fresh
        max_sum = max(max_sum, current_sum)
    return max_sum
```

### Strings

Strings in Python are immutable sequences of characters. Many string problems are really array problems in disguise — you treat the string as an array of characters. The key string tools you need:

**Common operations:**
```python
s[::-1]                    # reverse
s.count('a')               # count occurrences
set(s)                     # unique characters
Counter(s)                 # character frequency
s.isalnum()                # alphanumeric check
ord('a')                   # ASCII value (97)
chr(97)                    # character from ASCII ('a')
```

**Anagram check:** Two strings are anagrams if they contain the same characters in the same quantities, just rearranged. The simplest check is to compare their character frequency counts.

```python
def is_anagram(s1, s2):
    return Counter(s1) == Counter(s2)
```

**Palindrome check:** A palindrome reads the same forwards and backwards. The simplest approach is to reverse the string and compare:

```python
def is_palindrome(s):
    s = s.lower().replace(" ", "")
    return s == s[::-1]
```

---

## 2. Hash Maps (Dictionaries)

Hash maps are arguably the most useful data structure in coding interviews. They provide O(1) average-case lookup, insertion, and deletion. The idea is simple: instead of searching through all elements to find something (O(n)), you compute a "hash" of the key — a number that tells you exactly where to look. It's like having an index that directly maps any key to its location.

In Python, `dict` is the hash map, and `set` is a hash set (hash map without values). Whenever a problem says "find if X exists" or "count occurrences" or "find pairs that satisfy a condition," think hash map first.

**Two Sum (unsorted) — THE classic interview question:**

You're given an unsorted array and a target sum. Find two numbers that add up to the target. The brute force is O(n²) — check every pair. The hash map approach is O(n) — for each number, check if its complement (target - number) has already been seen.

```python
def two_sum(nums, target):
    seen = {}  # value -> index
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
```

As you walk through the array, you store each number and its index in the hash map. For each new number, you check "have I already seen the number that would complete the sum?" If yes, return both indices. One pass through the array, O(1) lookups in the hash map — total O(n).

**Group Anagrams:** Given a list of strings, group the ones that are anagrams of each other. The trick is choosing a hash map key that's the same for all anagrams. Sorting the characters works — "eat", "tea", "ate" all sort to "aet".

```python
def group_anagrams(strs):
    groups = defaultdict(list)
    for s in strs:
        key = tuple(sorted(s))  # sorted letters as key
        groups[key].append(s)
    return list(groups.values())
```

**Frequency counting pattern:** Counting how often things appear is one of the most common uses of hash maps. Python's Counter makes this trivial:

```python
freq = Counter(nums)
most_common = freq.most_common(k)    # top k frequent
```

---

## 3. Linked Lists

A linked list is a chain of nodes where each node contains a value and a pointer (reference) to the next node. Unlike arrays, linked list elements are NOT stored contiguously in memory — each node can be anywhere, connected only by pointers.

**Why linked lists matter in interviews:** They're a favorite interview topic because they test your ability to manipulate pointers (references) and handle edge cases (empty list, single node, end of list). They also force you to think carefully about what happens when you change a pointer — you can easily "lose" part of the list if you're not careful.

**When linked lists are better than arrays:** Inserting or deleting in the middle is O(1) if you already have a reference to the node (just change pointers), while arrays require shifting all subsequent elements (O(n)). But random access is O(n) in linked lists (you must walk from the head), while arrays give O(1) random access.

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
```

**Reverse a linked list:** This is the #1 linked list interview question. The idea is to walk through the list, and for each node, reverse its pointer to point to the previous node instead of the next. You need three pointers: `prev` (the reversed part behind you), `current` (the node you're processing), and `next_node` (saved so you don't lose the rest of the list when you reverse the pointer).

```python
def reverse(head):
    prev = None
    current = head
    while current:
        next_node = current.next
        current.next = prev    # reverse the pointer
        prev = current
        current = next_node
    return prev
```

**Detect cycle (Floyd's Tortoise and Hare algorithm):** How do you detect if a linked list has a cycle (a node pointing back to an earlier node, creating an infinite loop)? Use two pointers moving at different speeds. The slow pointer moves one step at a time, the fast pointer moves two steps. If there's a cycle, the fast pointer will eventually "lap" the slow pointer and they'll meet. If there's no cycle, the fast pointer reaches the end.

```python
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next         # 1 step
        fast = fast.next.next    # 2 steps
        if slow == fast:
            return True
    return False
```

**Find middle:** The same two-speed pointer trick. When the fast pointer reaches the end, the slow pointer is at the middle (because slow moved half as many steps).

```python
def find_middle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow    # slow is at middle when fast reaches end
```

---

## 4. Stacks and Queues

Stacks and queues are two fundamental data structures that differ in the order they process elements. Understanding when to use which is key.

### Stack — LIFO (Last In, First Out)

A stack processes elements in reverse order — the last element added is the first one removed, like a stack of plates. You push plates on top and take plates from the top. In Python, a regular list works perfectly as a stack using `append()` and `pop()`.

Stacks are the right choice whenever you need to process things in reverse order, match nested structures (parentheses, HTML tags), or remember a "history" that you backtrack through (undo operations, browser back button, DFS traversal).

```python
stack = []
stack.append(1)    # push
stack.pop()        # pop (from end)
stack[-1]          # peek (top element)
```

**Valid parentheses — THE classic stack problem:** Given a string of brackets like `"({[]})"`, check if every opening bracket has a matching closing bracket in the correct order. The key insight is that the most recently opened bracket must be closed first — that's LIFO behavior, perfect for a stack. When you see an opening bracket, push it. When you see a closing bracket, pop and check if it matches.

```python
def is_valid(s):
    stack = []
    pairs = {')': '(', '}': '{', ']': '['}
    for char in s:
        if char in '({[':
            stack.append(char)
        elif char in ')}]':
            if not stack or stack[-1] != pairs[char]:
                return False
            stack.pop()
    return len(stack) == 0
```

### Queue — FIFO (First In, First Out)

A queue processes elements in the order they arrived — like a line at a shop. The first person in line is served first. Use Python's `deque` (double-ended queue) because it provides O(1) operations at both ends, while `list.pop(0)` is O(n).

Queues are the right choice for BFS (breadth-first search), task scheduling, and any situation where you need to process things in arrival order.

```python
from collections import deque
queue = deque()
queue.append(1)     # enqueue (right)
queue.popleft()     # dequeue (left) -- O(1) with deque
```

### Monotonic Stack — Next Greater Element

A monotonic stack is an advanced stack pattern where you maintain elements in a specific order (increasing or decreasing). It's used to efficiently find the "next greater element" or "next smaller element" for each position in an array. Without this pattern, you'd need O(n²) nested loops; with it, you do it in O(n) because each element is pushed and popped at most once.

```python
def next_greater(nums):
    result = [-1] * len(nums)
    stack = []  # stores indices
    for i, num in enumerate(nums):
        while stack and nums[stack[-1]] < num:
            result[stack.pop()] = num
        stack.append(i)
    return result
```

The stack keeps track of elements that haven't found their "next greater" yet. When a new element is bigger than what's on top of the stack, that new element IS the next greater for the top element.

---

## 5. Trees

Trees are hierarchical data structures where each node has a value and references to child nodes. The most common type is a binary tree, where each node has at most two children (left and right). Trees appear in interviews constantly because they naturally require recursion, and recursion tests your ability to think about problems in terms of smaller subproblems.

### Binary Tree

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
```

### Traversals — Must Know All Three

Tree traversals define the order in which you visit nodes. There are three depth-first traversals, and the names tell you when you process the ROOT relative to its children:

**Inorder (Left, Root, Right):** Visit the left subtree first, then the root, then the right subtree. For a Binary Search Tree (BST), inorder traversal gives you all elements in sorted order — this is a very common interview fact.

**Preorder (Root, Left, Right):** Visit the root first, then left, then right. Useful for creating a copy of the tree or serializing it (because you process the root before its children, you can reconstruct the structure).

**Postorder (Left, Right, Root):** Visit children first, then the root. Useful for deleting a tree (delete children before parent) or calculating values that depend on children (like the size or height of each subtree).

```python
# Inorder (Left, Root, Right) -- gives sorted order for BST:
def inorder(root):
    if not root: return []
    return inorder(root.left) + [root.val] + inorder(root.right)

# Preorder (Root, Left, Right):
def preorder(root):
    if not root: return []
    return [root.val] + preorder(root.left) + preorder(root.right)

# Postorder (Left, Right, Root):
def postorder(root):
    if not root: return []
    return postorder(root.left) + postorder(root.right) + [root.val]
```

### BFS (Level Order) — Using Queue

BFS visits nodes level by level — first the root (level 0), then all nodes at level 1, then all at level 2, and so on. It uses a queue because you process nodes in the order you discover them (FIFO). BFS is the right choice when you need to find the shortest path, process level by level, or explore nodes closest to the root first.

```python
def level_order(root):
    if not root: return []
    result, queue = [], deque([root])
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.val)
            if node.left: queue.append(node.left)
            if node.right: queue.append(node.right)
        result.append(level)
    return result
```

The trick for level-by-level processing: at the start of each iteration, the queue contains exactly the nodes for the current level. Process all of them (inner loop), and their children (next level) get added to the queue.

### Max Depth

A classic recursive problem. The depth of a tree is 1 (for the current node) plus the maximum depth of its two subtrees. The base case is: an empty tree (None) has depth 0. This is a perfect example of how tree problems decompose into subproblems.

```python
def max_depth(root):
    if not root: return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))
```

### BST (Binary Search Tree)

A BST is a binary tree with an ordering property: for every node, all values in its left subtree are smaller, and all values in its right subtree are larger. This property enables O(log n) search — at each node, you know whether to go left or right, eliminating half the remaining nodes.

However, BST performance depends on balance. A perfectly balanced BST with n nodes has height log(n), giving O(log n) operations. But if you insert sorted data, the tree degenerates into a linked list with height n, giving O(n) operations. Self-balancing BSTs (AVL trees, Red-Black trees) prevent this by automatically rebalancing after insertions and deletions.

```python
def search_bst(root, target):
    if not root: return None
    if target == root.val: return root
    if target < root.val: return search_bst(root.left, target)
    return search_bst(root.right, target)
```

---

## 6. Graphs

A graph is a collection of nodes (vertices) connected by edges. Unlike trees, graphs can have cycles (circular paths), multiple paths between nodes, and nodes with any number of connections. Graphs model real-world relationships: social networks (people connected by friendships), maps (cities connected by roads), dependencies (tasks that depend on other tasks).

### Representations

There are two main ways to store a graph in code:

**Adjacency list** is the most common and memory-efficient for sparse graphs (graphs with relatively few edges). Each node maps to a list of its neighbors. In Python, a dictionary of lists works perfectly.

**Adjacency matrix** uses a 2D array where `matrix[i][j] = 1` means there's an edge from node i to node j. Better for dense graphs (many edges) and when you need O(1) edge existence checks, but uses O(n²) memory.

```python
# Adjacency list (most common):
graph = {
    'A': ['B', 'C'],
    'B': ['A', 'D'],
    'C': ['A'],
    'D': ['B']
}

# From edge list:
from collections import defaultdict
graph = defaultdict(list)
for u, v in edges:
    graph[u].append(v)
    graph[v].append(u)  # undirected
```

### BFS — Shortest Path (Unweighted)

BFS explores all neighbors at distance 1 before neighbors at distance 2, then distance 3, and so on. This makes BFS perfect for finding the shortest path in an unweighted graph — the first time BFS reaches a node, that's the shortest path to it.

BFS uses a queue (FIFO) and a visited set to avoid revisiting nodes (which would cause infinite loops in graphs with cycles).

```python
def bfs(graph, start):
    visited = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return visited
```

### DFS — Explore Deep First

DFS goes as deep as possible along each branch before backtracking. It's implemented with recursion (which uses the call stack) or an explicit stack. DFS is the right choice for: detecting cycles, topological sorting, finding connected components, solving maze-like problems, and any problem where you need to explore all possible paths.

```python
def dfs(graph, node, visited=None):
    if visited is None: visited = set()
    visited.add(node)
    for neighbor in graph[node]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited)
    return visited
```

**BFS vs DFS — When to Use Which:**
- BFS: shortest path (unweighted), level-by-level processing, finding nearest X
- DFS: cycle detection, topological sort, path finding, connected components, backtracking

### Cycle Detection (Directed Graph)

Detecting cycles in a directed graph uses DFS with a three-color marking system. Each node starts WHITE (unvisited). When you start processing a node, mark it GRAY (in progress). When you finish processing all its descendants, mark it BLACK (done). If you ever encounter a GRAY node during DFS, that means you've found a back edge — a path leading back to a node you're currently processing — which means there's a cycle.

```python
def has_cycle(graph):
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}

    def dfs(node):
        color[node] = GRAY
        for neighbor in graph[node]:
            if color[neighbor] == GRAY: return True   # back edge = cycle
            if color[neighbor] == WHITE and dfs(neighbor): return True
        color[node] = BLACK
        return False

    return any(dfs(n) for n in graph if color[n] == WHITE)
```

### Number of Islands (Grid BFS/DFS)

This is one of the most popular graph interview problems. A 2D grid of '1's (land) and '0's (water) is given. An island is a group of '1's connected horizontally or vertically. Count the number of islands.

The approach: scan the grid cell by cell. When you find a '1' (land), increment the island count and then use BFS (or DFS) to "flood fill" — visit all connected '1's and mark them as visited (change to '0') so you don't count them again. Each time you start a new flood fill, you've found a new island.

```python
def num_islands(grid):
    count = 0
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] == '1':
                count += 1
                # BFS to mark entire island as visited
                queue = deque([(i, j)])
                grid[i][j] = '0'
                while queue:
                    r, c = queue.popleft()
                    for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] == '1':
                            grid[nr][nc] = '0'
                            queue.append((nr, nc))
    return count
```

---

## 7. Sorting and Searching

### Binary Search — O(log n)

Binary search works on sorted arrays. The idea: look at the middle element. If it's your target, done. If the target is smaller, search the left half. If larger, search the right half. Each step eliminates half the remaining elements, giving O(log n) — even a billion elements only needs ~30 steps.

Binary search is one of the most important algorithms to master because it appears in many forms — not just "find a number in a sorted array" but also "find the first position where a condition becomes true" (binary search on the answer).

```python
def binary_search(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target: return mid
        elif nums[mid] < target: left = mid + 1
        else: right = mid - 1
    return -1
```

**Lower bound (first occurrence):** A variation that finds the first position where the target could be inserted while maintaining sorted order. This is useful for finding the first occurrence of a value, or the insertion point.

```python
def lower_bound(nums, target):
    left, right = 0, len(nums)
    while left < right:
        mid = (left + right) // 2
        if nums[mid] < target: left = mid + 1
        else: right = mid
    return left
```

### Sorting Algorithms — Know These

You don't need to code all of these from memory, but you should know their complexities, trade-offs, and which situations favor which algorithm. The table below is frequently asked in interviews.

**Stability** means that elements with equal keys maintain their original relative order. This matters when you sort by multiple criteria — sort by name first, then by age; a stable sort preserves the name order among people with the same age.

| Algorithm | Best | Average | Worst | Space | Stable? |
|-----------|------|---------|-------|-------|---------|
| Bubble Sort | O(n) | O(n^2) | O(n^2) | O(1) | Yes |
| Selection Sort | O(n^2) | O(n^2) | O(n^2) | O(1) | No |
| Insertion Sort | O(n) | O(n^2) | O(n^2) | O(1) | Yes |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) | Yes |
| Quick Sort | O(n log n) | O(n log n) | O(n^2) | O(log n) | No |
| Heap Sort | O(n log n) | O(n log n) | O(n log n) | O(1) | No |
| Tim Sort (Python) | O(n) | O(n log n) | O(n log n) | O(n) | Yes |

**Merge Sort** is the one you should be able to code from scratch. It's a divide-and-conquer algorithm: split the array in half, recursively sort each half, then merge the two sorted halves together. The merge step is the key — you walk through both halves simultaneously, always picking the smaller element.

```python
def merge_sort(arr):
    if len(arr) <= 1: return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
```

**Quick Sort** is usually faster in practice (better cache behavior) but has O(n²) worst case when the pivot is poorly chosen (already sorted data with first-element pivot). **Merge Sort** guarantees O(n log n) always but uses O(n) extra memory.

Python's built-in `sorted()` uses Timsort, which is a hybrid of merge sort and insertion sort. It's adaptive — it takes advantage of partially sorted data and achieves O(n) on already-sorted input. Always O(n log n) in the worst case. In interviews, just use `sorted()` unless the problem specifically asks you to implement a sorting algorithm.

---

## 8. Dynamic Programming (DP)

### The Concept

Dynamic Programming is the most feared interview topic, but the core idea is simple: if a problem can be broken into smaller overlapping subproblems, solve each subproblem only once and store the result so you don't recompute it. The "dynamic" part is just a fancy name for "remembering answers."

There are two approaches:
- **Top-down (memoization):** Write the recursive solution, then add caching. Start from the big problem, break it down, cache results.
- **Bottom-up (tabulation):** Build a table from the smallest subproblems up to the answer. No recursion — just loops.

Both give the same result; memoization is usually easier to write, while tabulation can be more memory-efficient.

**Fibonacci — the simplest DP example:**

Without DP, computing fibonacci(50) takes ~2^50 function calls because the same values are recomputed exponentially. Fib(3) is computed millions of times. With DP, each value is computed exactly once.

```python
# Without DP: O(2^n) -- exponentially slow
def fib_naive(n):
    if n < 2: return n
    return fib_naive(n-1) + fib_naive(n-2)

# With memoization (top-down DP): O(n)
from functools import lru_cache
@lru_cache
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)

# With tabulation (bottom-up DP): O(n)
def fib_tab(n):
    if n < 2: return n
    dp = [0] * (n+1)
    dp[1] = 1
    for i in range(2, n+1):
        dp[i] = dp[i-1] + dp[i-2]
    return dp[n]
```

### Climbing Stairs — Classic DP

"You can climb 1 or 2 steps. How many ways to reach step n?" This is fibonacci in disguise. To reach step n, you either came from step n-1 (one step) or step n-2 (two steps). So `ways(n) = ways(n-1) + ways(n-2)`. You can even optimize to O(1) space by only keeping the last two values instead of the entire array.

```python
def climb_stairs(n):
    if n <= 2: return n
    prev2, prev1 = 1, 2
    for _ in range(3, n+1):
        current = prev1 + prev2
        prev2, prev1 = prev1, current
    return prev1
```

### 0/1 Knapsack

"Given items with weights and values, maximize total value within a weight capacity." This is the classic DP problem because each item presents a binary choice — take it or leave it — and the optimal solution depends on optimal solutions to smaller subproblems (smaller capacity, fewer items).

The 2D table `dp[i][w]` represents "the maximum value achievable using the first i items with weight capacity w." For each item, you either skip it (value stays the same as `dp[i-1][w]`) or take it (add its value and reduce capacity: `dp[i-1][w-weight] + value`). Take the maximum.

```python
def knapsack(weights, values, capacity):
    n = len(weights)
    dp = [[0] * (capacity+1) for _ in range(n+1)]
    for i in range(1, n+1):
        for w in range(capacity+1):
            dp[i][w] = dp[i-1][w]  # don't take item i
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], dp[i-1][w-weights[i-1]] + values[i-1])
    return dp[n][capacity]
```

### Longest Common Subsequence (LCS)

"Find the length of the longest subsequence common to two strings." A subsequence doesn't have to be contiguous — you can skip characters. For example, LCS of "abcde" and "ace" is "ace" (length 3).

The DP table `dp[i][j]` represents the LCS length of `s1[:i]` and `s2[:j]`. If the current characters match (`s1[i-1] == s2[j-1]`), extend the LCS by 1 from the diagonal. If not, take the maximum of skipping a character from either string.

```python
def lcs(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n+1) for _ in range(m+1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]
```

### How to Spot a DP Problem

DP problems have these characteristics:
1. **"Find the minimum/maximum/number of ways..."** — optimization or counting problems are strong DP signals.
2. **Overlapping subproblems** — the same inputs are computed multiple times in a naive recursive approach.
3. **Optimal substructure** — the optimal solution to the big problem is built from optimal solutions to smaller subproblems.
4. **You can define a recurrence relation** — a formula like `dp[i] = dp[i-1] + dp[i-2]` that relates the current answer to previous answers.

If a problem has these traits, try defining what `dp[i]` represents, write the base case(s), write the recurrence, and fill in the table.

---

## 9. Heaps / Priority Queues

A heap is a special tree-based data structure where the parent node is always smaller (min-heap) or larger (max-heap) than its children. This means the smallest (or largest) element is always at the root, giving you O(1) access to the extreme value and O(log n) insertion and removal.

Heaps are the implementation behind priority queues — data structures where elements are processed by priority rather than arrival order. Think of an emergency room: patients are treated by severity, not by who arrived first.

Python's `heapq` module provides a min-heap (smallest element first). For a max-heap, negate the values.

```python
import heapq

nums = [5, 1, 8, 3]
heapq.heapify(nums)           # O(n), min-heap
heapq.heappush(nums, 2)       # O(log n)
smallest = heapq.heappop(nums)  # O(log n), returns smallest

# Top K largest:
heapq.nlargest(3, nums)

# Top K smallest:
heapq.nsmallest(3, nums)

# Max-heap trick (negate values):
heapq.heappush(heap, -val)
max_val = -heapq.heappop(heap)
```

**Kth Largest Element:** A common interview pattern. Maintain a min-heap of size k. As you process elements, if a new element is larger than the heap's minimum, replace the minimum. After processing all elements, the heap's minimum is the kth largest. This is O(n log k) — much better than sorting the entire array O(n log n) when k is small.

```python
def kth_largest(nums, k):
    heap = nums[:k]
    heapq.heapify(heap)
    for num in nums[k:]:
        if num > heap[0]:
            heapq.heapreplace(heap, num)
    return heap[0]
```

---

## 10. Time and Space Complexity — Quick Reference

Big-O notation describes how an algorithm's performance scales as the input size grows. It doesn't tell you the exact time — it tells you the growth rate. An O(n) algorithm might be slow for n=10 but it scales linearly; an O(n²) algorithm might be fast for n=10 but becomes unusable at n=1,000,000.

In interviews, you'll be asked "What's the time complexity?" for almost every solution you write. Being able to analyze this correctly is as important as writing the solution.

| Notation | Name | What It Means | Example |
|----------|------|---------------|---------|
| O(1) | Constant | Time doesn't change regardless of input size. Whether you have 10 or 10 million elements, it takes the same time. | Dict lookup, array index access, push/pop on a stack |
| O(log n) | Logarithmic | Time grows very slowly. Doubling the input only adds one more step. 1 billion elements? Only ~30 steps. | Binary search, balanced BST operations |
| O(n) | Linear | Time grows directly proportional to input. Twice the input = twice the time. | Single loop through an array, linear search |
| O(n log n) | Linearithmic | Slightly worse than linear. This is the best possible time for comparison-based sorting. | Merge sort, Tim sort, heap sort |
| O(n^2) | Quadratic | Time grows with the square of the input. Doubling the input quadruples the time. Usually means nested loops. | Bubble sort, checking all pairs |
| O(2^n) | Exponential | Time doubles with each additional input element. Becomes unusable quickly. | Recursive fibonacci (naive), generating all subsets |
| O(n!) | Factorial | Time grows factorially. Worse than exponential. Only works for tiny inputs (n < 12). | Generating all permutations, brute-force traveling salesman |

**How to calculate complexity in your code:**
- **Single loop** over n elements: O(n)
- **Nested loops** (loop inside loop), both over n: O(n²)
- **Loop that halves** the remaining input each iteration (like binary search): O(log n)
- **Recursive function** that makes two recursive calls per level: O(2^n)
- **Sorting** first, then a single pass: O(n log n) — the sort dominates
- **Hash map lookups** inside a loop: O(n) total — each lookup is O(1)

**Space complexity** works the same way but measures memory usage instead of time. Creating a copy of the array is O(n) space. Using only a few variables is O(1) space. A 2D table of size n×m is O(n×m) space.

---

# PART 2: SYSTEM DESIGN

---

## 11. System Design Basics

At 4 years of experience, you won't be asked to design Twitter or Google Maps from scratch — that's for senior/staff engineers. But you're expected to understand the building blocks of large-scale systems and make informed trade-off decisions. Think of system design knowledge as your vocabulary for discussing architecture.

### Load Balancer

A load balancer sits between clients and your servers, distributing incoming requests across multiple server instances. Without a load balancer, all traffic goes to one server — if it crashes or gets overloaded, everything goes down. With a load balancer, traffic is spread across multiple servers, providing both redundancy (if one server dies, others handle the load) and scalability (add more servers to handle more traffic).

```
Client -> Load Balancer -> Server 1
                        -> Server 2
                        -> Server 3
```

**Load balancing algorithms determine which server receives each request:**
- **Round Robin:** Requests go to servers in order — 1, 2, 3, 1, 2, 3. Simple and works well when all servers have similar capacity and requests take similar time.
- **Least Connections:** Send each new request to the server with the fewest active connections. Better when requests have varying processing times — a server handling a slow query won't get more work piled on.
- **IP Hash:** Hash the client's IP address to deterministically pick a server. The same client always goes to the same server (session stickiness). Useful when servers maintain local session state.

You used NGINX as a reverse proxy/load balancer at Tech Mahindra — it sits in front of your Python and Node.js services and routes incoming requests to the appropriate backend.

### Caching

Caching stores frequently accessed data in fast storage (typically memory — RAM) to avoid repeatedly hitting a slower data source (typically a database on disk). Disk access is ~100,000x slower than memory access, so caching can dramatically improve response times.

Think of it like keeping a cookbook open on your kitchen counter instead of going to the bookshelf every time you need a recipe. The counter is your cache (fast, limited space), and the bookshelf is your database (slow, lots of space).

**Where to cache — multiple layers:**
- **Client-side (browser cache):** Static assets (images, CSS, JS) cached by the browser. No server request needed on repeat visits.
- **CDN (Content Delivery Network):** Static files cached on servers geographically close to users. A user in Mumbai gets served from a Mumbai CDN node, not from your server in the US.
- **Application layer (Redis, Memcached):** In-memory key-value store that sits between your app and database. Your API checks Redis first; if the data is there (cache hit), return immediately. If not (cache miss), query the database and store the result in Redis for next time.
- **Database query cache:** The database itself caches results of recent queries. Transparent to your application.

**Cache strategies — how your app interacts with the cache:**
- **Cache Aside (Lazy Loading):** The most common strategy. App checks cache first. On miss, app reads from DB, stores result in cache, and returns it. Data is only cached when it's actually requested. Simple but the first request for any data is always slow (cache miss).
- **Write Through:** When data is written, it goes to both the cache AND the database simultaneously. Cache is always up-to-date, but writes are slower (two destinations).
- **Write Behind (Write Back):** When data is written, it goes to the cache only. The cache asynchronously writes to the database in the background. Very fast writes, but if the cache crashes before flushing to DB, data is lost.
- **TTL (Time To Live):** Every cached entry has an expiration time. After that time, the entry is deleted and the next request triggers a fresh DB read. Simple to implement, but data can be stale until the TTL expires.

**Cache invalidation** — figuring out when to update or remove cached data — is famously described as one of the two hardest problems in computer science (the other being naming things). TTL is the simplest approach. Event-based invalidation (clear the cache when the database row is updated) is more precise but more complex to implement.

### Database Scaling

When a single database server can't handle the load, you need to scale it. There are two fundamental approaches, and they're not mutually exclusive.

**Vertical scaling (scale up):** Get a bigger, more powerful server — more RAM, faster CPU, faster disks. This is the simplest approach and should be your first move. A single powerful PostgreSQL server can handle a LOT of traffic. The limitation is that there's a maximum server size you can buy, and costs increase non-linearly.

**Horizontal scaling (scale out):** Add more database servers. This is more complex but has virtually no upper limit.

**Read replicas** are the most common first step in horizontal scaling. Your primary (main) database handles all write operations (INSERT, UPDATE, DELETE). One or more replicas (copies) handle read operations (SELECT). Since most applications have far more reads than writes (often 90% reads), this offloads the majority of work from the primary. The primary automatically replicates changes to the replicas, usually with a small delay (replication lag).

**Sharding** splits data itself across multiple independent database servers (shards). Each shard holds a subset of the total data. For example, shard by user_id: users 1-1,000,000 on Shard 1, users 1,000,001-2,000,000 on Shard 2. Each shard is independent — it only stores and queries its subset of data. The challenge: cross-shard queries (JOINing data from different shards) are very expensive or impossible. Your application must know which shard to query based on the shard key.

### Message Queues (Kafka, RabbitMQ)

Message queues decouple producers (services that generate work) from consumers (services that process work). Instead of Service A directly calling Service B (which means A must wait for B, and if B is down, A fails), Service A puts a message in a queue, and Service B picks it up when it's ready.

You know this well from XenonStack, where you used Kafka to stream CDC events from PostgreSQL to downstream consumers.

```
Producer -> Queue/Topic -> Consumer
```

**Why message queues matter:**
- **Async processing:** The producer doesn't wait for the consumer. A web API can accept an order and return immediately while the order processing happens in the background.
- **Traffic spike buffering:** If 10,000 requests arrive in one second, the queue absorbs them, and the consumer processes them at its own pace. Without a queue, the consumer would be overwhelmed.
- **Fault tolerance:** If the consumer crashes, messages stay in the queue until the consumer recovers. No data is lost.
- **Decoupling:** Producer and consumer can be developed, deployed, and scaled independently. Adding a new consumer (e.g., analytics) doesn't require changing the producer.

### API Gateway

An API Gateway is a single entry point that sits in front of all your microservices. Instead of clients knowing about and calling individual services directly, they call the gateway, which routes requests to the right service.

Think of it like a hotel concierge — you don't go directly to housekeeping, the restaurant, or maintenance. You tell the concierge what you need, and they route your request appropriately.

**What an API gateway handles:**
- **Routing:** `/users/*` goes to the Users service, `/orders/*` goes to the Orders service.
- **Authentication/Authorization:** Verify the JWT token once at the gateway rather than in every service.
- **Rate limiting:** Limit how many requests each user/API key can make per minute.
- **Request/response transformation:** Convert between formats, aggregate responses from multiple services into one response.
- **Logging and monitoring:** Centralized request logging and metrics collection.

### CAP Theorem

CAP theorem states that in a distributed system (data stored across multiple servers), you can only guarantee two of these three properties simultaneously:

- **Consistency:** Every read returns the most recent write. All servers have the same data at the same time.
- **Availability:** Every request gets a response (even if it's not the latest data). The system never refuses to answer.
- **Partition Tolerance:** The system continues to work even when network communication between servers is broken (network partition).

Since network partitions WILL happen in any distributed system (it's a matter of when, not if), you must always accept Partition Tolerance. This means your real choice is between Consistency and Availability during a partition:

- **CP (Consistency + Partition Tolerance):** During a network partition, the system returns an error rather than risk serving stale data. The system chooses to be correct over being available. Example: banking systems — you'd rather get an error than see an incorrect balance.
- **AP (Availability + Partition Tolerance):** During a network partition, the system returns whatever data it has, even if it might be slightly stale. The system chooses to be available over being perfectly correct. Example: social media feeds — seeing a 5-second-old version of your feed is acceptable.

### Rate Limiting

Rate limiting prevents abuse by restricting how many requests a user or IP address can make in a given time period. Without it, a single user could overwhelm your servers (intentionally or accidentally), affecting everyone else.

**Token Bucket algorithm:** Each user has a "bucket" that holds N tokens. Each request consumes one token. Tokens are replenished at a fixed rate (e.g., 10 tokens per second). If the bucket is empty (no tokens left), the request is rejected with HTTP 429 (Too Many Requests). The bucket can accumulate tokens up to its maximum, allowing short bursts of traffic while enforcing a long-term rate limit.

**Sliding Window algorithm:** Count the number of requests in the last N seconds. If the count exceeds the limit, reject new requests. This provides a smoother rate limit than fixed windows (which can allow bursts at window boundaries).

### Monolith vs Microservices

These are two architectural approaches to building applications, each with clear trade-offs.

**Monolith:** The entire application is one big codebase, deployed as a single unit. All features share the same database, the same process, and the same deployment. Benefits: simpler to develop (everything in one place), simpler to deploy (one artifact), simpler to debug (one log, one process), no network calls between components (function calls instead). Works great for small-to-medium apps and small teams.

**Microservices:** The application is split into many small, independent services, each responsible for one business capability. Each service has its own database, its own deployment pipeline, and communicates with others via APIs or message queues. Benefits: independent deployment (update one service without touching others), independent scaling (scale the busy service without scaling everything), technology flexibility (different services can use different languages), fault isolation (one service failing doesn't crash everything). Costs: complex networking, distributed debugging, data consistency challenges, operational overhead.

You work with microservices at Tech Mahindra (TMDC platform) — separate Python and Node.js services, each independently deployed.

---

## 12. System Design Interview Framework

When an interviewer asks "Design X," they're not looking for a perfect architecture. They want to see your thought process: how you gather requirements, make trade-offs, and communicate your reasoning. Follow this structure:

**1. Clarify Requirements (2 min)**
Don't start drawing immediately. Ask questions first:
- What features? (functional requirements — what should the system do?)
- How many users? (scale — thousands vs millions vs billions)
- Read-heavy or write-heavy? (this determines your optimization strategy)
- Latency requirements? (does it need to be real-time or is near-real-time OK?)
- What can we skip? (explicitly scope out non-essential features)

**2. High-Level Design (5 min)**
Sketch the main components and how data flows between them:
- Draw the main components (client, API, DB, cache, queue)
- Trace the data flow: how does a request travel through the system?
- Identify the database type (relational vs NoSQL) and justify your choice

**3. Detailed Design (10 min)**
Dive deeper into the most critical or complex parts:
- Database schema (what tables/collections, what columns, what indexes)
- API endpoints (REST endpoints with request/response format)
- Caching strategy (what to cache, when to invalidate)
- How to handle edge cases (duplicate requests, race conditions, failures)

**4. Scaling & Trade-offs (5 min)**
Show that you think about production reality:
- What's the bottleneck? (database reads? writes? network?)
- How to scale (replicas, sharding, caching, CDN)?
- What are the trade-offs of your choices? (consistency vs availability, complexity vs simplicity)

### Example: "Design a URL Shortener"

**Requirements:** Create short URL from long URL, redirect short URL to original, track click count.

**API:**
```
POST /shorten  { "url": "https://long-url.com/..." }  -> { "short": "abc123" }
GET  /abc123   -> 301 Redirect to original URL
```

**Database:**
```
urls: id | short_code | original_url | created_at | click_count
```

**Short code generation:** Base62 encode an auto-increment ID. ID=12345 -> base62 -> "dnh" (using 62 characters: a-z, A-Z, 0-9). This guarantees uniqueness (IDs are unique) and produces short codes (base62 is compact).

**Read-heavy** — many more redirects (reads) than URL creations (writes). This means caching is critical. Cache popular URLs in Redis — most URLs follow a Zipf distribution where a small percentage of URLs get the vast majority of clicks.

**Scale:** Read replicas for the database. Redis cache layer for hot URLs. CDN for the redirect service's static pages. Horizontal sharding by hash of short_code if the database grows beyond one server's capacity.

---

# PART 3: REST APIs & HTTP

---

## 13. HTTP Fundamentals

HTTP (HyperText Transfer Protocol) is the protocol that powers the web. Every time your browser loads a page, every time your API serves a request, every time your frontend talks to your backend — it's HTTP. Understanding HTTP deeply is essential for any backend developer.

### HTTP Methods

HTTP methods tell the server what operation you want to perform. They're not just names — they have semantic meanings that clients, servers, proxies, and caches rely on.

| Method | Purpose | Idempotent? | Safe? |
|--------|---------|-------------|-------|
| GET | Read data | Yes | Yes |
| POST | Create new resource | No | No |
| PUT | Replace entire resource | Yes | No |
| PATCH | Partial update | No | No |
| DELETE | Remove resource | Yes | No |

**Idempotent** means calling the operation multiple times has the same effect as calling it once. PUT /user/1 {name: "Vishal"} — calling it 5 times doesn't change the user 5 times; the user is still just "Vishal." This is important for reliability: if a network timeout occurs and you retry a PUT, you know it's safe. POST /users {name: "Vishal"} — calling it 5 times creates 5 users, so POST is NOT idempotent and retrying blindly is dangerous.

**Safe** means the operation doesn't modify any data on the server. GET is safe — it only reads. This tells caches and crawlers that they can call GET requests freely without causing side effects.

### HTTP Status Codes

Status codes tell the client what happened with their request. They're grouped by the first digit:

```
2xx = Success -- your request worked
  200 OK              -- general success, response body contains the result
  201 Created          -- a new resource was successfully created (typical POST response)
  204 No Content       -- success, but there's nothing to return (typical DELETE response)

3xx = Redirect -- the resource is somewhere else
  301 Moved Permanently  -- resource permanently moved; update your bookmarks
  302 Found (temporary redirect) -- resource temporarily at another URL
  304 Not Modified -- your cached version is still valid, no need to re-download

4xx = Client Error -- YOU (the caller) did something wrong
  400 Bad Request      -- your request is malformed (invalid JSON, missing fields)
  401 Unauthorized     -- you didn't provide authentication (who are you?)
  403 Forbidden        -- you authenticated but don't have permission (you can't do this)
  404 Not Found        -- the resource you requested doesn't exist
  405 Method Not Allowed -- you used GET on a POST-only endpoint, etc.
  409 Conflict         -- your request conflicts with current state (duplicate email)
  422 Unprocessable Entity -- request is well-formed but fails validation (email format wrong)
  429 Too Many Requests -- you've been rate limited, slow down

5xx = Server Error -- the SERVER messed up, not you
  500 Internal Server Error -- generic catch-all server crash
  502 Bad Gateway      -- the server (acting as proxy) got a bad response from upstream
  503 Service Unavailable -- server is overloaded or under maintenance
  504 Gateway Timeout  -- upstream server didn't respond in time
```

The distinction between 401 and 403 is a classic interview question: 401 means "I don't know who you are" (provide a token), 403 means "I know who you are but you're not allowed" (you have a token but insufficient permissions).

### Headers You Should Know

HTTP headers are metadata attached to requests and responses. They carry information about the content, authentication, caching, and more.

```
Content-Type: application/json       -- tells the recipient what format the body is in
Authorization: Bearer <token>        -- carries the authentication token
Cache-Control: max-age=3600          -- tells caches this response is valid for 1 hour
Accept: application/json             -- tells the server what format the client wants
X-Request-ID: uuid                   -- unique ID for tracing a request through multiple services
```

### REST API Design Best Practices

REST (Representational State Transfer) is a design philosophy for APIs. The key idea is that URLs represent resources (nouns), and HTTP methods represent actions (verbs). Your API should feel like you're interacting with objects, not calling functions.

```
# Resources as nouns, not verbs:
GET  /users           -- list users (not /getUsers)
GET  /users/123       -- get one user
POST /users           -- create user
PUT  /users/123       -- update user
DELETE /users/123     -- delete user

# Nested resources for relationships:
GET /users/123/orders        -- orders for user 123
GET /users/123/orders/456    -- specific order

# Filtering, sorting, pagination via query parameters:
GET /users?role=engineer&sort=name&page=2&limit=20

# Versioning to avoid breaking existing clients when you change the API:
GET /api/v1/users
GET /api/v2/users
```

**Why good API design matters:** A well-designed API is intuitive — other developers (and your future self) can guess how it works without reading documentation. Consistent resource naming, proper HTTP method usage, and meaningful status codes reduce errors and support tickets.

### Authentication Methods

**API Key:** A simple string that identifies the caller. Passed in a header like `X-API-Key: abc123`. Easy to implement but offers no granular permissions. Good for server-to-server communication where you trust both sides.

**JWT (JSON Web Token):** A self-contained token that carries user information (who they are, what they can do) signed with a secret key. The server creates a JWT on login, the client stores it and sends it with every request. The server verifies the signature without needing to look up a session in the database. This makes JWT "stateless" — any server can verify the token independently.

**OAuth 2.0:** A delegated authorization protocol. Instead of your app handling passwords, a trusted provider (Google, GitHub) authenticates the user and gives your app a token. "Login with Google" — Google verifies the user's identity and tells your app "yes, this is vishal@gmail.com." Your app never sees the user's Google password.

**Session-based:** The traditional approach. On login, the server creates a session (stored in memory or a database), gives the client a session ID cookie, and looks up the session on every request. Simple but requires server-side storage and doesn't scale easily across multiple servers (unless you use a shared session store like Redis).

### JWT — How It Works

A JWT consists of three parts, separated by dots:

```
Header.Payload.Signature

Header:  {"alg": "HS256", "typ": "JWT"}
Payload: {"user_id": 123, "role": "admin", "exp": 1693000000}
Signature: HMAC-SHA256(header + payload, secret_key)
```

The header specifies the algorithm. The payload contains the actual data (called "claims") — who the user is, their role, when the token expires. The signature is a cryptographic hash of the header and payload using a secret key that only the server knows.

Server creates JWT on login, client stores it (usually in localStorage or a cookie), sends in `Authorization: Bearer <token>` with every request. Server verifies the signature on each request without touching the database — just compute the hash again with the secret key and compare.

**Advantage:** Stateless — no session storage needed. Any server can verify the token independently, which is perfect for microservices and horizontally scaled backends.

**Disadvantage:** You can't revoke individual tokens before they expire. If a user's token is stolen, it's valid until the expiration time. Workaround: use short expiry times (15 minutes) combined with refresh tokens (long-lived tokens used only to get new short-lived tokens).

---

# PART 4: GIT

---

## 14. Git — What You Need to Know

Git is a distributed version control system. It tracks every change you make to your code, lets you go back to any previous version, and enables multiple people to work on the same codebase simultaneously without stepping on each other's toes. Every professional development team uses Git or a similar tool.

### The Basics

Git tracks changes in "commits" — snapshots of your code at a point in time. Each commit has a message describing what changed, a timestamp, and a pointer to the previous commit. This forms a chain (history) of all changes ever made.

The workflow is: make changes → stage them (choose what to include in the next commit) → commit them (save the snapshot) → push to remote (share with the team).

```bash
git init                    # new repo
git clone <url>             # copy remote repo
git status                  # what's changed
git add .                   # stage all changes
git commit -m "message"     # commit staged changes
git push origin main        # push to remote
git pull origin main        # fetch + merge from remote
```

### Branching

Branches let you work on features, fixes, or experiments in isolation without affecting the main codebase. A branch is just a pointer to a commit — creating one is instant and cheap.

```bash
git branch feature-x        # create branch
git checkout feature-x       # switch to it
git checkout -b feature-x    # create + switch (shortcut)
git merge feature-x          # merge into current branch
git branch -d feature-x      # delete branch
```

### The Git Workflow You Used at TechM

This is the standard Gitflow pattern used by most professional teams. Understanding this workflow is important because interviewers often ask "how does your team use Git?"

```
main (production)
  |
  +-- develop (integration)
       |
       +-- feature/add-login
       +-- feature/battery-api
       +-- bugfix/null-pointer
```

1. Create a feature branch from develop — this is your sandbox
2. Work on the feature, making commits as you go
3. Push the branch and create a Pull Request (PR) — a formal request to merge your changes
4. Team reviews the code (code review) — catches bugs, ensures quality
5. Merge to develop — your feature is now part of the integration branch
6. Periodically merge develop → main to create a release

### Merge vs Rebase

Both merge and rebase integrate changes from one branch into another, but they do it differently and produce different histories.

**Merge** creates a special "merge commit" that joins the two branches together. It preserves the complete history — you can see exactly when branches diverged and when they joined. The history looks like a river with tributaries flowing in.

```bash
git checkout main
git merge feature-x    # creates merge commit
```

**Rebase** replays your feature branch's commits on top of the target branch, as if you had started your work from the latest version of that branch. This produces a clean, linear history — no merge commits, no branching visible. It looks like everyone worked one after another in a straight line.

```bash
git checkout feature-x
git rebase main        # moves feature commits on top of main
git checkout main
git merge feature-x    # now a fast-forward (linear)
```

**The Golden Rule of Rebasing:** Never rebase commits that have already been pushed to a shared branch. Rebase rewrites commit history (changes commit hashes), which means anyone who based their work on the old commits will have conflicts. Rebase is safe for your local, unpushed feature branches only.

### Common Operations

```bash
git stash                   # save uncommitted changes temporarily
git stash pop               # restore stashed changes
git log --oneline           # compact history
git diff                    # see unstaged changes
git diff --staged           # see staged changes
git reset HEAD~1            # undo last commit (keep changes)
git reset --hard HEAD~1     # undo last commit (discard changes!) DANGEROUS
git cherry-pick <commit>    # apply specific commit to current branch
git revert <commit>         # create a new commit that undoes a previous commit (safe)
```

**`git stash`** is useful when you need to switch branches but have uncommitted work. It saves your changes to a temporary storage and restores a clean working directory. When you come back, `git stash pop` restores everything.

**`git reset` vs `git revert`:** Reset moves the branch pointer backward, effectively "erasing" commits from history. This is dangerous for shared branches because other people's work may depend on those commits. Revert is safe — it creates a NEW commit that undoes the changes of a previous commit. The original commit stays in history, and a new "undo" commit is added.

**`git cherry-pick`** applies a specific commit from one branch to another. Useful when you need just one bug fix from a feature branch without merging the entire branch.

### Merge Conflicts

Merge conflicts happen when two branches modify the same lines in the same file. Git can't automatically determine which version is correct, so it asks you to resolve the conflict manually.

```
<<<<<<< HEAD
your version of the line
=======
their version of the line
>>>>>>> feature-x
```

To resolve: read both versions, decide which is correct (or combine them), remove the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`), and commit the resolved file. Your IDE usually provides tools to make this easier.

Conflicts are normal and expected in team development. They're not a sign that something went wrong — just that two people worked on the same area of code.

### .gitignore

The `.gitignore` file tells Git which files and directories to completely ignore — they won't be tracked, staged, or committed. This is essential for keeping your repository clean.

```
__pycache__/
*.pyc
.env
node_modules/
.venv/
*.log
```

**What to ignore:** Generated files (compiled code, build artifacts), dependencies (node_modules — they can be reinstalled), secrets (.env files with passwords/API keys — NEVER commit these), IDE settings, log files, and OS-specific files (.DS_Store on Mac).

**Important:** Add .gitignore BEFORE your first commit. If you commit a file first and then add it to .gitignore, Git continues tracking it. You'd need to `git rm --cached <file>` to stop tracking it.

---

# PART 5: DOCKER

---

## 15. Docker — Containers Explained

### What Docker Solves

The classic problem: "It works on my machine but not on the server." This happens because your machine has specific versions of Python, specific libraries, specific OS settings — and the server has different ones. Docker solves this by packaging your application AND its entire environment (OS, language runtime, libraries, config) into a single portable unit called a container. The container runs identically everywhere — your laptop, your colleague's laptop, a test server, production.

### Images vs Containers

The relationship between images and containers is like the relationship between classes and objects in OOP:

**Image:** A read-only template that contains your app code, runtime, libraries, and configuration. It's built once from a Dockerfile. Think of it as a recipe or a blueprint.

**Container:** A running instance of an image. You can create multiple containers from the same image. Each container is isolated — it has its own filesystem, network, and process space. Think of it as a running application created from the blueprint.

```bash
docker build -t myapp .          # build image from Dockerfile
docker run -d -p 8080:5000 myapp  # run container (host:container port)
docker ps                         # list running containers
docker stop <id>                  # stop container
docker logs <id>                  # see container output
docker exec -it <id> bash         # shell into running container
```

`docker run -d -p 8080:5000 myapp` deserves explanation: `-d` runs in detached mode (background), `-p 8080:5000` maps port 8080 on your host machine to port 5000 inside the container. So accessing `localhost:8080` on your machine hits the app running on port 5000 inside the container.

### Dockerfile — The Recipe

A Dockerfile is a text file with instructions for building an image. Each instruction creates a "layer" — a cached snapshot of the filesystem at that point. Docker caches layers and only rebuilds layers that changed, which makes subsequent builds much faster.

```dockerfile
FROM python:3.11-slim             # base image
WORKDIR /app                      # set working directory
COPY requirements.txt .           # copy dependency file
RUN pip install -r requirements.txt  # install dependencies
COPY . .                          # copy app code
EXPOSE 5000                       # document the port
CMD ["python", "app.py"]          # default command when container starts
```

**Layer caching is crucial for build speed.** Docker rebuilds a layer and ALL layers after it whenever that layer changes. That's why you copy `requirements.txt` and install dependencies BEFORE copying your app code. Dependencies change rarely; your code changes with every build. By separating them, `pip install` only reruns when `requirements.txt` changes — saving minutes on every build.

### Docker Compose — Multi-Container Setup

Real applications need multiple services: your app, a database, a cache, maybe a message queue. Docker Compose lets you define and run all of them together in one configuration file. Instead of manually starting each container with specific flags, you define everything in `docker-compose.yml` and run one command.

```yaml
# docker-compose.yml
version: '3'
services:
  web:
    build: .
    ports:
      - "8080:5000"
    environment:
      - DATABASE_URL=postgres://db:5432/myapp
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: myapp
      POSTGRES_PASSWORD: secret
    volumes:
      - db_data:/var/lib/postgresql/data

  redis:
    image: redis:7

volumes:
  db_data:
```

```bash
docker-compose up -d     # start all services
docker-compose down      # stop all services
docker-compose logs web  # logs for specific service
```

### Docker Networking

Docker Compose automatically creates a network for all your services. Containers on the same network can reach each other by service name — Docker provides built-in DNS resolution. Your `web` container connects to the database as `db:5432` — Docker resolves `db` to the database container's internal IP address automatically. You never need to know or manage IP addresses.

### Volumes — Persistent Storage

Containers are ephemeral by design — when a container is stopped or removed, all data inside it is lost. This is a feature, not a bug — it ensures clean, reproducible environments. But databases need persistent storage. Volumes solve this by storing data outside the container's lifecycle.

```yaml
volumes:
  - db_data:/var/lib/postgresql/data    # named volume (managed by Docker)
  - ./config:/app/config                # bind mount (host directory)
```

**Named volumes** are managed by Docker — they persist data in a Docker-managed location on the host. **Bind mounts** map a specific directory on your host machine into the container — useful for development (edit code on your machine, see changes in the container immediately).

---

# PART 6: LINUX / SHELL

---

## 16. Linux Commands You Need to Know

As a backend developer managing 80+ production servers at TechM, Linux command-line skills are essential. You SSH into servers, check logs, monitor processes, and troubleshoot issues — all from the terminal.

### File Operations

These are the commands you'll use dozens of times a day:

```bash
ls -la                    # list with details and hidden files
cd /path/to/dir           # change directory
pwd                       # current directory
mkdir -p dir/subdir       # create nested directories
cp file.txt backup.txt    # copy
mv old.txt new.txt        # rename/move
rm file.txt               # delete file
rm -rf directory/         # delete directory recursively (CAREFUL!)
cat file.txt              # print file contents
head -20 file.txt         # first 20 lines
tail -f app.log           # follow log file in real-time
```

`tail -f app.log` is one of the most useful commands for debugging in production. The `-f` flag means "follow" — it keeps the file open and shows new lines as they're appended. You can watch your application's logs in real-time as requests come in. `Ctrl+C` to stop following.

### Search and Filter

These commands help you find files and search through content — essential for debugging when you need to find error messages in logs or locate specific code:

```bash
grep "ERROR" app.log              # find lines containing "ERROR"
grep -r "TODO" src/               # recursive search in directory
grep -i "error" app.log           # case-insensitive
grep -c "ERROR" app.log           # count matches
find . -name "*.py"               # find files by name
find . -name "*.log" -mtime +30   # files modified 30+ days ago
wc -l file.txt                    # count lines
```

`grep` is the single most important search tool on Linux. It searches for patterns in text. You'll use it constantly to filter logs, find configuration values, and search codebases.

### Pipes and Redirection

Pipes (`|`) connect the output of one command to the input of another, creating a processing pipeline. This is the Unix philosophy — small programs that do one thing well, chained together to accomplish complex tasks. Each program processes the stream of text and passes it to the next.

```bash
cat app.log | grep "ERROR" | wc -l          # count error lines
cat app.log | grep "ERROR" | sort | uniq    # unique error messages
ps aux | grep python                         # find python processes

echo "hello" > file.txt    # write (overwrite)
echo "world" >> file.txt   # append
command 2>&1               # redirect stderr to stdout
command > /dev/null 2>&1   # suppress all output
```

`>` overwrites the file; `>>` appends. `2>&1` redirects error output (file descriptor 2) to the same place as normal output (file descriptor 1). `/dev/null` is a "black hole" — anything written to it is discarded. `command > /dev/null 2>&1` runs a command silently, discarding all output.

### Process Management

These commands help you monitor and control running processes:

```bash
ps aux                     # list all processes
ps aux | grep python       # find specific process
kill <pid>                 # graceful stop (SIGTERM -- process can clean up)
kill -9 <pid>              # force kill (SIGKILL -- immediate, no cleanup)
top / htop                 # live process monitor
nohup python app.py &      # run in background, survives logout
```

`kill <pid>` sends SIGTERM, which asks the process to shut down gracefully — it can save state, close connections, and exit cleanly. `kill -9 <pid>` sends SIGKILL, which terminates immediately with no chance to clean up. Always try `kill` first; use `kill -9` only when a process is stuck.

`nohup command &` runs a command in the background and prevents it from being killed when you log out. `nohup` means "no hangup signal." `&` puts it in the background. You used PM2 at TechM, which is essentially a more sophisticated version of this for Node.js processes.

### Networking

These commands help you test network connectivity, make HTTP requests, and check what's listening on ports:

```bash
curl http://localhost:8080/api/health     # make HTTP request
curl -X POST -H "Content-Type: application/json" -d '{"key":"val"}' URL
wget https://example.com/file.zip        # download file
netstat -tlnp                            # list open ports
ss -tlnp                                 # modern netstat
ping google.com                          # check connectivity
```

`curl` is essential for testing APIs from the command line. `-X` sets the HTTP method, `-H` adds headers, `-d` sends request body data. You can test any API endpoint directly from the terminal without needing Postman or a browser.

### Permissions

Linux has a permission system that controls who can read, write, or execute files. Every file has three sets of permissions: owner, group, and others.

```bash
chmod 755 script.sh        # rwxr-xr-x (owner: all, others: read+execute)
chmod +x script.sh         # make executable
chown user:group file.txt  # change owner
```

**Permission numbers explained:** read=4, write=2, execute=1. You add them together for each category.
- 7 = 4+2+1 = read+write+execute (full access)
- 5 = 4+0+1 = read+execute (no write)
- 4 = 4+0+0 = read only

So 755 means: owner gets 7 (rwx), group gets 5 (r-x), others get 5 (r-x). This is the standard permission for scripts and executables — the owner can modify them, everyone else can run them.

### SSH — Remote Server Access

SSH (Secure Shell) is how you connect to remote servers securely. All communication is encrypted. You manage 80+ production servers at TechM via SSH.

```bash
ssh user@server.com                      # connect
ssh -i key.pem user@server.com           # with key file
scp file.txt user@server.com:/path/      # copy file to server
scp user@server.com:/path/file.txt .     # copy from server
```

`scp` (secure copy) transfers files between your machine and a remote server over SSH. It uses the same authentication and encryption as SSH.

---

# PART 7: DESIGN PATTERNS & SOLID

---

## 17. SOLID Principles

SOLID is a set of five design principles that help you write code that's maintainable, flexible, and testable. They're named by Robert C. Martin ("Uncle Bob") and are a very common interview topic. You don't need to follow them dogmatically, but understanding them helps you recognize and avoid common design problems.

### S — Single Responsibility Principle

Each class or function should have ONE reason to change — it should do one thing and do it well. If a class handles user data, sends emails, AND generates reports, it has three reasons to change. Changing the email format shouldn't risk breaking the report generator.

```python
# BAD:
class User:
    def save_to_db(self): ...
    def send_email(self): ...
    def generate_report(self): ...

# GOOD:
class User: ...
class UserRepository:
    def save(self, user): ...
class EmailService:
    def send(self, user, message): ...
```

Splitting responsibilities into separate classes means each can change independently, be tested independently, and be reused independently. The User class only knows about user data. The UserRepository only knows about database operations. The EmailService only knows about sending emails.

### O — Open/Closed Principle

Classes should be open for extension (you can add new behavior) but closed for modification (you don't change existing code). This means when a new requirement comes in, you add new code rather than modifying existing, tested code.

```python
# BAD: adding a new shape requires modifying the function
def area(shape):
    if shape.type == "circle": return 3.14 * shape.r ** 2
    elif shape.type == "rect": return shape.w * shape.h
    # add more elif for every new shape...

# GOOD: each shape knows how to compute its own area
class Shape(ABC):
    @abstractmethod
    def area(self): pass

class Circle(Shape):
    def area(self): return 3.14 * self.r ** 2

class Rectangle(Shape):
    def area(self): return self.w * self.h
```

In the bad version, adding a Triangle requires modifying the `area` function — which means retesting it, risking bugs in existing circle/rectangle logic, and potentially breaking things. In the good version, adding a Triangle means creating a new class. Existing code doesn't change at all.

### L — Liskov Substitution Principle

Any subclass should be usable wherever its parent class is expected, without surprising behavior. If your code works with `Animal`, it should work with `Dog` (a subclass of Animal) without any errors or unexpected outcomes.

A `Dog` shouldn't override `speak()` to throw an error or return an integer when the parent's `speak()` returns a string. The subclass should honor the contract established by the parent — same parameter types, same return types, same behavior guarantees.

A classic violation: a `Square` class that inherits from `Rectangle`. Setting the width of a rectangle doesn't change its height, but setting the width of a square MUST change its height too. This means `Square` breaks the expectations of `Rectangle`, violating Liskov.

### I — Interface Segregation Principle

Don't force classes to implement methods they don't need. If you have a large interface with many methods, split it into smaller, focused interfaces so that implementors only deal with the methods relevant to them.

```python
# BAD: Printer forced to implement scan() and fax()
class AllInOne(ABC):
    @abstractmethod
    def print(self): pass
    @abstractmethod
    def scan(self): pass
    @abstractmethod
    def fax(self): pass

# GOOD: separate interfaces
class Printable(ABC):
    @abstractmethod
    def print(self): pass

class Scannable(ABC):
    @abstractmethod
    def scan(self): pass
```

In the bad version, a simple printer that can only print is forced to implement `scan()` and `fax()` — probably with empty methods or raising NotImplementedError. This is a sign that the interface is too broad. Splitting into smaller interfaces means each class only commits to what it can actually do.

### D — Dependency Inversion Principle

High-level modules (business logic) should not depend on low-level modules (infrastructure). Both should depend on abstractions (interfaces). This means your UserService shouldn't directly create a `PostgreSQLDatabase` object — it should receive a `Database` abstraction that could be PostgreSQL, MySQL, or a mock for testing.

```python
# BAD: directly depends on PostgreSQL
class UserService:
    def __init__(self):
        self.db = PostgreSQLDatabase()

# GOOD: depends on abstraction
class UserService:
    def __init__(self, db: Database):  # any Database implementation works
        self.db = db

# Can inject PostgreSQL, MySQL, MockDB for testing...
```

This principle enables: (1) easy testing — inject a mock database during tests, no real database needed; (2) flexibility — switch from PostgreSQL to MySQL by just passing a different implementation; (3) decoupling — UserService doesn't import or know about PostgreSQL at all.

---

## 18. Common Design Patterns

Design patterns are proven solutions to common software design problems. You don't need to memorize all 23 Gang of Four patterns, but knowing these five will cover most interview questions and real-world scenarios.

### Singleton — One Instance Only

The Singleton pattern ensures that a class has only one instance throughout the application, and provides a global access point to it. Useful for things that should exist exactly once — a database connection pool, a configuration manager, a logger.

```python
class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

db1 = DatabaseConnection()
db2 = DatabaseConnection()
db1 is db2  # True
```

By overriding `__new__`, we check if an instance already exists before creating a new one. Every call to `DatabaseConnection()` returns the same object. Note: Singletons are controversial because they're essentially global state, which makes testing harder. In modern Python, module-level variables or dependency injection are often preferred alternatives.

### Factory — Create Objects Without Specifying Exact Class

The Factory pattern provides a method for creating objects without the caller needing to know the exact class being instantiated. The caller says "I need a notification for this channel" and the factory decides which specific class to create.

```python
class NotificationFactory:
    @staticmethod
    def create(channel):
        if channel == "email": return EmailNotification()
        elif channel == "sms": return SMSNotification()
        elif channel == "push": return PushNotification()
        raise ValueError(f"Unknown channel: {channel}")

notif = NotificationFactory.create("email")
notif.send("Hello!")
```

The benefit: the rest of your code works with the `Notification` interface and doesn't need to know about `EmailNotification`, `SMSNotification`, etc. Adding a new notification type means updating only the factory — all other code stays the same. This is the Open/Closed Principle in action.

### Observer — Notify Multiple Listeners of Changes

The Observer pattern defines a one-to-many relationship: when one object changes state, all registered listeners are automatically notified. Think of it like a YouTube channel — when a new video is uploaded, all subscribers are notified.

```python
class EventEmitter:
    def __init__(self):
        self._listeners = defaultdict(list)

    def on(self, event, callback):
        self._listeners[event].append(callback)

    def emit(self, event, data):
        for callback in self._listeners[event]:
            callback(data)

emitter = EventEmitter()
emitter.on("user_created", send_welcome_email)
emitter.on("user_created", update_analytics)
emitter.emit("user_created", {"name": "Vishal"})
```

This decouples the event source from the event handlers. The code that creates users doesn't need to know about welcome emails or analytics — it just emits an event, and whoever cares can listen. Adding a new reaction to user creation (like sending a Slack notification) requires zero changes to the user creation code.

### Strategy — Swap Algorithms at Runtime

The Strategy pattern lets you define a family of algorithms, encapsulate each one, and swap between them at runtime. Instead of hardcoding an algorithm, you pass it as a parameter — making the behavior configurable.

```python
class Sorter:
    def __init__(self, strategy):
        self.strategy = strategy

    def sort(self, data):
        return self.strategy(data)

sorter = Sorter(strategy=sorted)            # use built-in
sorter = Sorter(strategy=custom_sort_func)  # use custom
```

In Python, the Strategy pattern is often implemented naturally using first-class functions — you pass a function as an argument. In Java, you'd need to create a Strategy interface and implementing classes. Python's flexibility makes this pattern almost invisible because it's so easy.

### Decorator Pattern (not Python's @decorator)

The Decorator pattern wraps an object to add behavior without modifying the original class. It's called "Decorator" in the design pattern world, but it's different from Python's `@decorator` syntax (though the concept is related).

```python
class LoggingDB:
    def __init__(self, db):
        self.db = db

    def query(self, sql):
        print(f"Executing: {sql}")
        return self.db.query(sql)
```

`LoggingDB` wraps any database object and adds logging. The original database class is unchanged. You can stack decorators: `LoggingDB(CachingDB(PostgreSQL()))` — each layer adds behavior. This is composition over inheritance — adding behavior by wrapping instead of subclassing.

---

# PART 8: NETWORKING

---

## 19. Networking Fundamentals

Understanding how networks work is essential for debugging connectivity issues, understanding latency, and designing distributed systems.

### How a Web Request Works

When you type `example.com` in your browser, a complex chain of events happens in milliseconds:

```
1. You type example.com in browser
2. DNS lookup: example.com -> 93.184.216.34 (IP address)
3. TCP handshake: browser <-> server establish connection
4. HTTP request sent over TCP connection
5. Server processes request, sends HTTP response
6. Browser renders the response
```

Step 2 (DNS) translates the human-friendly domain name to a machine-friendly IP address. Step 3 (TCP handshake) is a three-way process where the client and server agree to communicate (SYN, SYN-ACK, ACK). Step 4 sends the actual HTTP request over the established TCP connection. Steps 2-3 only happen for the first request — subsequent requests to the same server reuse the existing connection (HTTP keep-alive).

### TCP vs UDP

These are two transport layer protocols — they define HOW data is sent over the network. They make very different trade-offs between reliability and speed.

**TCP (Transmission Control Protocol):** Guarantees that data arrives, arrives in the correct order, and isn't corrupted. It achieves this through acknowledgments (the receiver confirms each chunk of data), retransmissions (sender re-sends if no acknowledgment arrives), and sequencing (each chunk is numbered so they can be reordered if they arrive out of order). The cost is overhead — all these guarantees require extra communication.
- Connection-oriented: requires a three-way handshake to establish a connection before sending data
- Used for: HTTP/HTTPS (web), SSH (remote access), database connections, email — anything where correctness matters

**UDP (User Datagram Protocol):** Just sends data with no guarantees. No acknowledgments, no retransmissions, no ordering. Packets might arrive out of order, might be duplicated, or might be lost entirely. The benefit is speed — no connection setup, no waiting for acknowledgments, minimal overhead.
- Connectionless: just send packets; no handshake needed
- Used for: video streaming (a dropped frame is fine), online gaming (old position data is useless anyway), DNS lookups (small, single-packet queries), VoIP (real-time audio can't wait for retransmissions)

### DNS — Domain Name System

DNS is the internet's phone book. It translates human-readable domain names (example.com) to machine-readable IP addresses (93.184.216.34). Without DNS, you'd have to memorize IP addresses for every website.

```
example.com -> DNS Resolver -> Root DNS -> .com DNS -> example.com DNS -> 93.184.216.34
```

The lookup follows a hierarchy: your computer asks a DNS resolver (usually your ISP's), which asks a root DNS server, which directs to the `.com` TLD (top-level domain) server, which directs to the authoritative DNS server for `example.com`, which returns the IP address.

This result is cached at multiple levels — browser cache, OS cache, ISP cache — so subsequent lookups for the same domain are nearly instant. Each cached entry has a TTL (time to live) after which it expires and triggers a fresh lookup.

### HTTPS and TLS

HTTPS is HTTP with encryption provided by TLS (Transport Layer Security). All data between client and server is encrypted, preventing anyone in the middle (ISPs, WiFi snoopers, hackers) from reading or modifying the communication.

The TLS handshake establishes a shared encryption key using an elegant combination of asymmetric and symmetric encryption:

```
1. Client: "Hello, I want HTTPS" (ClientHello, lists supported encryption methods)
2. Server: sends its TLS certificate (contains public key, verified by a Certificate Authority)
3. Client: verifies the certificate is genuine, generates a random session key,
   encrypts it with the server's public key, sends it
4. Server: decrypts the session key with its private key (only the server has this)
5. Both sides: use the session key for symmetric encryption (AES — very fast)
```

Why two types of encryption? Asymmetric encryption (public/private key) is secure for key exchange but slow for bulk data. Symmetric encryption (shared key) is very fast but requires both sides to have the same key. TLS uses asymmetric just to securely share the symmetric key, then uses symmetric for everything else. Best of both worlds.

### WebSockets

HTTP follows a request-response pattern: the client asks, the server answers, and the conversation ends. If the client wants updates, it must ask again (polling). This is wasteful for real-time applications.

WebSocket provides a persistent, full-duplex connection between client and server. Once established, either side can send messages at any time without the overhead of establishing new connections. The connection stays open until explicitly closed.

Used for: chat applications (messages appear instantly), live dashboards (data updates in real-time), real-time notifications, collaborative editing (Google Docs), online gaming, and stock tickers.

### REST vs GraphQL vs gRPC

These are three different approaches to API communication, each with different strengths:

**REST:** Resource-based URLs, standard HTTP methods, JSON payloads. The most common API style and what you use daily. Simple, well-understood, cacheable (GET requests can be cached by proxies and CDNs). Drawback: over-fetching (GET /user returns ALL user fields even if you only need the name) and under-fetching (you need separate requests for related data).

**GraphQL:** A query language that lets the client specify exactly which fields it needs. One endpoint handles all requests. The client sends a query like `{ user(id: 1) { name, email } }` and gets back only those fields. Avoids over-fetching and under-fetching. Drawback: more complex server implementation, harder to cache, potential for expensive queries that clients can construct.

**gRPC:** A binary protocol using Protocol Buffers (Protobuf) instead of JSON. Much faster than REST (binary is smaller and faster to parse than text JSON). Uses HTTP/2 features like streaming and multiplexing. Primarily used for high-performance service-to-service communication within a backend, not for browser-to-server communication. Drawback: not human-readable, requires code generation from `.proto` files.

---

# PART 9: OS CONCEPTS

---

## 20. Operating System Concepts

These OS concepts come up in backend interviews because they directly affect how your applications perform — especially when dealing with concurrency, memory management, and process management.

### Process vs Thread

A **process** is an independent running program with its own memory space (address space). Two processes cannot directly access each other's memory — they're isolated by the operating system. This isolation provides safety (a bug in one process can't corrupt another) but makes communication harder. Processes communicate via Inter-Process Communication (IPC) mechanisms like pipes, sockets, shared memory, or files.

A **thread** is a lightweight unit of execution within a process. Multiple threads within the same process share the same memory space — they can read and write the same variables directly. This makes communication between threads trivially easy (just use shared variables) but introduces the risk of concurrency bugs like race conditions (two threads modifying the same variable simultaneously).

Creating a new thread is much cheaper than creating a new process (no need to duplicate the memory space), and switching between threads is faster than switching between processes.

**In Python context:**
- `multiprocessing` = separate processes, separate memory, true parallelism (each process has its own GIL)
- `threading` = separate threads, shared memory, limited by GIL (only one thread runs Python code at a time)

### Concurrency vs Parallelism

These two terms are often confused but mean different things.

**Concurrency** means multiple tasks are making progress, but not necessarily at the exact same instant. They might be interleaved — the OS switches between them rapidly, creating the illusion of simultaneous execution. One CPU core can handle concurrent tasks by time-slicing. Think of a single chef preparing two dishes by switching between them.

**Parallelism** means multiple tasks are literally executing at the same instant, on different CPU cores. Two CPU cores each running a different task simultaneously. Think of two chefs each working on their own dish at the same time.

Threading in Python = concurrent (the GIL allows only one thread to execute Python code at a time, so threads take turns on one core). Multiprocessing in Python = parallel (each process runs on its own core with its own GIL, achieving true simultaneous execution).

### Virtual Memory and Paging

Physical RAM is limited and expensive. Virtual memory creates the illusion of having more memory than physically available by using disk space as an extension of RAM.

**How it works:** Memory is divided into fixed-size chunks called pages (typically 4KB). Each process thinks it has its own contiguous memory space, but the OS maps these virtual pages to physical RAM pages. When a process needs a page that isn't currently in RAM (because RAM is full), the OS loads it from disk — this is called a "page fault." To make room, the OS swaps an unused page from RAM to disk.

**Why page faults matter:** Disk access is approximately 100,000x slower than RAM access. A page fault that loads from disk takes milliseconds — an eternity for a CPU that operates in nanoseconds. If your system has too many page faults (more data than RAM can hold, constantly swapping pages in and out), performance collapses. This is called "thrashing" — the system spends all its time swapping pages instead of doing useful work.

### Context Switching

When the OS switches from running Process A to Process B, it must save A's entire state (register values, program counter, stack pointer) and load B's previously saved state. This is a context switch, and it has a real cost — typically a few microseconds per switch, which adds up quickly.

1. Save Process A's state (CPU registers, program counter, stack pointer) to memory
2. Load Process B's previously saved state from memory
3. Resume Process B from where it left off

If you have too many threads or processes competing for CPU time, the OS spends a significant portion of time just switching between them rather than doing productive work. This is why creating 10,000 OS threads is a bad idea — the context switching overhead dominates. This is also why asyncio (which uses cooperative multitasking with negligible switching cost) is preferred for high-concurrency I/O workloads.

### Deadlock Conditions (Coffman)

A deadlock occurs when two or more processes are stuck waiting for each other forever — none can proceed because each holds a resource the other needs. The Coffman conditions describe the four conditions that must ALL be present simultaneously for a deadlock to occur:

1. **Mutual Exclusion:** At least one resource can only be used by one process at a time (it can't be shared). Example: a database row lock — only one transaction can hold it.
2. **Hold and Wait:** A process holds at least one resource while waiting to acquire another resource that's currently held by a different process.
3. **No Preemption:** Resources cannot be forcibly taken from a process — they can only be released voluntarily by the process holding them.
4. **Circular Wait:** A circular chain of processes exists where each process holds a resource that the next process in the chain needs. Process A waits for B's resource, B waits for C's resource, C waits for A's resource.

**Prevention strategies:** Break any one of the four conditions to prevent deadlocks. The most practical approach is preventing circular wait by imposing a global ordering — always acquire locks in the same order (e.g., by resource ID ascending). If every process acquires Lock A before Lock B, the circular dependency can never form.

---

# PART 10: BEHAVIORAL / HR

---

## 21. Behavioral Questions — STAR Format

Behavioral questions assess your soft skills — how you communicate, handle conflict, deal with failure, and work in a team. These are just as important as technical skills because you'll be working with people, not just code.

**STAR = Situation, Task, Action, Result**

Every behavioral answer should follow this structure. STAR keeps your answers focused and concrete instead of vague and rambling. Be specific — use real examples from XenonStack and TechM with actual details (technologies, metrics, outcomes).

**Situation:** Set the context — what was happening, what was the project, what was the challenge.
**Task:** What was YOUR responsibility specifically — not the team's goal, but YOUR role.
**Action:** What did YOU do — specific steps, decisions, and actions YOU took.
**Result:** What happened — quantifiable outcomes, lessons learned, impact.

### "Tell me about yourself" (60-second pitch)

This is always the first question. Have a rehearsed, natural-sounding 60-second pitch that covers who you are, what you've done, and what you're looking for. Don't read your entire resume — hit the highlights.

"I'm Vishal, a Backend Software Engineer with about 4 years of experience.
I started at XenonStack as a Data Engineer building real-time fraud detection pipelines
using Kafka, Spark, and ArangoDB. Currently at Tech Mahindra, I work on the TMDC platform —
Python microservices with Flask and FastAPI, managing 80+ production servers, and building
CI/CD pipelines with GitHub Actions. I have a B.Tech in Computer Science from IKG PTU."

### "Tell me about a challenging project"

**Situation:** At XenonStack, the UPI fraud detection system was catching fraud hours late
because it relied on batch processing.
**Task:** I needed to build a real-time pipeline that detected fraud within seconds.
**Action:** Set up Debezium for CDC from PostgreSQL, streamed events through Kafka,
built graph-based fraud detection in ArangoDB, and loaded results into Synapse for Power BI.
**Result:** Fraud detection went from hours to seconds. Data pipeline efficiency improved 40%.

### "How do you handle disagreements?"

**Situation:** At TechM, a colleague wanted to use a monolith for a new service, I recommended microservices.
**Task:** Reach a decision without damaging the relationship.
**Action:** I prepared a comparison document with pros/cons of each approach for our specific use case.
Presented it in a team meeting, invited feedback, acknowledged the valid concerns about microservice complexity.
**Result:** Team agreed on microservices with simplified deployment. We documented the decision rationale.

### "Describe a time you failed / made a mistake"

This question tests self-awareness and learning ability. Everyone fails — interviewers want to see that you take responsibility, learn from mistakes, and put systems in place to prevent repetition.

**Situation:** Deployed a code change to production at TechM that caused an API to return 500 errors.
**Task:** Fix it fast, understand what went wrong.
**Action:** Immediately rolled back using our CI/CD pipeline. Wrote a post-mortem documenting the root cause
(untested edge case with null values). Added the missing test case. Proposed a staging environment check.
**Result:** Downtime was under 15 minutes. The new testing process caught 3 similar bugs before they reached production.

### More Questions to Prepare

For each of these, prepare a specific STAR story from your real experience:

- **"Why are you leaving your current job?"** — Always frame positively. Focus on growth, new challenges, learning opportunities. Never badmouth your current employer.
- **"Where do you see yourself in 5 years?"** — Show ambition but be realistic. Growing into a senior/lead engineer role, deepening technical expertise, possibly mentoring.
- **"How do you prioritize when you have multiple deadlines?"** — Talk about your actual prioritization method: urgency vs importance, communicating with stakeholders, breaking work into smaller pieces.
- **"Describe a time you mentored someone or helped a teammate"** — Shows leadership potential and collaboration skills.
- **"How do you handle pressure?"** — Demonstrate calmness and systematic problem-solving, not "I just work harder."
- **"What's your approach to learning a new technology?"** — Show your learning process: documentation, small projects, real-world application.
- **"Tell me about a time you improved a process"** — This is a great place to mention your CI/CD work, automation, or pipeline optimization.

### Questions You Should Ask the Interviewer

Always have questions prepared. Asking thoughtful questions shows genuine interest and helps you evaluate whether you actually want to work there. Ask questions that can't be answered by reading the company's website.

- "What does a typical day look like for this role?"
- "What's the team structure and how are technical decisions made?"
- "What's the tech stack? Any plans to change or modernize it?"
- "How do you handle deployments and incidents?"
- "What does growth/promotion look like here?"
- "What's the biggest challenge the team is facing right now?"

---

# PART 11: MISCELLANEOUS

---

## 22. NGINX — Quick Reference (From Your TechM Work)

NGINX is a high-performance web server, reverse proxy, and load balancer. At Tech Mahindra, it sits in front of your Python (Flask/FastAPI) and Node.js (Express) services, acting as the single entry point for all external traffic.

```nginx
# Reverse proxy:
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /var/www/static/;    # serve static files directly
    }
}
```

**What NGINX does for you at TechM — and why each matters:**

- **Reverse proxy:** Routes external requests to your internal Python/Node services. External clients talk to NGINX on port 80/443; NGINX forwards to your app on port 5000. This hides your application's internal structure from the outside world and provides a layer of security.
- **Load balancing:** If you have multiple instances of your app running, NGINX distributes requests across them. If one instance crashes, NGINX stops sending traffic to it automatically.
- **SSL termination:** NGINX handles HTTPS encryption/decryption, then forwards plain HTTP to your backend. This means your application code doesn't need to deal with certificates or TLS at all — NGINX handles the complexity.
- **Static file serving:** CSS, JavaScript, images, and other static files are served directly by NGINX without hitting your application. NGINX is extremely fast at serving files — your Python app shouldn't waste time on this.
- **Rate limiting:** NGINX can limit how many requests each IP address can make per second, protecting your backend services from abuse or accidental overload.

---

## 23. CI/CD — What You Should Know

CI/CD is the practice of automating the build, test, and deployment process. Instead of manually building, testing, and deploying code (which is slow, error-prone, and inconsistent), automation handles it every time code is pushed.

### What CI/CD Means

**CI (Continuous Integration):** Every code push automatically triggers a build and runs the test suite. This catches bugs immediately — within minutes of the developer pushing code — rather than days or weeks later when someone manually tests. The key benefit is fast feedback: you know immediately if your change broke something. You used GitHub Actions for this at TechM.

**CD (Continuous Delivery):** After CI passes (code builds and tests pass), the code is automatically deployed to a staging environment. Production deployment still requires a manual approval step. This ensures that the code in staging is always deployable — you can release to production at any time with confidence.

**CD (Continuous Deployment):** Goes one step further — after CI passes, code is automatically deployed to production with no manual step. This requires very high confidence in your test suite because there's no human gatekeeping production deploys. Companies like Netflix and Amazon practice continuous deployment.

### Your GitHub Actions Pipeline at TechM

```yaml
name: CI/CD
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: pytest tests/

  deploy:
    needs: test          # only runs after tests pass
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: ssh deploy@server "cd /app && git pull && systemctl restart app"
```

This pipeline has two jobs: `test` runs pytest on every push and PR. `deploy` only runs after tests pass (`needs: test`) and only on the main branch (`if: github.ref == 'refs/heads/main'`). It SSHes into the production server, pulls the latest code, and restarts the application.

### Blue-Green Deployment

Blue-Green is a zero-downtime deployment strategy. You maintain two identical production environments: Blue (currently serving traffic) and Green (idle, used for deploying the new version).

Process: Deploy the new version to Green. Test it thoroughly in the Green environment. Once verified, switch the load balancer to point traffic from Blue to Green. Green is now production. If something breaks, switch back to Blue instantly — it still has the old, working version. Zero downtime throughout.

The trade-off is cost — you need to maintain two full production environments. But for critical applications, the ability to roll back in seconds (just switch the load balancer) is worth it.

### Canary Deployment

Canary deployment is a gradual rollout strategy named after the "canary in a coal mine" — you send a small group in first to test for danger before committing everyone.

Process: Route a small percentage of traffic (e.g., 5%) to the new version. Monitor error rates, response times, and key metrics closely. If everything looks healthy, gradually increase: 10%, 25%, 50%, 100%. If metrics show problems at any stage, roll back immediately. Only the small percentage of users at the canary stage were affected.

This is safer than deploying to all users at once because problems are caught early with minimal user impact. Many companies combine canary with feature flags for even more granular control.

---

## 24. Regex — Quick Reference (From Your Packet Parsing Work)

Regular expressions (regex) are patterns for matching text. They're powerful for parsing logs, validating input, extracting data from strings, and — in your case at TechM — parsing network packet data.

Regex looks intimidating but it follows consistent rules. Think of it as a pattern description language: "I'm looking for a digit followed by a letter followed by three more digits."

```python
import re

# Common patterns:
re.search(r'\d+', 'age: 26')           # finds '26'
re.findall(r'\d+', 'a1b2c3')           # ['1', '2', '3']
re.sub(r'\s+', ' ', 'too   many  spaces')  # 'too many spaces'
re.match(r'^Hello', 'Hello World')      # matches at start only

# Groups -- capture specific parts of the match:
match = re.search(r'(\d{4})-(\d{2})-(\d{2})', '2023-08-01')
match.group(1)   # '2023'
match.group(2)   # '08'

# Named groups -- more readable than numbered groups:
match = re.search(r'(?P<year>\d{4})-(?P<month>\d{2})', '2023-08')
match.group('year')   # '2023'

# Compile for performance (reuse pattern):
pattern = re.compile(r'ERROR: (.+)')
results = pattern.findall(log_content)
```

`re.compile()` is important for performance when you use the same pattern multiple times (like in a loop processing thousands of log lines). It compiles the pattern once into an internal representation that's faster to execute repeatedly.

`re.search()` finds the first match anywhere in the string. `re.match()` only matches at the beginning. `re.findall()` returns all matches. `re.sub()` replaces matches with a replacement string.

**Cheat sheet — what each symbol means:**
```
\d  = digit (0-9)       \D = non-digit (anything except 0-9)
\w  = word char (a-z, A-Z, 0-9, _)     \W = non-word character
\s  = whitespace (space, tab, newline)    \S = non-whitespace
.   = any single character (except newline by default)
^   = start of string     $  = end of string
*   = 0 or more of the preceding element (greedy)
+   = 1 or more of the preceding element (greedy)
?   = 0 or 1 of the preceding element (optional)
{n} = exactly n occurrences     {n,m} = between n and m occurrences
[]  = character set (match any one character inside)
[^] = negated set (match any character NOT inside)
|   = or (alternation)     () = group (capture and/or grouping)
```

---

## 25. Quick Checklist — What to Review Before Each Interview

### Coding Round
- [ ] Two pointers, sliding window
- [ ] HashMap problems (two sum, anagrams, frequency)
- [ ] Linked list (reverse, cycle detection, merge)
- [ ] Stack (valid parentheses, monotonic stack)
- [ ] Binary search (sorted array, lower/upper bound)
- [ ] BFS/DFS (trees and graphs)
- [ ] Basic DP (fibonacci, climbing stairs, knapsack)
- [ ] Sorting (know merge sort, know complexities)
- [ ] Know Python's built-in helpers: sorted, heapq, Counter, defaultdict, deque

### Technical Round
- [ ] Python concepts (mutability, decorators, GIL, generators, OOP)
- [ ] SQL (JOINs, window functions, CTEs, NULL traps, optimization)
- [ ] REST APIs (HTTP methods, status codes, auth)
- [ ] System design basics (caching, load balancing, DB scaling, message queues)
- [ ] Docker (Dockerfile, compose, volumes)
- [ ] Git (branching, merge vs rebase, conflict resolution)
- [ ] SOLID principles
- [ ] Your resume — explain every bullet point in detail

### Behavioral Round
- [ ] "Tell me about yourself" (60-second pitch rehearsed)
- [ ] 3-4 STAR stories ready (challenge, failure, disagreement, achievement)
- [ ] Why leaving current job (positive framing)
- [ ] Questions to ask the interviewer (prepared)

---

*Last updated: August 2026*
