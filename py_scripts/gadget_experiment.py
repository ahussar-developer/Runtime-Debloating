import subprocess
import os
import re
import shutil
import json
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MaxNLocator
from fractions import Fraction

def change_dir(dir):
    os.chdir(dir)
    #print("Current directory:", os.getcwd())

def run_GSA(num):
    gsa_dir = "GadgetSetAnalyzer/src/"
    initial_directory = os.getcwd()
    change_dir(gsa_dir)
    # Run your Python script and capture the output
    command = [
        "python3",
        "GSA.py",
        "--output_metrics",
        "/home/user/test/nginx-1.24.0/objs/nginx",
        "--variants",
        'Aggressive="/home/user/test/nginx-1.24.0/objs/nginx_pass"'
    ]
    #os.system('python3 GSA.py --output_metrics /home/user/test/nginx-1.24.0/objs/nginx --variants Aggressive="/home/user/test/nginx-1.24.0/objs/nginx_pass"')
    try:
        output = subprocess.check_output('python3 GSA.py --output_metrics /home/user/test/nginx-1.24.0/objs/nginx --variants Aggressive="/home/user/test/nginx-1.24.0/objs/nginx_pass"', shell=True, text=True)
        #print("Standard Output:", output)
    except subprocess.CalledProcessError as e:
        print("Command failed with return code:", e.returncode)
        print("Standard Output:", e.output)


    # Extract the folder path using a regular expression
    match = re.search(r'Writing metrics files to (results/[^"]+)', output)
    if match:
        tmp = match.group(1)
        tmp_split = tmp.split("\n")
        folder_path = tmp_split[0]
    else:
        print_red("Error: Unable to extract folder path from the output.")
        exit(1)

    # Create a new folder name with the specified 'num'
    new_folder_name = f"results/results_{num}"
    if os.path.exists(new_folder_name):
        # Delete the directory and its contents
        shutil.rmtree(new_folder_name)
    os.rename(folder_path, new_folder_name)
    csv = f"results/results_{num}/SpecialPurpose_GadgetCounts_Reduction.csv"
    with open(csv, 'r') as file:
        lines = file.readlines()[1:]
    with open(csv, 'w') as file:
        file.writelines(lines)
    change_dir(initial_directory)
    print_green(f"GSA Successfully Ran. Created {new_folder_name}")
    return new_folder_name

def get_Gadgets(csv):
    df = pd.read_csv(csv)
    # Identify the 'Aggressive' row
    aggressive_row = df['Package Variant'] == 'Aggressive'

    # List of columns to process
    columns_to_process = df.columns[df.dtypes == 'O']

    # Loop over columns and replace parentheses
    for column in columns_to_process:
        df.loc[aggressive_row, column] = df.loc[aggressive_row, column].str.replace(r'\([^)]*\)', '', regex=True)

    # Print the modified DataFrame
    #print(df)
    return df

def convert_to_fraction(value, original_value):
    # Extract the denominator from the original row
    denominator = int(original_value.split()[-1])
    
    # If the value contains " of ", extract the numerator
    if ' of ' in value:
        numerator = int(value.split()[0])
    else:
        # If the value is in the format "X (Y)", extract the first number
        numerator = int(value.split()[0])

    return Fraction(numerator, denominator)

def get_Expressivity(csv):
    df = pd.read_csv(csv)
    # Iterate through columns and update both "Original" and "Aggressive" rows
    for column in df.columns[1:]:
        original_value = df.loc[df['Package Variant'] == 'Original', column].values[0]
        df[column] = df[column].apply(lambda x: str(convert_to_fraction(x, original_value)))

    # Print the modified DataFrame
    #print(df)
    return df

def build_pass():
    initial_directory = os.getcwd()
    dir_path = "/home/user/passes/"
    scirpt = " build_nginx.sh"
    change_dir(dir_path)
    os.system("./build_nginx.sh")
    change_dir(initial_directory)

