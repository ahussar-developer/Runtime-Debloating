
## All of these ocme from the other vm where the static reachability file is output
## look to other vm for the output the cfg needs to be in for this to work
import sys

def load_functions(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    functions = {}
    current_section = None

    for line in lines:
        line = line.strip()
        if line.endswith(':'):
            current_section = line[:-1]
            functions[current_section] = set()
        elif current_section and line.startswith('File'):
            functions[current_section].update(line.split(':')[1].strip().replace('{', '').replace('}', '').split(','))

    return functions

def compare_function_names(file1_functions, file2_functions):
    for section in file1_functions:
        common_functions = file1_functions[section].intersection(file2_functions.get(section, set()))
        diff_file1 = file1_functions[section] - common_functions
        diff_file2 = file2_functions.get(section, set()) - common_functions

        if diff_file1 or diff_file2:
            print(f"\nSection: {section}")
            print(f"Functions unique to file1: {diff_file1}")
            print(f"Functions unique to file2: {diff_file2}")


def display_help():
    print("Usage: python compare_files.py file1.txt file2.txt")
    print("Options:")
    print("  --help, -h   Display this help message")
    print("This fuciton is meant to compare 2 different outputs from the parse_output.py.")
    print("It is trying to find non-determinism when 2 configs for comparison are ran twice.")
    print("They produce comp.log files that need to be compared.")

if __name__ == "__main__":
    if len(sys.argv) == 2 and (sys.argv[1] == "--help" or sys.argv[1] == "-h"):
        display_help()
        sys.exit(0)
    elif len(sys.argv) != 3:
        print("Invalid usage. Run 'python compare_files.py --help' for usage information.")
        sys.exit(1)

    file1_path = sys.argv[1]
    file2_path = sys.argv[2]

    file1_functions = load_functions(file1_path)
    file2_functions = load_functions(file2_path)

    compare_function_names(file1_functions, file2_functions)
