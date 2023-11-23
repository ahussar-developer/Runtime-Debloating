## All of these ocme from the other vm where the static reachability file is output
## look to other vm for the output the cfg needs to be in for this to work
import sys

def read_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return lines

def parse_functions(lines):
    function_dict = {}
    for line in lines:
        parts = line.strip().split(':')
        caller = parts[0].strip()
        callees = [callee.strip() for callee in parts[1].split(',')]
        function_dict[caller] = callees
    return function_dict

def compare_functions(file1_functions, file2_functions):
    common_callers = set(file1_functions.keys()) & set(file2_functions.keys())
    different_callees = {}

    for caller in common_callers:
        callees_file1 = set(file1_functions[caller])
        callees_file2 = set(file2_functions[caller])

        if callees_file1 != callees_file2:
            different_callees[caller] = {
                'file1': callees_file1 - callees_file2,
                'file2': callees_file2 - callees_file1
            }

    missing_callers_file1 = set(file1_functions.keys()) - common_callers
    missing_callers_file2 = set(file2_functions.keys()) - common_callers

    return {
        'different_callees': different_callees,
        'missing_callers_file1': missing_callers_file1,
        'missing_callers_file2': missing_callers_file2
    }

def print_results(results):
    print("Different Callees:")
    for caller, callees in results['different_callees'].items():
        print(f"{caller}:")
        print(f"  File 1: {callees['file1']}")
        print(f"  File 2: {callees['file2']}")

    print("\nMissing Callers:")
    print(f"  File 1: {results['missing_callers_file1']}")
    print(f"  File 2: {results['missing_callers_file2']}")

def display_help():
    print("Usage: python script.py file1.txt file2.txt")
    print("Options:")
    print("  --help, -h   Display this help message")
    print("Parses the original config static-reachability.csv against the new one from the new/different config.")
    print("Output should be redirected via > name.log file that will contain function names followed by what is reachable from that function")
    print("from the new csv and the original csv.")

if __name__ == "__main__":
    if len(sys.argv) == 2 and (sys.argv[1] == "--help" or sys.argv[1] == "-h"):
        display_help()
        sys.exit(0)
    elif len(sys.argv) != 3:
        print("Usage: python script.py file1.txt file2.txt")
        sys.exit(1)

    file1_path = sys.argv[1]
    file2_path = sys.argv[2]

    file1_lines = read_file(file1_path)
    file2_lines = read_file(file2_path)

    file1_functions = parse_functions(file1_lines)
    file2_functions = parse_functions(file2_lines)

    comparison_results = compare_functions(file1_functions, file2_functions)

    print_results(comparison_results)