def check_log():
    log_path = "/home/user/passes/nginx-pass.log"
    with open(log_path, 'r') as file:
        # Read all lines from the file
        lines = file.readlines()
        # Check if the desired line exists
        for line in lines:
            if "Num functions to erase:" in line:
                split_result = line.split(':')
                num = split_result[1].strip()
                print_red("Erased Functions: "+ num)
                return (True, num)
        return (False, -1)

def print_red(text):
    print("\033[91m" + text + "\033[0m")

def print_green(text):
    print("\033[92m" + text + "\033[0m")

def run_pass():
    opt_dir = "/home/user/passes"
    initial_directory = os.getcwd()
    change_dir(opt_dir)

    # First opt command
    os.system("opt -O3 /home/user/test/nginx-1.24.0/objs/nginx.0.0.preopt.bc -o /home/user/test/nginx-1.24.0/objs/nginx.0.0.preopt.bc")
    os.system('opt -load-pass-plugin build/DebloatPass/libDebloatPass.so --passes="debloat" /home/user/test/nginx-1.24.0/objs/nginx.0.0.preopt.bc -o /home/user/test/nginx-1.24.0/objs/nginx_pass.bc 2> nginx-pass.log')
    success, num_erased = check_log()
    if(not success):
        print_red("LLVM Pass did not run correctly!")
    else:
        print_green("LLVM Pass Successful.")

    # Change back to the original directory
    change_dir(initial_directory)
    return num_erased

def create_exe():
    initial_directory = os.getcwd()
    nginx_dir = "/home/user/test/nginx-1.24.0/objs/"
    change_dir(nginx_dir)
    
    orig_file = "nginx_pass.bc"
    orig_name = os.path.splitext(os.path.basename(orig_file))[0]
    
    # Run llc command
    llc_command = ["llc", "-filetype=obj", "-relocation-model=pic", orig_file]
    subprocess.run(llc_command, check=True)
    
    # Run clang command
    clang_command = ["clang", "-g", f"{orig_name}.o", "-lcrypt", "-lpcre2-8", "-lz", "-o", "nginx_pass", "-fPIC"]
    subprocess.run(clang_command, check=True)

    print_green("Executable created.")
    
    change_dir(initial_directory)
    
def run_llvm(fuc_num):
    build_pass()
    num_erased = run_pass()
    create_exe()
    return num_erased

def erase_file_contents(file_path):
    with open(file_path, 'w'):
        pass 

def get_line_by_number(file_path, line_number):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    if 1 <= line_number <= len(lines):
        return lines[line_number - 1]
    else:
        return f"Error: Line {line_number} does not exist in the file."

def write_list_to_file(file_path, my_list):
    with open(file_path, 'w') as file:
        for item in my_list:
            file.write(str(item) + '\n')

def del_GSA_Results():
    results_dir = "/home/user/GadgetSetAnalyzer/src/results/"
    prefix = "results_"
    # Get a list of all directories in the specified directory
    directories = [d for d in os.listdir(results_dir) if os.path.isdir(os.path.join(results_dir, d)) and d.startswith(prefix)]

    # Iterate through directories and remove them
    for subdirectory in directories:
        full_path = os.path.join(results_dir, subdirectory)
        shutil.rmtree(full_path)
        print(f"Deleted folder: {full_path}")

def extract_functions(filename, target_line):
    functions = []

    with open(filename, 'r') as file:
        for current_line, line in enumerate(file, start=1):
            # Remove leading and trailing whitespaces
            line = line.strip()

            # Skip empty lines
            if not line:
                continue
            if "Error: Line" in line:
                print("Error found: Exiting the script.")
                print_red(line)
                exit()
            functions.append(line)

            # Check if the target line is reached
            if current_line == target_line:
                break

    return functions

