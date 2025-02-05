import pyhop
import json

def check_enough(state, ID, item, num):
    if getattr(state,item)[ID] >= num:
        return []
    return False

def produce_enough(state, ID, item, num):
    return [('produce', ID, item), ('have_enough', ID, item, num)]

pyhop.declare_methods('have_enough', check_enough, produce_enough)

def produce(state, ID, item):
    return [('produce_{}'.format(item), ID)]

pyhop.declare_methods('produce', produce)

def make_method(name, rule):
    def method(state, ID):
        subtasks = []
        
        # Add requirements
        if 'Requires' in rule:
            for item, amount in rule['Requires'].items():
                subtasks.append(('have_enough', ID, item, amount))
        
        # Add consumed items
        if 'Consumes' in rule:
            for item, amount in rule['Consumes'].items():
                subtasks.append(('have_enough', ID, item, amount))
        
        # Add operator
        subtasks.append((f'op_{name}', ID))
        
        return subtasks
    
    return method

def declare_methods(data):
    # Sort recipes by time efficiency for each product
    product_methods = {}
    
    for recipe_name, rule in data['Recipes'].items():
        if 'Produces' not in rule:
            continue
            
        for product, amount in rule['Produces'].items():
            if product not in product_methods:
                product_methods[product] = []
            
            # Create method
            method = make_method(recipe_name.replace(' ', '_'), rule)
            method.__name__ = f'produce_{product}_by_{recipe_name.replace(" ", "_")}'
            
            # Store method with its time cost
            product_methods[product].append((method, rule.get('Time', float('inf'))))
    
    # Declare methods for each product, sorted by time efficiency
    for product, methods in product_methods.items():
        # Sort methods by time cost
        sorted_methods = [m[0] for m in sorted(methods, key=lambda x: x[1])]
        pyhop.declare_methods(f'produce_{product}', *sorted_methods)

def make_operator(rule):
    def operator(state, ID):
        # Check time
        if 'Time' in rule and state.time[ID] < rule['Time']:
            return False
        
        # Check requirements
        if 'Requires' in rule:
            for item, amount in rule['Requires'].items():
                if getattr(state, item)[ID] < amount:
                    return False
        
        # Check consumed items
        if 'Consumes' in rule:
            for item, amount in rule['Consumes'].items():
                if getattr(state, item)[ID] < amount:
                    return False
        
        # Apply time cost
        if 'Time' in rule:
            state.time[ID] -= rule['Time']
        
        # Consume items
        if 'Consumes' in rule:
            for item, amount in rule['Consumes'].items():
                getattr(state, item)[ID] -= amount
        
        # Produce items
        if 'Produces' in rule:
            for item, amount in rule['Produces'].items():
                getattr(state, item)[ID] += amount
        
        return state
    
    return operator

def declare_operators(data):
    operators = []
    
    for recipe_name, rule in data['Recipes'].items():
        # Create operator
        op = make_operator(rule)
        op_name = f'op_{recipe_name.replace(" ", "_")}'
        op.__name__ = op_name
        operators.append(op)
    
    pyhop.declare_operators(*operators)

def add_heuristic(data, ID):
    def heuristic(state, curr_task, tasks, plan, depth, calling_stack):
        # Prevent infinite recursion
        if depth > 10:
            return True
        
        # Prevent overly long plans
        if len(plan) > 30:
            return True
        
        # Check if we have enough time
        if state.time[ID] < 0:
            return True
        
        # Check for circular dependencies in calling stack
        task_count = {}
        for task in calling_stack:
            task_name = task[0]
            if task_name.startswith('produce_'):
                task_count[task_name] = task_count.get(task_name, 0) + 1
                if task_count[task_name] > 2:  # Allow at most 2 attempts to produce same item
                    return True
        
        return False
    
    pyhop.add_check(heuristic)

def set_up_state(data, ID, time=0):
    state = pyhop.State('state')
    state.time = {ID: time}
    
    for item in data['Items']:
        setattr(state, item, {ID: 0})
    
    for item in data['Tools']:
        setattr(state, item, {ID: 0})
    
    for item, num in data['Initial'].items():
        setattr(state, item, {ID: num})
    
    return state

def set_up_goals(data, ID):
    goals = []
    for item, num in data['Goal'].items():
        goals.append(('have_enough', ID, item, num))
    return goals

if __name__ == '__main__':
    rules_filename = 'crafting.json'
    
    with open(rules_filename) as f:
        data = json.load(f)
    
    state = set_up_state(data, 'agent', time=239)
    goals = set_up_goals(data, 'agent')
    
    declare_operators(data)
    declare_methods(data)
    add_heuristic(data, 'agent')
    
    pyhop.pyhop(state, goals, verbose=3)