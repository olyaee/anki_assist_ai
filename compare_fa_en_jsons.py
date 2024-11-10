import os
import json

def read_json_files(directory):
    json_data = []
    for filename in os.listdir(directory):
        json_data.append(filename)
        # if filename.endswith('.json'):
        #     filepath = os.path.join(directory, filename)
        #     with open(filepath, 'r', encoding='utf-8') as file:
        #         json_data.append(json.load(file))
    return json_data

def main():
    files_dir = '/Users/ehsanolyaee/Documents/Code/anki_assist_ai/files'
    files_en_dir = '/Users/ehsanolyaee/Documents/Code/anki_assist_ai/files_EN'
    
    files_data = sorted([f for f in read_json_files(files_dir)])
    files_en_data = sorted([f for f in read_json_files(files_en_dir)])
    # print(files_data)
    # print(files_en_data)

    # differences = []
    files_data_set = set(files_data)
    files_en_data_set = set(files_en_data)
    
    differences = list(files_data_set.symmetric_difference(files_en_data_set))

    differences_files = [diff for diff in differences if diff in files_data_set]
    differences_files_en = [diff for diff in differences if diff in files_en_data_set]

    print("{:<40} {:<40}".format('Differences in files', 'Differences in files_EN'))
    for diff_file, diff_file_en in zip(differences_files, differences_files_en):
        print("{:<40} {:<40}".format(diff_file, diff_file_en))

    print("Differences in files:", differences_files)
    print("Differences in files_EN:", differences_files_en)

    print("Number of differences in files:", len(differences_files))
    print("Number of differences in files_EN:", len(differences_files_en))

    print("Number of files in files_data_set:", len(files_data_set))
    print("Number of files in files_en_data_set:", len(files_en_data_set))
    
    # print("Files Data:", files_data)
    # print("Files EN Data:", files_en_data)

if __name__ == "__main__":
    main()