import sys
import os

def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_command> <output_file_name>")
        return

    input_command = sys.argv[1]
    pathDcache = input_command[12:]
    newPath = "root" + pathDcache
    output_file = sys.argv[2]
    
    command_output = os.popen(input_command).read().strip().split('\n')

    # If the output file does not exist, create it
    if not os.path.exists(output_file):
        with open(output_file, 'w') as f:
            pass

    print("Writing to file:", output_file)

    with open(output_file, 'a') as f:
        for line in command_output:
            f.write(newPath + '/' + line + '\n')

if __name__ == "__main__":
    main()