def create_GSA_Results(num_start, num_end, file):
    dir_path = "/home/user/passes/pass_files/nginx/"
    trace_file = "orig_llvm_all_tests.log"
    exp_file = "exp_funcs.txt"
    erased_funcs = {}
    erase_file_contents(dir_path+trace_file)
    for i in range(num_start,num_end):
        functions = extract_functions(dir_path+exp_file,i)
        print(len(functions))
        # overwrites the current file with new list
        write_list_to_file(dir_path+trace_file, functions)
        num_erased = run_llvm(i)
        erased_funcs[i] = num_erased
        run_GSA(i)
    write_dic_to_file(erased_funcs, file)
    return erased_funcs

def add_Func_Num_Col(df):
    # Add a new column "Functions Kept" with conditional assignment
    df["Functions Kept"] = df["Package Variant"].astype(str).apply(lambda x: int(x) if x.isdigit() else 0)

def add_Code_Num_Col(df, orig_value, agg_value, col):
    df['Code Lines of Kept Functions'] = 0  # Default value for all rows
    df.loc[df['Package Variant'] == 'Original', 'Code Lines of Kept Functions'] = orig_value  # Value for 'Original' package
    df.loc[df['Package Variant'] == str(col), 'Code Lines of Kept Functions'] = agg_value  # Value for 'Aggressive' package

def add_Num_Del_Func(df, agg_value, col):
    df['Deleted Functions'] = 0  # Default value for all rows
    df.loc[df['Package Variant'] == str(col), 'Deleted Functions'] = agg_value  # Value for 'Aggressive' package

def add_Total_Pass_Code_Lines(df):
    original_value = df.loc[df['Package Variant'] == 'Original', 'Code Lines of Kept Functions'].iloc[0]
    df['Total Code Lines After Pass'] = df.apply(lambda row: original_value - row['Code Lines of Kept Functions'] if row['Package Variant'] != 'Original' else None, axis=1)

def create_disassembly():
    llvm_bc_file = "/home/user/test/nginx-1.24.0/objs/nginx.0.0.preopt.bc"
    output_ll_file = "/home/user/test/nginx-1.24.0/objs/nginx_human.ll"
    function_file = "/home/user/passes/pass_files/nginx/exp_funcs.txt"
    functions = extract_functions(function_file,448)
    # Use llvm-dis to disassemble the binary file into LLVM IR
    print(f"DISASSEMBLE: llvm-dis {llvm_bc_file} -o {output_ll_file}")
    os.system(f"llvm-dis {llvm_bc_file} -o {output_ll_file}")
    with open(output_ll_file, 'r') as file:
        ir_content = file.read()
    return ir_content

def get_lines_per_function():
    output_ll_file = "/home/user/test/nginx-1.24.0/objs/nginx_human.ll"
    #if not os.path.exists(output_ll_file):
    #    ir_content = create_disassembly
    #else:    
    #    with open(output_ll_file, 'r') as file:
    #        ir_content = file.readlines()
    with open(output_ll_file, 'r') as file:
            ir_content = file.readlines()
    pattern = r'@([^(\s]+)\s*\('
    lines_of_code_per_function = {}
    lines_of_code_per_function["ORIGINAL"] = len(ir_content)
    count = 0
    begin = False
    func = ""
    for line in ir_content:
        line = line.strip()
        if begin == True:
            count += 1
        if line.startswith('define') and line.endswith('{'):
            match = re.search(pattern, line)
            if match:
                function_name = match.group(1)
                #print("Function Name:", function_name)
                begin = True
                func = function_name
        if line.startswith('}'):
            #print(f"Count: {count}")
            lines_of_code_per_function[func] = count
            begin = False
            count = 0
            func = ""
    return lines_of_code_per_function

def calc_code_lines(func_code, target_line):
    file = "/home/user/passes/pass_files/nginx/exp_funcs.txt"
    functions = extract_functions(file, target_line)
    total_lines = 0
    for f in functions:
        if f in func_code:
            total_lines += func_code[f]
    #print(f"Total Code Lines: {total_lines}")
    return total_lines

