#!/usr/bin/env python3
import argparse
import networkx as nx
import csv
import re
import time

def process_data(input_file, output_location):
    # Load Graphviz file using NetworkX
    graph = nx.drawing.nx_agraph.read_dot(input_file)


    # Regular expression to extract the function name from the label
    label_pattern = re.compile(r'fun:\s+([a-zA-Z_][a-zA-Z0-9_.]*)')

    # Open CSV file for writing
    output_file = output_location+"/callgraph.csv"
    with open(output_file, "w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)

        # Write header row
        csv_writer.writerow(["Source", "Target"])

        # Write edge data with function names
        for edge in graph.edges():
            source_function_match = label_pattern.search(graph.nodes[edge[0]]['label'])
            target_function_match = label_pattern.search(graph.nodes[edge[1]]['label'])

            source_function = source_function_match.group(1) if source_function_match else edge[0]
            target_function = target_function_match.group(1) if target_function_match else edge[1]

            csv_writer.writerow([source_function, target_function])


def main():
    #input_file = '/home/user/passes/SVF/callgraph_final.dot'
    #output_file_path = '/home/user/passes'
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Parse and extract call graph to an edges CSV to be ingested during the pass.')

    # Define command-line arguments
    parser.add_argument('-input', dest='input_file', required=True, help='Path to the dot callgraph.')
    parser.add_argument('-output-dir', dest='output_dir', required=True, help='Path to the output directory where callgraph.csv will be written.')
    

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the processing function with the provided arguments
    start = time.time()
    process_data(args.input_file, args.output_dir)
    end = time.time()
    total_seconds = end - start
    print(f"CG Parsing Time: {total_seconds:.6f} seconds")

if __name__ == "__main__":
    main()