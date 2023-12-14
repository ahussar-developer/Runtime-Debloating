import networkx as nx
import csv
from collections import Counter
from collections import defaultdict
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from scipy.stats import zscore
import seaborn as sns
import time
import statistics
import pygraphviz as pgv

# Load the Call Graph from CSV
def load_call_graph(filename):
    G = nx.DiGraph()
    with open(filename, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip header row
        for row in csv_reader:
            source, target = row
            G.add_edge(source, target)
    return G

def visualize_subgraph(graph, function_list, radius=1):
    subgraph = nx.DiGraph()  # Use DiGraph instead of Graph
    for function in function_list:
        if function in graph:
            ego = nx.ego_graph(graph, function, radius=radius)
            subgraph = nx.compose(subgraph, ego)
        else:
            print(f"Warning: Function '{function}' not found in the graph. Skipping.")

    if len(subgraph) > 0:
        # Create a PyGraphviz graph from the NetworkX graph
        pos = nx.spring_layout(subgraph)  # You can use a different layout if needed
        pos_dot = {node: f"{pos[node][0]},{pos[node][1]}" for node in subgraph.nodes()}

        node_colors = ['red' if node in function_list else 'skyblue' for node in subgraph.nodes()]

        # Use PyGraphviz to create a directed graph and write to DOT file
        G = pgv.AGraph(directed=True)
        for node, color in zip(subgraph.nodes(), node_colors):
            G.add_node(node, color=color)
        G.add_nodes_from(subgraph.nodes())
        G.add_edges_from(subgraph.edges())
        G.layout(prog="dot")
        G.draw("temp.png")

        # Print the number of nodes and edges
        print(f"Number of nodes in the subgraph: {subgraph.number_of_nodes()}")
        print(f"Number of edges in the subgraph: {subgraph.number_of_edges()}")

    else:
        print("No nodes found in the subgraph.")
    
    return

# Load the Missed Functions
def load_missed_funcs(filename):
    with open(filename, 'r') as file:
        missed_funcs = [line.strip() for line in file]
    return missed_funcs

# Load the Dynamic Trace
def load_dynamic_trace(filename):
    with open(filename, 'r') as trace_file:
        dynamic_trace = [line.strip() for line in trace_file]
    return dynamic_trace

# Load the possible realted functions
def load_related_functions(filename):
    with open(filename, 'r') as trace_file:
        related_funcs = [line.strip() for line in trace_file]
    return related_funcs

def load_exe_metrics(filename):
    result_dict = {}
    with open(filename, 'r') as file:
        for line in file:
            parts = line.strip().split(' : ')
            if len(parts) == 2:
                key, value = parts
                result_dict[key] = int(value)
    return result_dict


# Perform Dependency Analysis to find functions that dominate a given function
def find_dominators(call_graph, target_function):
    dominators = set()
    # Check if the target function is in the graph
    if target_function not in call_graph:
        print(f"Error: Target function '{target_function}' not found in the graph.")
        return dominators
    # Use networkx's dominator algorithm to find dominators
    dominator_dict = nx.algorithms.dominance.immediate_dominators(call_graph.reverse(), target_function)

    # Traverse the dominator dictionary to find nodes that dominate the target_function
    for node, dominator in dominator_dict.items():
        if dominator is not None:
            dominators.add(dominator)

    return dominators

# Create a dictionary of functions not in dynamic_trace but in dominance sets
def find_functions_in_dominance_sets(call_graph, dynamic_trace):
    functions_in_dominance_sets = {}

    for target_function in dynamic_trace:
        dominators = find_dominators(call_graph, target_function)

        for dominator in dominators:
            if dominator not in dynamic_trace:
                functions_in_dominance_sets.setdefault(dominator, 0)
                functions_in_dominance_sets[dominator] += 1
    with open("dom_funcs.txt", 'w') as file:
        for function in functions_in_dominance_sets:
            file.write(f"{function}\n")
    
    return functions_in_dominance_sets

def visualize_dominance(functions_in_dominance_sets):
    # Extract function names and counts for plotting
    functions = list(functions_in_dominance_sets.keys())
    counts = list(functions_in_dominance_sets.values())
    
    # Extract function names and counts for plotting
    functions = list(functions_in_dominance_sets.keys())
    counts = list(functions_in_dominance_sets.values())
    
    # Increase the overall size of the graph
    fig, ax = plt.subplots(figsize=(18, 12))
    bars = ax.barh(functions, counts, color='gray')
    
    # Make text bolder and larger
    prop = fm.FontProperties(fname=fm.findfont(fm.FontProperties(family='Arial')))
    for text in ax.get_xticklabels() + ax.get_yticklabels():
        text.set_fontproperties(prop)
        text.set_fontsize(14)
        text.set_fontweight('bold')
    
    ax.set_xlabel('Number of Occurrences in Dominance Sets')
    ax.set_title('Frequency of Functions in Dominance Sets of thttpd')
    ax.invert_yaxis()  # To have the highest count at the top

    # Add function names within the bars
    for bar, function in zip(bars, functions):
        text_x = bar.get_x() + bar.get_width() / 2
        ax.text(text_x, bar.get_y() + bar.get_height() / 2, function, ha='center', va='center', color='black', fontsize=12, fontweight='bold')

    # Remove y-axis tick labels
    ax.set_yticks([])

    plt.savefig('dominance_frequency.png')
    plt.savefig('dominance_plot.svg', format='svg', bbox_inches='tight')
    plt.clf()

def visualize_edge_complexity(complexity_dict, positive_threshold, negative_threshold):
    functions = list(complexity_dict.keys())
    complexity_scores = list(complexity_dict.values())

    plt.figure(figsize=(8, 5))
    plt.plot(complexity_scores, range(len(functions)), 'o', color='gray')
    # Draw vertical lines for positive and negative thresholds
    plt.axvline(x=positive_threshold, color='red', linestyle='--', label='Positive Threshold')
    plt.axvline(x=negative_threshold, color='red', linestyle='--', label='Negative Threshold')
    plt.yticks([])  # Remove y-axis labels
    plt.xlabel('Edge Complexity: Outgoing - Incoming')
    plt.title('Edge Complexity of thttpd')
    plt.grid(axis='x', linestyle='--', alpha=0.6)
    plt.savefig('edge_complexity.png')
    plt.savefig('edge_complexity.svg', format='svg', bbox_inches='tight')
    plt.clf()

def determine_thresholds(complexity_dict, std_factor=2):
    complexity_scores = list(complexity_dict.values())
    mean_complexity = np.mean(complexity_scores)
    std_dev_complexity = np.std(complexity_scores)
    
    positive_threshold = mean_complexity + std_factor * std_dev_complexity
    negative_threshold = mean_complexity - std_factor * std_dev_complexity
    
    return positive_threshold, negative_threshold

def analyze_strongly_connected_components(call_graph, dynamic_trace):
    scc_list = list(nx.strongly_connected_components(call_graph))
    
    print("Strongly Connected Components:")
    for i, scc in enumerate(scc_list):
        functions_in_scc = [func for func in dynamic_trace if func in scc]
        if functions_in_scc:
            functions_not_in_trace = set(scc) - set(dynamic_trace)
            if functions_not_in_trace:
                #print(f"Component {i + 1} ({len(scc)} functions): {', '.join(functions_not_in_trace)}")
                print(f"  Number of functions not in trace: {len(functions_not_in_trace)}")
            if (len(scc) > 1):
                #print(f"Component {i + 1} ({len(scc)} functions): {scc}")
                #print(f"Component {i + 1} ({len(scc)} functions)")
                pass
    return


def find_functions_not_in_trace(call_graph, traced_functions):
    # Step 2: Find Neighbors of Traced Functions
    neighbors_1_hop = set()
    neighbors_2_hop = set()

    for function in traced_functions:
        if function in call_graph:
            neighbors_1_hop.update(call_graph.successors(function))
            neighbors_2_hop.update(nx.single_source_shortest_path_length(call_graph, function, cutoff=2).keys())

    # Remove traced functions from the sets
    neighbors_1_hop -= set(traced_functions)
    neighbors_2_hop -= set(traced_functions)

    # Step 3: Generate the List of Functions
    functions_not_in_trace = neighbors_1_hop.union(neighbors_2_hop)
    #for f in functions_not_in_trace:
        #print(f"Not in trace: {f}")

    return functions_not_in_trace

# Calculate Cyclomatic Complexity for Each Function
def calculate_edge_complexity(call_graph, dynamic_trace):
    complexity_dict = {}

    for node in call_graph.nodes:
        if node in dynamic_trace:
            continue
        if "llvm" in node:
            continue
        in_degree = call_graph.in_degree(node)
        out_degree = call_graph.out_degree(node)
        complexity = out_degree - in_degree
        complexity_dict[node] = complexity

    return complexity_dict

def calculate_edge_complexity_neighbors(call_graph, neighbors):
    complexity_dict = {}

    for node in call_graph.nodes:
        if node not in neighbors:
            continue
        if "llvm" in node:
            continue
        in_degree = call_graph.in_degree(node)
        out_degree = call_graph.out_degree(node)
        complexity = out_degree - in_degree
        print(f"Neighbor({node}): {complexity}")
        complexity_dict[node] = complexity

    return complexity_dict

def run_dominance(call_graph, dynamic_trace):
    # Record start time
    start_time = time.time()
    #OUTPUTS unique dominators: dom_funcs.txt
    functions_in_dominance_sets = find_functions_in_dominance_sets(call_graph, dynamic_trace)
    end_time = time.time()
    print(f"\nExecution Time: {end_time - start_time} seconds")
    
    #visualize_dominance(functions_in_dominance_sets)
    
    #print("Functions in Dominance Sets not in Dynamic Trace:")
    #for function, count in functions_in_dominance_sets.items():
    #    print(f"{function}: {count} times in dominance sets")
    return

def run_complexity(call_graph,dynamic_trace):
    complexity_dict = calculate_edge_complexity(call_graph,dynamic_trace)
    positive_threshold, negative_threshold = determine_thresholds(complexity_dict, 1)
    print(f"Positive Threshold: {positive_threshold}")
    print(f"Negative Threshold: {negative_threshold}")
    #visualize_edge_complexity(complexity_dict, positive_threshold, negative_threshold)
    # Example usage
    
    
    # Print edge Complexity for Each Function
    with open("edge_complexity_funcs.txt", 'w') as file:
        for function, complexity in complexity_dict.items():
            if (complexity >= 0):
                # positive threhold
                if (complexity > positive_threshold):
                    #print(f'{function}: {complexity}')
                    file.write(f"{function}\n")
            else:
                #negative threshold
                if (complexity < negative_threshold):
                    #print(f'{function}: {complexity}')
                    file.write(f"{function}\n") 
    return

def calculate_edge_directions(call_graph, related_funcs, dynamic_trace):
    edge_scores = {}

    for related_function in related_funcs:
        if related_function not in call_graph:
            #print(f"Warning: {related_function} not found in call graph")
            continue

        for trace_function in dynamic_trace:
            if trace_function not in call_graph:
                #print(f"Warning: {trace_function} not found in call graph")
                continue

            if nx.has_path(call_graph, trace_function, related_function):
                edges = nx.shortest_path(call_graph, trace_function, related_function, method="dijkstra")
                for i in range(len(edges) - 1):
                    edge = (edges[i], edges[i + 1])
                    if edge in edge_scores:
                        #edge_scores[edge] += 1 if i == 0 else -1  # Positive if related function executes before, negative otherwise
                        edge_scores[edge] += 1
                    else:
                        #edge_scores[edge] = 1 if i == 0 else -1
                        edge_scores[edge] = 1
    # Filter out edges with zero occurrences
    non_zero_edges = {edge: score for edge, score in edge_scores.items() if score != 0}
    # Aggregate scores for each function pair
    function_scores = {}
    for (func1, func2), score in non_zero_edges.items():
        if func1 in function_scores:
            function_scores[func1] += score
        else:
            function_scores[func1] = score

        if func2 in function_scores:
            function_scores[func2] += score
        else:
            function_scores[func2] = score
    return function_scores

def calculate_edge_stats(sorted_functions):
    # Extract scores from the sorted_functions
    scores = [score for _, score in sorted_functions]

    # Calculate mean, median, and standard deviation
    mean_score = statistics.mean(scores)
    median_score = statistics.median(scores)
    std_dev_score = statistics.stdev(scores)
    
    count_above_median = sum(score >= median_score for _, score in sorted_functions)
    print("Number of functions at or above the median score:", count_above_median)
    count_at_median = sum(score > median_score for _, score in sorted_functions)
    print("Number of functions at the median score:", count_at_median)
    return mean_score, median_score, std_dev_score

def write_src_edges(functions, conservative=False):
    filename = 'src_edge_funcs.txt'
    _, median_score, _ = calculate_edge_stats(functions)

    selected_functions = [func for func, score in functions if (score == median_score) if not conservative or (score >= median_score)]

    with open(filename, 'w') as file:
        file.write('\n'.join(selected_functions))

def run_src_edge(call_graph, related_funcs, dynamic_trace):
    edge_scores = calculate_edge_directions(call_graph, related_funcs, dynamic_trace)

    # Sort and print in descending order of aggregate scores
    sorted_functions = sorted(edge_scores.items(), key=lambda x: x[1], reverse=True)
    for func, aggregate_score in sorted_functions:
        print(f"{func}: {aggregate_score} aggregate score")
    
    mean_score, median_score, std_dev_score = calculate_edge_stats(sorted_functions)

    print(f"Mean Score: {mean_score}")
    print(f"Median Score: {median_score}")
    print(f"Standard Deviation of Scores: {std_dev_score}")
    write_src_edges(sorted_functions)


if __name__ == "__main__":
    # Example Usage
    #dir = "/home/user/passes/pass_files/nginx/"
    dir = "/home/user/passes/pass_files/thttpd/"
    #call_graph_filename = dir + 'callgraph-ander.csv'
    call_graph_filename = "/home/user/passes/SVF/callgraph.csv"
    
    dynamic_trace_filename = dir + 'orig_llvm_all_tests.log'
    exe_metrics_filename = dir + 'func_count_all_tests.txt'
    nginx_missed_funcs = "/home/user/passes/pass_files/nginx/missed_funcs.txt"
    
    load_cfg_start = time.time() 
    call_graph = load_call_graph(call_graph_filename)
    dynamic_trace = load_dynamic_trace(dynamic_trace_filename)
    exe_metrics = load_exe_metrics(exe_metrics_filename)
    missed_funcs = load_missed_funcs(nginx_missed_funcs)
    load_cfg_end = time.time() 
    load_cfg_seconds = load_cfg_end - load_cfg_start
    
    
    #visualize_subgraph(call_graph, missed_funcs)
    
    #neighbors = find_functions_not_in_trace(call_graph, dynamic_trace)
    #calculate_edge_complexity_neighbors(call_graph, neighbors)
    complexity_start = time.time()
    run_complexity(call_graph,dynamic_trace)
    complexity_end = time.time()
    complexity_seconds = complexity_end - complexity_start
    
    dom_start = time.time()
    run_dominance(call_graph,dynamic_trace)
    dom_end = time.time()
    dom_seconds = dom_end - dom_start
    # This grabs too many functions at the moment -- only one SCC that has 700 funcs
    #analyze_strongly_connected_components(call_graph, dynamic_trace)
    
    #related_funcs_filename = '/home/user/passes/py_scripts/src_assoc_py_matched_funcs.txt'
    #related_funcs = load_related_functions(related_funcs_filename)
    #run_src_edge(call_graph, related_funcs, dynamic_trace)
    
    print(f"Load CFG Time: {load_cfg_seconds:.6f} seconds")
    print(f"Edge Complexity CFG Time: {complexity_seconds:.6f} seconds")
    print(f"Dominator Time: {dom_seconds:.6f} seconds")
    
    
    
        