def process_CSVs(num_start, num_end, func_code, erased_funcs):
    initial_directory = os.getcwd()
    results_dir = "/home/user/GadgetSetAnalyzer/src/results/"
    csv_1 = "Expressivity_Counts.csv"
    csv_2 = "GadgetCounts_Reduction.csv"
    csv_3 = "SpecialPurpose_GadgetCounts_Reduction.csv"
    # Create an empty DataFrame
    combined_df1 = pd.DataFrame()
    combined_df2 = pd.DataFrame()
    combined_df3 = pd.DataFrame()
    change_dir(results_dir)
    for i in range(num_start, num_end):
        #i += 1
        folder = f"results_{i}"
        orig_dir = os.getcwd()
        change_dir(folder)
        
        df1 = get_Expressivity(csv_1)
        df2 = get_Gadgets(csv_2)
        df3 = get_Gadgets(csv_3)
        
        df1['Package Variant'] = df1['Package Variant'].replace('Aggressive', str(i))
        df2['Package Variant'] = df2['Package Variant'].replace('Aggressive', str(i))
        df3['Package Variant'] = df3['Package Variant'].replace('Aggressive', str(i))
        
        num_lines = int(calc_code_lines(func_code, i))
        orig_num = func_code["ORIGINAL"]
        add_Code_Num_Col(df1,orig_num, num_lines, i)
        add_Code_Num_Col(df2,orig_num, num_lines, i)
        add_Code_Num_Col(df3,orig_num, num_lines, i)
        num_erased = int(erased_funcs[str(i)])
        add_Num_Del_Func(df1,num_erased, i)
        add_Num_Del_Func(df2,num_erased, i)
        add_Num_Del_Func(df3,num_erased, i)
        
        
        combined_df1 = pd.concat([combined_df1, df1], ignore_index=True)
        combined_df2 = pd.concat([combined_df2, df2], ignore_index=True)
        combined_df3 = pd.concat([combined_df3, df3], ignore_index=True)
        
        
        change_dir(orig_dir)
    combined_df1 = (combined_df1.drop_duplicates(subset="Package Variant")).reset_index(drop=True)
    combined_df2 = (combined_df2.drop_duplicates(subset="Package Variant")).reset_index(drop=True)
    combined_df3 = (combined_df3.drop_duplicates(subset="Package Variant")).reset_index(drop=True)
    add_Func_Num_Col(combined_df1)
    add_Func_Num_Col(combined_df2)
    add_Func_Num_Col(combined_df3)
    #print(combined_df1)
    #print(combined_df2)
    #print(combined_df3)
    change_dir(initial_directory)
    return combined_df1, combined_df2, combined_df3
        
