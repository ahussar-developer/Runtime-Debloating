#!/usr/bin/env python3
import argparse
import os
import shutil

def parse_file(file_path, target_image):
    result = []

    with open(file_path, 'r') as file:
        # Skip the header line
        next(file)

        for line in file:
            procedure, image, address, calls, instructions = line.split()

            if image == target_image:
                #print(line)
                result.append(procedure)

    return result

def main():
    #file_path = '/home/user/test/nginx-1.24.0/proccount.out'
    #target_image = 'nginx'
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Parse a proccount.out (pin output) and extract function names for a target image.')

    # Define command-line arguments
    parser.add_argument('-file', dest='file_path', required=True, help='Path to the file to be parsed.')
    parser.add_argument('-target', dest='target_image', required=True, help='Target image to filter procedures.')
    parser.add_argument('-overwrite', action='store_true', help='Prompt user to overwrite the existing pass file.')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the parsing function with the provided arguments
    procedures = parse_file(args.file_path, args.target_image)


    output_file = args.target_image + '_pin.log'
    if os.path.exists(output_file):
        os.remove(output_file)

    with open(output_file, 'a') as new_file:
        for procedure in procedures:
            print(procedure)
            new_file.write(procedure+'\n')

    if args.overwrite:
        user_confirmation = input('Do you want to overwrite the existing pass file? (Enter "Y" for Yes, any other key for Cancel): ')
        if user_confirmation == 'Y':
            destination_path = '/home/user/passes/pass_files/orig_nginx_pin.log'
            shutil.copy(output_file, destination_path)
            print(f'Pass file overwritten and copied to: {destination_path}')
        else:
            print('Operation canceled. Existing pass file not overwritten.')

if __name__ == "__main__":
    main()