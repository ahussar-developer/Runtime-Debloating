#!/usr/bin/env python3
import argparse
from collections import defaultdict

def process_data(input_file_path, output_file_path, extract_kept=False):
    unique_function_names = set()
    kept_function_names = set()
    function_counts = defaultdict(int)

    with open(input_file_path, 'r') as input_file:
        for line in input_file:
            if '-- DELETED' in line:
                # Extract the function name by removing "-- DELETED"
                function_name = line.split('--')[0].strip()
                # Increment the occurrence count for the function
                function_counts[function_name] += 1
            elif extract_kept and '-- KEPT' in line:
                # Extract the function name by removing "-- KEPT"
                function_name = line.split('--')[0].strip()
                # Add the function name to the set for kept functions
                kept_function_names.add(function_name)

    # Create func_count.txt output file
    # Find the index of the last '/'
    last_slash_index = output_file_path.rfind('/')
    # Slice the string up to the last '/'
    output_file_path2 = ""
    if (last_slash_index > -1):
        modified_string = output_file_path[:last_slash_index]
        output_file_path2 = modified_string + "/func_count.txt"
    else:
        output_file_path2 = "func_count.txt"

    # Write the unique function names to the output file
    if output_file_path:
        with open(output_file_path, 'w') as output_file:
            with open(output_file_path2, 'w') as func_count:
                for function_name, count in function_counts.items():
                    output_file.write(f"{function_name}\n")
                    func_count.write(f"{function_name} : {count}\n")
            
    if extract_kept:
        # Print the kept functions to the terminal
        print("\nFunctions Marked KEPT:")
        for function_name in kept_function_names:
            print(function_name)
            
def main():
    #input_file_path = 'new-del-output.log'
    #output_file_path = 'parsed_new-del-output.txt'
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Parse and extract functions that were called but marked DELETED from a log file\ncreated during via printf when running the exe.')

    # Define command-line arguments
    parser.add_argument('-input-file', dest='input_file', required=True, help='Path to the file to extract DELETED functions.')
    parser.add_argument('-output-file', dest='output_file', help='Path to the output file for found functions.')
    parser.add_argument('-kept', action='store_true', help='Extract and print functions marked as KEPT to the terminal.')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the processing function with the provided arguments
    process_data(args.input_file, args.output_file, args.kept)

if __name__ == "__main__":
    main()
