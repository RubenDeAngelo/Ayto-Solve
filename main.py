import json
import time
import numpy as np
from ortools.sat.python import cp_model
from heatmap import create_probability_heatmap


def load_data(json_file):
    with open(json_file, 'r') as file:
        return json.load(file)


def solve_are_you_the_one(data):
    model = cp_model.CpModel()

    women_names = data['participants']['women']
    men_names = data['participants']['men']

    W = len(women_names)
    M = len(men_names)
    is_women_smaller = W < M
    is_men_smaller = M < W

    # Create name-to-index mappings
    women_index = {name: idx for idx, name in enumerate(women_names)}
    men_index = {name: idx for idx, name in enumerate(men_names)}
    double_match = data['participants']['double_match']

    # Create variables
    matches = {(i, j): model.NewBoolVar(f'M_{i}_{j}') for i in range(W) for j in range(M)}

    # Constraints
    if is_women_smaller:
        double_match_idx = men_index[double_match]

        for i in range(W):
            model.Add(sum(matches[(i, j)] for j in range(M) if j != double_match_idx) == 1)
            model.Add(sum(matches[(i, j)] for j in range(M) if j == double_match_idx) <= 1)

        for j in range(M):
            model.Add(sum(matches[(i, j)] for i in range(W)) == 1)

        # Restriction: Prevent reusing perfect match people in double matches
        for decision in data['matchbox_decisions']:
            woman = women_index[decision['woman']]
            man = men_index[decision['man']]
            if decision['is_match'] and man != double_match_idx:
                model.Add(matches[(woman, double_match_idx)] == 0)

    if is_men_smaller:
        double_match_idx = women_index[double_match]

        for j in range(M):
            model.Add(sum(matches[(i, j)] for i in range(W) if i != double_match_idx) == 1)
            model.Add(sum(matches[(i, j)] for i in range(W) if i == double_match_idx) <= 1)

        for i in range(W):
            model.Add(sum(matches[(i, j)] for j in range(M)) == 1)

        # Restriction: Prevent reusing perfect match people in double matches
        for decision in data['matchbox_decisions']:
            woman = women_index[decision['woman']]
            man = men_index[decision['man']]
            if decision['is_match'] and woman != double_match_idx:
                model.Add(matches[(double_match_idx, man)] == 0)
    if W == M:
        for j in range(M):
            model.Add(sum(matches[(i, j)] for i in range(W)) == 1)
        for i in range(W):
            model.Add(sum(matches[(i, j)] for j in range(M)) == 1)

    # Matchbox decisions constraints
    for decision in data['matchbox_decisions']:
        woman = women_index[decision['woman']]
        man = men_index[decision['man']]
        if decision['is_match']:
            model.Add(matches[(woman, man)] == 1)
        else:
            model.Add(matches[(woman, man)] == 0)

    # Matching night constraints
    for night in data['matching_nights']:
        A_t = night['matches']
        b_t = night['correct_matches']
        match_count = sum(
            matches[(women_index[w], men_index[m])]
            for w, m in A_t.items() if m != "None" and w != "None"
        )
        model.Add(match_count == b_t)

    # Solver
    solver = cp_model.CpSolver()
    solution_collector = AllSolutionsCollector(matches, W, M, women_names, men_names)
    solver.SearchForAllSolutions(model, solution_collector)

    return solution_collector.solutions(), women_names, men_names


class AllSolutionsCollector(cp_model.CpSolverSolutionCallback):
    def __init__(self, matches, W, M, women_names, men_names):
        super().__init__()
        self._matches = matches
        self._W = W
        self._M = M
        self._women_names = women_names
        self._men_names = men_names
        self._solutions = []

    def on_solution_callback(self):
        solution = [[self.Value(self._matches[(i, j)]) for j in range(self._M)] for i in range(self._W)]
        self._solutions.append(solution)

    def solutions(self):
        return self._solutions


# Main Execution
start_time = time.time()

data = load_data('season_february25.json')
double_match_field = data['participants']['double_match']
double_match_list = double_match_field if isinstance(double_match_field, list) else [double_match_field]

solutions = []
seen_solutions = set()

for double_match in double_match_list:
    temp_data = json.loads(json.dumps(data))  # Deep copy to avoid modifying original
    temp_data['participants']['double_match'] = double_match

    new_solutions, women_names, men_names = solve_are_you_the_one(temp_data)

    for sol in new_solutions:
        sol_tuple = tuple(map(tuple, sol))  # Convert solution to a hashable format
        if sol_tuple not in seen_solutions:
            seen_solutions.add(sol_tuple)
            solutions.append(np.array(sol))  # Convert back to NumPy array

print(f"My program took {time.time() - start_time:.2f} s / {(time.time() - start_time) / 60:.2f} m to run")

if solutions:
    print(f"Found {len(solutions)} feasible solutions.\n")
    create_probability_heatmap(solutions, women_names, men_names)
else:
    print("No solution found.")
