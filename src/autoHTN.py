import json
import pyhop

def make_operator(rule):
    """
    Dynamically create an operator based on a recipe from crafting.json
    """
    def operator(state, ID):
        # Check if time constraint is met
        if state.time[ID] < rule.get('Time', 1):
            return False
        
        # Check if required items are present
        requires = rule.get('Requires', {})
        for item, amount in requires.items():
            if getattr(state, item)[ID] < amount:
                return False
        
        # Check if consumed items are sufficient
        consumes = rule.get('Consumes', {})
        for item, amount in consumes.items():
            if getattr(state, item)[ID] < amount:
                return False
        
        # Modify state
        state.time[ID] -= rule.get('Time', 1)
        
        # Consume required items
        for item, amount in consumes.items():
            getattr(state, item)[ID] -= amount
        
        # Produce items
        produces = rule.get('Produces', {})
        for item, amount in produces.items():
            getattr(state, item)[ID] += amount
        
        return state
    
    return operator

def make_method(name, rule):
    """
    Dynamically create a method based on a recipe from crafting.json
    """
    def method(state, ID):
        subtasks = []
        
        # Check for required items
        requires = rule.get('Requires', {})
        for item, amount in requires.items():
            subtasks.append(('have_enough', ID, item, amount))
        
        # Check for consumed items
        consumes = rule.get('Consumes', {})
        for item, amount in consumes.items():
            subtasks.append(('have_enough', ID, item, amount))
        
        # Add the operator task
        subtasks.append((f'op_{name}', ID))
        
        return subtasks
    
    return method

def declare_operators(data):
    """
    Declare operators for all recipes in crafting.json
    """
    operators = []
    for name, rule in data['Recipes'].items():
        # Create operator with 'op_' prefix
        op_name = f'op_{name}'.replace(' ', '_')
        op = make_operator(rule)
        op.__name__ = op_name
        operators.append(op)
    
    pyhop.declare_operators(*operators)

def declare_methods(data):
    """
    Declare methods for all recipes in crafting.json
    """
    # Track unique produce categories to prevent duplicate method declarations
    produce_categories = {}
    
    for name, rule in data['Recipes'].items():
        # Create method with 'produce_' prefix
        method_name = name.split()[0]  # Use first word as base for method
        
        # Ensure we have a produces item
        if 'Produces' not in rule:
            continue
        
        # Get the item being produced
        produces_item = list(rule['Produces'].keys())[0]
        
        # Create method
        method = make_method(name.replace(' ', '_'), rule)
        method.__name__ = f'produce_{produces_item}'
        
        # Declare or append to existing category methods
        if produces_item not in produce_categories:
            produce_categories[produces_item] = [method]
        else:
            produce_categories[produces_item].append(method)
    
    # Declare methods for each produce category
    for item, methods in produce_categories.items():
        pyhop.declare_methods(f'produce_{item}', *methods)

def add_heuristic(data, ID):
    """
    Prevent infinite recursion in task planning
    """
    def heuristic(state, curr_task, tasks, plan, depth, calling_stack):
        # Prevent excessive depth or circular dependencies
        if depth > 10:
            return True
        
        # Prevent making too many intermediate items
        if len(plan) > 30:
            return True
        
        return False
    
    pyhop.add_check(heuristic)

def set_up_state(initial_state):
    """
    Initialize pyhop state from json initial state
    """
    state = pyhop.State('state')
    
    # Add default items for all possible items
    items = set(json.load(open('crafting.json'))['Items']) | \
            set(json.load(open('crafting.json'))['Tools'])
    
    for item in items:
        setattr(state, item, {'agent': 0})
    
    # Add initial state items
    for item, amount in initial_state.items():
        state.__dict__[item]['agent'] = amount
    
    # Add time (default to large number)
    state.time = {'agent': 300}
    
    # Tracking flags for preventing duplicate tool creation
    tools = json.load(open('crafting.json'))['Tools']
    for tool in tools:
        setattr(state, f'made_{tool}', {'agent': False})
    
    return state

def set_up_goals(goal_state):
    """
    Create top-level task from goal state
    """
    goals = []
    for item, amount in goal_state.items():
        goals.append(('have_enough', 'agent', item, amount))
    
    return goals

# Load the recipes
with open('crafting.json', 'r') as f:
    recipes = json.load(f)

# Declare operators and methods
declare_operators(recipes)

# Declare base methods
def check_enough(state, ID, item, num):
    if getattr(state, item)[ID] >= num:
        return []
    return False

def produce_enough(state, ID, item, num):
    return [('produce', ID, item), ('have_enough', ID, item, num)]

def produce(state, ID, item):
    # Generic produce method to cover multiple items
    return [('produce_' + item, ID)]

pyhop.declare_methods('have_enough', check_enough, produce_enough)
pyhop.declare_methods('produce', produce)

# Test cases
test_cases = [
    ({'plank': 1}, {'plank': 1}, 0),
    ({}, {'plank': 1}, 300),
    ({'plank': 3, 'stick': 2}, {'wooden_pickaxe': 1}, 10),
    ({}, {'iron_pickaxe': 1}, 100),
    ({}, {'cart': 1, 'rail': 10}, 175),
    ({}, {'cart': 1, 'rail': 20}, 250)
]

# Run test cases
for i, (initial, goal, time_limit) in enumerate(test_cases, 1):
    print(f"\n--- Test Case {i} ---")
    state = set_up_state(initial)
    state.time['agent'] = time_limit
    goals = set_up_goals(goal)
    
    try:
        plan = pyhop.pyhop(state, goals, verbose=0)
        print(f"Solution found for test case {i}")
    except Exception as e:
        print(f"No solution found for test case {i}: {e}")