def plot_all_counts(count_df):
    plt.figure(figsize=(10, 6))
    # Convert to Numerics
    count_df['Total Gadgets'] = pd.to_numeric(count_df['Total Gadgets'], errors='raise')
    count_df['ROP Gadgets'] = pd.to_numeric(count_df['ROP Gadgets'], errors='raise')
    count_df['JOP Gadgets'] = pd.to_numeric(count_df['JOP Gadgets'], errors='raise')
    count_df['COP Gadgets'] = pd.to_numeric(count_df['COP Gadgets'], errors='raise')
    count_df['Special Purpose Gadgets'] = pd.to_numeric(count_df['Special Purpose Gadgets'], errors='raise')
    count_df['Code Lines of Kept Functions'] = pd.to_numeric(count_df['Code Lines of Kept Functions'], errors='raise')
    
    ## TOTAL Gadgets - Outliers Removed
    mean_value = count_df['Total Gadgets'].mean()
    std_value = count_df['Total Gadgets'].std()
    threshold = 3 * std_value
    outliers_mask = (count_df['Total Gadgets'] > (mean_value - threshold)) & (count_df['Total Gadgets'] < (mean_value + threshold))
    df_total_outliers = count_df[outliers_mask]
    plt.scatter(df_total_outliers["Deleted Functions"], df_total_outliers["Total Gadgets"], label="Total Gadgets", c="blue")
    num_outliers = count_df.shape[0] - count_df[outliers_mask].shape[0]
    print(f"Total Gadgets Outliers Removed: {num_outliers}")
    for index, row in count_df[~outliers_mask].iterrows():
        print(f"Associated Row: {row['Package Variant']}")
    
    ## ROP Gadgets - Outliers Removed
    mean_value = count_df['ROP Gadgets'].mean()
    std_value = count_df['ROP Gadgets'].std()
    threshold = 3 * std_value
    outliers_mask = (count_df['ROP Gadgets'] > (mean_value - threshold)) & (count_df['ROP Gadgets'] < (mean_value + threshold))
    df_rop_outliers = count_df[outliers_mask]
    plt.scatter(df_rop_outliers["Deleted Functions"], df_rop_outliers["ROP Gadgets"], label="ROP Gadgets", c="red")
    num_outliers = count_df.shape[0] - count_df[outliers_mask].shape[0]
    print(f"ROP Gadgets Outliers Removed: {num_outliers}")
    for index, row in count_df[~outliers_mask].iterrows():
        print(f"Associated Row: {row['Package Variant']}")
    
    ## JOP Gadgets - Outliers Removed
    mean_value = count_df['JOP Gadgets'].mean()
    std_value = count_df['JOP Gadgets'].std()
    threshold = 3 * std_value
    outliers_mask = (count_df['JOP Gadgets'] > (mean_value - threshold)) & (count_df['JOP Gadgets'] < (mean_value + threshold))
    df_jop_outliers = count_df[outliers_mask]
    plt.scatter(df_jop_outliers["Deleted Functions"], df_jop_outliers["JOP Gadgets"], label="JOP Gadgets", c="orange")
    num_outliers = count_df.shape[0] - count_df[outliers_mask].shape[0]
    print(f"JOP Gadgets Outliers Removed: {num_outliers}")
    for index, row in count_df[~outliers_mask].iterrows():
        print(f"Associated Row: {row['Package Variant']}")
    
    ## COP Gadgets - Outliers Removed
    mean_value = count_df['COP Gadgets'].mean()
    std_value = count_df['COP Gadgets'].std()
    threshold = 3 * std_value
    outliers_mask = (count_df['COP Gadgets'] > (mean_value - threshold)) & (count_df['COP Gadgets'] < (mean_value + threshold))
    df_cop_outliers = count_df[outliers_mask]
    plt.scatter(df_cop_outliers["Deleted Functions"], df_cop_outliers["COP Gadgets"], label="COP Gadgets", c="green")
    num_outliers = count_df.shape[0] - count_df[outliers_mask].shape[0]
    print(f"COP Gadgets Outliers Removed: {num_outliers}")
    for index, row in count_df[~outliers_mask].iterrows():
        print(f"Associated Row: {row['Package Variant']}")
    
    ## Special Purpose Gadgets - Outliers Removed
    mean_value = count_df['Special Purpose Gadgets'].mean()
    std_value = count_df['Special Purpose Gadgets'].std()
    threshold = 3 * std_value
    outliers_mask = (count_df['Special Purpose Gadgets'] > (mean_value - threshold)) & (count_df['Special Purpose Gadgets'] < (mean_value + threshold))
    df_sp_outliers = count_df[outliers_mask]
    plt.scatter(df_sp_outliers["Deleted Functions"], df_sp_outliers["Special Purpose Gadgets"], label="Special Purpose Gadgets", c="purple")
    num_outliers = count_df.shape[0] - count_df[outliers_mask].shape[0]
    print(f"Special Purpose Gadgets Outliers Removed: {num_outliers}")
    for index, row in count_df[~outliers_mask].iterrows():
        print(f"Associated Row: {row['Package Variant']}")
    
    plt.xlabel("Number of Deleted Functions")
    plt.ylabel("Count")
    plt.title("Scatter Plot: Deleted Functions vs Various Gadgets")
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.legend()
    plt.legend(bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3)
    plt.savefig("del_func_vs_gadget_count_outliers_removed.png", bbox_inches='tight')
    plt.clf()
    
    plt.scatter(df_total_outliers["Code Lines of Kept Functions"], df_total_outliers["Total Gadgets"], label="Total Gadgets", c="blue")
    plt.scatter(df_rop_outliers["Code Lines of Kept Functions"], df_rop_outliers["ROP Gadgets"], label="ROP Gadgets", c="red")
    plt.scatter(df_jop_outliers["Code Lines of Kept Functions"], df_jop_outliers["JOP Gadgets"], label="JOP Gadgets", c="orange")
    plt.scatter(df_cop_outliers["Code Lines of Kept Functions"], df_cop_outliers["COP Gadgets"], label="COP Gadgets", c="green")
    plt.scatter(df_sp_outliers["Code Lines of Kept Functions"], df_sp_outliers["Special Purpose Gadgets"], label="Special Purpose Gadgets", c="purple")
    plt.xlabel("Lines of Code Kept")
    plt.ylabel("Count")
    plt.title("Scatter Plot: Kept Code Lines vs Various Gadgets")
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.legend()
    plt.legend(bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3)
    plt.savefig("code_lines_vs_gadget_count_outliers_removed.png", bbox_inches='tight')
    plt.clf()
    ## NO OUTLIERS REMOVED PLOT
    '''
    # Scatter plot with different colors for each column
    plt.scatter(count_df["Deleted Functions"], count_df["Total Gadgets"], label="Total Gadgets", c="blue")
    plt.scatter(count_df["Deleted Functions"], count_df["ROP Gadgets"], label="ROP Gadgets", c="red")
    plt.scatter(count_df["Deleted Functions"], count_df["JOP Gadgets"], label="JOP Gadgets", c="orange")
    plt.scatter(count_df["Deleted Functions"], count_df["COP Gadgets"], label="COP Gadgets", c="green")
    plt.scatter(count_df["Deleted Functions"], count_df["Special Purpose Gadgets"], label="Special Purpose Gadgets", c="purple")
    plt.xlabel("Number of Deleted Functions")
    plt.ylabel("Count")
    plt.title("Scatter Plot: Deleted Functions vs Various Gadgets")
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.legend()
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.savefig("del_func_vs_gadget_count.png", bbox_inches='tight')
    plt.clf()
    '''
    return

