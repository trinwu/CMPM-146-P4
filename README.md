# P4-HTN-Planning-for-Minecraft

## **Team Members**
- Trinity Wu  
- Shaoan Wang  

## **Submission Files**
- **manualHTN.py**: Solves case (1) from the problem description.  
- **autoHTN.py**: Solves cases in (5), programmatically creating methods and operators.  
- **README.md**: Describes the heuristics implemented and their roles in the planner.  
- **(Optional Extra Credit)**: `custom_case.txt`, which states a custom problem for case (6).  

---

## **Code Modifications**

### **manualHTN.py**  
- Optimized task execution logic to improve performance and planning efficiency.

### **autoHTN.py**  
- Added dynamic generation of methods and operators to enhance flexibility:
  - **make_operator()**:  
    1. Verifies if the agent has sufficient time and resources to perform tasks.  
    2. Updates the state by consuming required resources and producing new items.  
  - **make_method()**:  
    1. Creates subtasks to ensure all necessary resources are available.  
    2. Executes corresponding operators for crafting.  
  - **declare_methods()** and **declare_operators()**:  
    - Automate the declaration of new crafting methods and operators based on input data.
  - **add_heuristic()**:  
    1. Limits recursion depth to prevent infinite loops.  
    2. Prevents excessive intermediate item creation, improving plan efficiency.  

Search Space Pruning
The primary heuristic implemented in add_heuristic() prevents infinite recursion and manages computational resources through two main constraints:

python
def heuristic(state, curr_task, tasks, plan, depth, calling_stack):
    # Prevent excessive depth
    if depth > 10:
        return True

    Prevent overly long plans
    if len(plan) > 30:
        return True

    return False

Depth Limitation

Sets a maximum depth of 10 levels in the task decomposition tree
Prevents circular dependencies (e.g., needing wood to make a pickaxe to get wood)
Balances between finding complex solutions and avoiding infinite recursion

Limits plans to 30 steps maximum
Ensures solutions remain practical and executable
Prevents the planner from generating overly complicated solutions

Method Ordering
In declare_methods(), methods are ordered by efficiency:

Tools are prioritized over manual actions (e.g., iron axe > wooden axe > punching)
Methods using existing resources are tried before crafting new items
Methods with lower time costs are attempted first

Resource Management

Tracks created tools using boolean flags (e.g., made_wooden_axe)
Prevents redundant tool creation
Encourages resource reuse 