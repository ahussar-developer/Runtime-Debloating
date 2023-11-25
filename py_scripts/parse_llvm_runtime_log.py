#!/usr/bin/env python3
import argparse

def process_data(input_file_path, output_file_path, extract_kept=False):
    unique_function_names = set()
    kept_function_names = set()

    with open(input_file_path, 'r') as input_file:
        for line in input_file:
            if '-- DELETED' in line:
                # Extract the function name by removing "-- DELETED"
                function_name = line.split('--')[0].strip()
                # Add the function name to the set
                unique_function_names.add(function_name)
            elif extract_kept and '-- KEPT' in line:
                # Extract the function name by removing "-- KEPT"
                function_name = line.split('--')[0].strip()
                # Add the function name to the set for kept functions
                kept_function_names.add(function_name)

    # Write the unique function names to the output file
    if output_file_path:
        with open(output_file_path, 'w') as output_file:
            for function_name in unique_function_names:
                output_file.write(f"{function_name}\n")
            
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