def plot_exploit_gadgets(df):
    # Truncate the strings to whole numbers
    columns_to_truncate = ['Practical ROP Exploit', 'ASLR-Proof Practical ROP Exploit', 'Simple Turing Completeness']
    df[columns_to_truncate] = df[columns_to_truncate].apply(lambda x: x.str.split('/').str[0])

    # Convert to numeric
    df[columns_to_truncate] = df[columns_to_truncate].apply(pd.to_numeric)

    
    # Plotting
    # Create a strip plot
    plt.figure(figsize=(10, 6))
    
    df_filtered = df[df['Package Variant'] != 'Original']
    
    # Melt the DataFrame to long format
    df_long = pd.melt(df_filtered, id_vars=['Code Lines of Kept Functions'], value_vars=columns_to_truncate, var_name='ROP Type', value_name='ROP Value')
    
    # Create a strip plot with hue
    sns.set(style="whitegrid")
    sns.stripplot(x='ROP Value', y='Code Lines of Kept Functions', hue='ROP Type', data=df_long, palette="muted", size=8, jitter=True)
    # Invert the y-axis
    #plt.gca().invert_yaxis()
    
    plt.xlabel('Count')
    plt.ylabel('Num Code Lines of Kept Functions')
    plt.title('Strip Plot of Gadget Chain Exploits vs Code Lines of Kept Functions')
    plt.legend(title='Gadget Chain Exploits',  bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3)
    plt.savefig("code_lines_vs_exploit.png", bbox_inches='tight')
    plt.clf()

