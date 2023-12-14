import numpy as np
import matplotlib.pyplot as plt
import statistics

def parse_file(file_path):
    complexity_dict = {}

    with open(file_path, 'r') as file:
        for line in file:
            if "Complexity Function" in line and "Complexity Score" in line:
                # Extract function name and complexity score
                parts = line.split(", ")
                function_name = parts[0].split(": ")[1]
                complexity_score = int(parts[1].split(": ")[1])

                # Update dictionary
                complexity_dict[function_name] = complexity_score

    return complexity_dict

def visualize_edge_complexity(complexity_dict, positive_threshold):
    functions = list(complexity_dict.keys())
    complexity_scores = list(complexity_dict.values())

    # Calculate mean, median, and standard deviation
    mean_score = statistics.mean(complexity_scores)
    median_score = statistics.median(complexity_scores)
    std_dev_score = statistics.stdev(complexity_scores)

    plt.figure(figsize=(8, 5))
    plt.plot(complexity_scores, range(len(functions)), 'o', color='gray')
    # Draw vertical lines for positive and negative thresholds
    plt.axvline(x=positive_threshold, color='red', linestyle='--', label='std')
    plt.axvline(x=median_score, color='green', linestyle='--', label='median')
    plt.axvline(x=mean_score, color='black', linestyle='--', label='mean')
    # Add labels to the vertical lines
    top_of_graph = len(functions)
    bottom_of_graph = 0
    
    plt.text(positive_threshold, top_of_graph * 1.02, '+1 std', color='red', ha='left')
    plt.text(median_score, top_of_graph * 1.02, 'median', color='green', ha='right')
    plt.text(mean_score, bottom_of_graph * 0.98, 'mean', color='black', ha='right')


    
    plt.yticks([])  # Remove y-axis labels
    plt.xlabel('Number of branching terminator instructions')
    plt.title('Cyclomatic Complexity of NGINX')
    plt.grid(axis='x', linestyle='--', alpha=0.6)
    plt.savefig('Cyclo_complexity.png')
    plt.savefig('Cyclo_complexity.svg', format='svg', bbox_inches='tight')
    plt.clf()


def determine_thresholds(complexity_dict, std_factor=1):
    complexity_scores = list(complexity_dict.values())
    mean_complexity = np.mean(complexity_scores)
    std_dev_complexity = np.std(complexity_scores)
    
    positive_threshold = mean_complexity + std_factor * std_dev_complexity
    negative_threshold = mean_complexity - std_factor * std_dev_complexity
    
    return positive_threshold, negative_threshold

def run_complexity(complexity_dict):
    positive_threshold, _ = determine_thresholds(complexity_dict, 1)
    print(f"Positive Threshold: {positive_threshold}")
    visualize_edge_complexity(complexity_dict, positive_threshold)
    
    
# Example usage
file_path = '/home/user/passes/py_scripts/nginx_complexity.log'
result = parse_file(file_path)

run_complexity(result)
