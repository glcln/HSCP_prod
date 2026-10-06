import subprocess
import re
import os
import argparse 

OUTPUT_BASE_DIR = "/scratch/ui3_1/gcoulon/HSCP_prod/SIGNAL/"

def run_gfal_ls(path):
    try:
        output = subprocess.check_output(['gfal-ls', path], stderr=subprocess.STDOUT)
        return [line.decode() if isinstance(line, bytes) else line for line in output.splitlines()]
    except subprocess.CalledProcessError as e:
        print("Command failed with error: {}".format(e.output))
        return []

def run_gfal_copy(src, dst):
    os.makedirs(dst, exist_ok=True)
    try:
        print("Copying {} -> {}".format(src, dst))
        subprocess.check_call(['gfal-copy', '-r', src, dst])
    except subprocess.CalledProcessError as e:
        print("gfal-copy failed for {}: {}".format(src, e))

def extract_signal(name):
    parts = name.split('_')
    return parts[0] + "_" + parts[1]


def main(search_string):

    version_dir = os.path.join(OUTPUT_BASE_DIR, 'V' + search_string)
    os.makedirs(version_dir, exist_ok=True)

    print("Search string for version is {}".format(search_string))
    base_url = 'davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/'

    # 1 : Run the initial gfal-ls command
    initial_output = run_gfal_ls(base_url)

    # 2 : Filter the lines that contain 'HSCP'
    filtered_lines = [line for line in initial_output if 'HSCP' in line]

    print("Filtered lines with substring:")
    print(filtered_lines)

    # 3 : Iterate over each signal hypothesis directory
    for line in filtered_lines:
        second_path = base_url + line
        second_output = run_gfal_ls(second_path)
        signalHypothesis = extract_signal(line)

        for tline in second_output:
            if search_string in tline:
                print("Found version match: {}".format(tline))
                third_path = second_path + '/' + tline
                third_output = run_gfal_ls(third_path)

                # 4 : Each sub_item is an individual production for this version
                for sub_item in third_output:
                    fourth_path = third_path + '/' + sub_item
                    fourth_output = run_gfal_ls(fourth_path)

                    for last_item in fourth_output:
                        final_path = fourth_path + '/' + last_item
                        src_path = final_path.replace('davs', 'root')

                        # Production name = signalHypothesis + sub_item for uniqueness
                        prod_name = "{}_{}".format(signalHypothesis, sub_item)
                        dst_path = os.path.join(version_dir, prod_name)

                        # 5 : Copy recursively the production directory
                        run_gfal_copy(src_path, dst_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process a search string.')
    parser.add_argument('search_string', type=str, help='The input string to process.')

    args = parser.parse_args()
    main(args.search_string)