def plot_special_gadgets(df):
    cols = ["Syscall Gadgets", "JOP Dispatcher Gadgets", "JOP Dataloader Gadgets", "JOP Initializers", "JOP Trampolines", "COP Dispatcher Gadgets", "COP Dataloader Gadgets", "COP Initializers", "COP Strong Trampoline Gadgets", "COP Intra-stack Pivot Gadgets", "Code Lines of Kept Functions"]#, "Deleted Functions", "Functions Kept"]
    df[cols] = df[cols].apply(pd.to_numeric)
    filtered_df = df[cols]
    filtered_df = filtered_df.drop(0)
    
    # Calculate the correlation matrix excluding "Code Lines of Kept Functions"
    correlation_matrix = filtered_df.corr()

    # Extract the correlation of each variable with "Code Lines of Kept Functions"
    correlation_with_code_lines = correlation_matrix.loc["Code Lines of Kept Functions"]
    
    # Exclude "Code Lines of Kept Functions" from x-axis labels
    #x_labels = [label for label in correlation_matrix.columns if label != "Code Lines of Kept Functions"]

    sns.heatmap(correlation_with_code_lines.values.reshape(1, -1), annot=True, cmap='coolwarm', xticklabels=correlation_with_code_lines.index)
    #sns.heatmap(correlation_with_code_lines.values.reshape(1, -1), annot=True, cmap='coolwarm',xticklabels=x_labels)
    plt.title("Correlation Heatmap: Variables vs Code Lines of Kept Functions")
    plt.savefig("special_gadgets_vs_code_lines.png", bbox_inches='tight')
    plt.clf()
    '''
    plt.scatter(filtered_df["Syscall Gadgets"], filtered_df["Code Lines of Kept Functions"], label="Syscall Gadgets", c="red")
    plt.scatter(filtered_df["JOP Dispatcher Gadgets"], filtered_df["Code Lines of Kept Functions"], label="JOP Dispatcher Gadgets", c="#4169E1")
    plt.scatter(filtered_df["JOP Dataloader Gadgets"], filtered_df["Code Lines of Kept Functions"], label="JOP Dataloader Gadgets", c="#1E90FF")
    plt.scatter(filtered_df["JOP Initializers"], filtered_df["Code Lines of Kept Functions"], label="JOP Initializers", c="#4682B4")
    plt.scatter(filtered_df["JOP Trampolines"], filtered_df["Code Lines of Kept Functions"], label="JOP Trampolines", c="#B0C4DE")

    plt.xlabel("Count")
    plt.ylabel("Number of Code Lines from Kept Functions")
    plt.title("Scatter Plot: Special Gadgets vs Code Lines of Kept Functions")
    plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.savefig("special_gadgets_vs_code_lines.png", bbox_inches='tight')
    plt.clf()
    '''


def count_correlation_matrix(count_df):
    # Select relevant columns for the pairs plot
    columns_to_plot = ["Deleted Functions","Code Lines of Kept Functions", "Total Gadgets", "ROP Gadgets", "JOP Gadgets", "COP Gadgets", "Special Purpose Gadgets"]
    
    count_df[columns_to_plot] = count_df[columns_to_plot].apply(pd.to_numeric)
    filtered_df = count_df[columns_to_plot]
    filtered_df = filtered_df.drop(0)
    
    correlation_matrix = filtered_df[columns_to_plot].corr()
    
    correlation_with_code_lines = correlation_matrix.loc["Code Lines of Kept Functions"]
    
    # Exclude "Code Lines of Kept Functions" from x-axis labels
    #x_labels = [label for label in correlation_matrix.columns if label != "Code Lines of Kept Functions"]

    sns.heatmap(correlation_with_code_lines.values.reshape(1, -1), annot=True, cmap='coolwarm', xticklabels=correlation_with_code_lines.index)
    #sns.heatmap(correlation_with_code_lines.values.reshape(1, -1), annot=True, cmap='coolwarm',xticklabels=x_labels)
    plt.title("Correlation Heatmap for Gradget Counts vs Code Lines of Kept Functions")
    plt.savefig("gadget_count_corr_heat_map.png", bbox_inches='tight')
    plt.clf()

    # Display the correlation matrix
    #print("Correlation Matrix:")
    #print(correlation_matrix)

