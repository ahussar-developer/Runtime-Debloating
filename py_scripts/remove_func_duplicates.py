#!/usr/bin/env python3
import argparse

def process_data(input_file_path, output_file_path):
    unique_function_names = set()

    with open(input_file_path, 'r') as input_file:
        for line in input_file:
            function_name = line.strip()  # Remove leading and trailing whitespaces
            unique_function_names.add(function_name)

    # Write the unique function names to the output file
    with open(output_file_path, 'w') as output_file:
        for function_name in sorted(unique_function_names):
            output_file.write(f"{function_name}\n")

def main():
    #input_file_path = '/home/user/passes/missed_runtime_funcs.log'
    #output_file_path = '/home/user/passes/unique_missed_runtime_funcs.log'
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process function names from an input file and write unique function names to an output file.')

    # Define command-line arguments
    parser.add_argument('-input', dest='input_file_path', required=True, help='Path to the input file.')
    parser.add_argument('-output', dest='output_file_path', required=True, help='Path to the output file.')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the processing function with the provided arguments
    process_data(args.input_file_path, args.output_file_path)

if __name__ == "__main__":
    main()