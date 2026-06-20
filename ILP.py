import json
import time

import numpy as np
import pulp as lp  # Use PuLP as an interface for CBC

from heatmap import create_probability_heatmap


def load_data(json_file):
    with open(json_file, 'r') as file:
        return json.load(file)


def solve_with_cbc(data):
    # Create a linear programming problem
    prob = lp.LpProblem("AreYouTheOne", lp.LpMaximize)  # Use maximize or minimize, here we don't need an objective.

    women_names = data['participants']['women']
    men_names = data['participants']['men']
    double_match = data['participants']['double_match']
    W = len(women_names)
    M = len(men_names)
    is_women_smaller = W < M
    is_men_smaller = M < W
    women_index = {name: idx for idx, name in enumerate(women_names)}
    men_index = {name: idx for idx, name in enumerate(men_names)}

    # Create binary match variables (W by M)
    matches = {(i, j): lp.LpVariable(f"match_{i}_{j}", cat="Binary") for i in range(W) for j in range(M)}

    # Handle the constraints based on the problem
    if is_women_smaller:
        double_match_idx = men_index[double_match]
        for i in range(W):
            for m1 in range(M - 1):
                for m2 in range(m1 + 1, M):
                    if double_match_idx != m1 and double_match_idx != m2:
                        prob += matches[i, m1] + matches[i, m2] <= 1
                    else:
                        prob += matches[i, m1] + matches[i, m2] <= 2
        for j in range(M):
            prob += lp.lpSum(matches[i, j] for i in range(W)) == 1

    if is_men_smaller:
        double_match_idx = women_index[double_match]
        for j in range(M):
            for w1 in range(W - 1):
                for w2 in range(w1 + 1, W):
                    if double_match_idx != w1 and double_match_idx != w2:
                        prob += matches[w1, j] + matches[w2, j] <= 1
                    else:
                        prob += matches[w1, j] + matches[w2, j] <= 2
        for i in range(W):
            prob += lp.lpSum(matches[i, j] for j in range(M)) == 1

    if W == M:
        for j in range(M):
            prob += lp.lpSum(matches[i, j] for i in range(W)) == 1
        for i in range(W):
            prob += lp.lpSum(matches[i, j] for j in range(M)) == 1

    for decision in data['matchbox_decisions']:
        woman = women_index[decision['woman']]
        man = men_index[decision['man']]
        is_match = decision['is_match']
        if is_match:
            prob += matches[woman, man] == 1
        else:
            prob += matches[woman, man] == 0

    for night in data['matching_nights']:
        A_t = night['matches']
        b_t = night['correct_matches']
        match_count = lp.lpSum(matches[women_index[w], men_index[m]] for w, m in A_t.items() if m != "None" and w != "None")
        prob += match_count == b_t

    # List to store all solutions
    solutions = []

    # Iteratively find solutions until no more can be found
    while True:
        prob.solve(lp.PULP_CBC_CMD(msg=False))  # Use CBC as the solver

        if lp.LpStatus[prob.status] == "Optimal" or lp.LpStatus[prob.status] == "Feasible":
            # Extract the current solution
            current_solution = np.array([[int(matches[i, j].varValue) for j in range(M)] for i in range(W)])
            solutions.append(current_solution)

            # Add a constraint to exclude this solution in future iterations
            prob += lp.lpSum(matches[i, j] * (1 - current_solution[i, j]) for i in range(W) for j in range(M)) <= W * M - 1
        else:
            break  # No more solutions found

    return solutions, women_names, men_names


start_time = time.time()
print(f"start time:", time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time())))
data = load_data('season_february25.json')
solutions, women_names, men_names = solve_with_cbc(data)
print("My program took", time.time() - start_time, "s / ", (time.time() - start_time) / 60, "m to run")

if solutions:
    print(f"Found {len(solutions)} feasible solutions.")
    create_probability_heatmap(solutions, women_names, men_names)