def exploit_correlation_matrix(df):
    
    # Truncate the strings to whole numbers
    columns_to_truncate = ['Practical ROP Exploit', 'ASLR-Proof Practical ROP Exploit', 'Simple Turing Completeness']
    df[columns_to_truncate] = df[columns_to_truncate].apply(lambda x: x.str.split('/').str[0])

    # Convert to numeric
    df[columns_to_truncate] = df[columns_to_truncate].apply(pd.to_numeric)
    
    
    # Select relevant columns for the pairs plot
    columns_to_plot = ["Deleted Functions","Code Lines of Kept Functions",'Practical ROP Exploit', 'ASLR-Proof Practical ROP Exploit', 'Simple Turing Completeness']
    
    df[columns_to_plot] = df[columns_to_plot].apply(pd.to_numeric)
    filtered_df = df[columns_to_plot]
    filtered_df = filtered_df.drop(0)
    
    correlation_matrix = filtered_df[columns_to_plot].corr()
    
    correlation_with_code_lines = correlation_matrix.loc["Code Lines of Kept Functions"]
    
    # Exclude "Code Lines of Kept Functions" from x-axis labels
    #x_labels = [label for label in correlation_matrix.columns if label != "Code Lines of Kept Functions"]

    sns.heatmap(correlation_with_code_lines.values.reshape(1, -1), annot=True, cmap='coolwarm', xticklabels=correlation_with_code_lines.index)
    #sns.heatmap(correlation_with_code_lines.values.reshape(1, -1), annot=True, cmap='coolwarm',xticklabels=x_labels)
    plt.title("Correlation Heatmap for Gradget Exploits vs Code Lines of Kept Functions")
    plt.savefig("gadget_exploits_corr_heat_map.png", bbox_inches='tight')
    plt.clf()

    # Display the correlation matrix
    print("Correlation Matrix:")
    print(correlation_matrix)

def process_Gadgets(exp_df, count_df, special_df):
    plot_all_counts(count_df)
    #count_correlation_matrix(count_df)
    
    #plot_exploit_gadgets(exp_df)
    #exploit_correlation_matrix(exp_df)
    
    #plot_special_gadgets(special_df)
    
    #column_names_str = ', '.join(f'"{col}"' for col in special_df.columns)
    #print(f"Column Names: {column_names_str}")
    
    
    

def write_dic_to_file(dictionary, filename):
    with open(filename, 'w') as file:
        json.dump(dictionary, file)
def read_dict_from_file(filename):
    with open(filename, 'r') as file:
        dictionary = json.load(file)
    return dictionary


num_start = 1
num_end = 445
file = "erased_functions.txt"
#erased_funcs = create_GSA_Results(num_start,num_end, file)
read_erased_funcs = read_dict_from_file(file)

## UNCOMMENT for ANLAYSIS
func_code = get_lines_per_function()
exp_df, count_df, special_df = process_CSVs(1,num_end, func_code, read_erased_funcs)

## UPDATE TO WORK WITH LINES OF CODE COL
process_Gadgets(exp_df, count_df, special_df)

# exp_num = 448
#exp_num = 188 # Failed earlier on 189..doesnt look like a space error tho
# Clean Up First - Delete Previous GSA Results
#del_GSA_Results()

# Create GSA Results
#create_GSA_Results(1,exp_num)

#exp_df, count_df, special_df = process_CSVs(exp_num)
#process_Gadgets(exp_df, count_df, special_df)


trace_file = "/home/user/passes/pass_files/nginx/orig_llvm_all_tests.log"
erase_file_contents(trace_file)

