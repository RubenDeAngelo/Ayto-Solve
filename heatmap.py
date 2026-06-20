import numpy as np
import matplotlib.pyplot as plt

def create_probability_heatmap(all_match_matrices, women_names, men_names):
    # Combine all match matrices
    aggregated_matrix = np.zeros_like(all_match_matrices[0])

    for matrix in all_match_matrices:
        aggregated_matrix += matrix

    # Number of solutions
    num_solutions = len(all_match_matrices)

    # Calculate probability matrix and count matrix
    probability_matrix = aggregated_matrix * 100 / num_solutions
    count_matrix = aggregated_matrix

    # Round the probability matrix to two decimal places
    probability_matrix_rounded = np.round(probability_matrix, decimals=2)

    # Plot heatmap
    plt.figure(figsize=(10, 8))
    plt.imshow(probability_matrix_rounded, cmap='coolwarm', interpolation='nearest')


    for i in range(len(women_names)):
        for j in range(len(men_names)):
            text = f'{probability_matrix_rounded[i, j]}%'
            plt.text(j, i, text, ha='center', va='center', color='black', fontsize=12)

    # Set ticks and labels
    plt.xticks(np.arange(len(men_names)), men_names, rotation=45)
    plt.yticks(np.arange(len(women_names)), women_names)
    plt.xlabel('Men')
    plt.ylabel('Women')
    plt.title('Probability Heatmap of Matches')

    # Add color bar
    plt.colorbar(label='Probability')

    # Display the plot
    plt.tight_layout()
    plt.show()
