import pandas as pd
import os

def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return str(e)
def delete_file(file_path):
    try:
        os.remove(file_path)
        return "File deleted successfully."
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return str(e)

file_path = './original_data.txt'
file_content = read_file(file_path)

file_path_final_word = './original_data_word.txt'
delete_file(file_path_final_word)

file_path_final_ubung = './original_data_ubung.txt'
delete_file(file_path_final_ubung)

with open(file_path, 'r') as final_file:
    lines_ubung = final_file.readlines()  # Read all lines from the file
    lines_ubung = [line.strip() + '\n' for line in lines_ubung]  # Strip leading/trailing whitespace and add newline
    lines_ubung = [line.rstrip().replace(' ÜB', '') + '\n' if line.rstrip().endswith(' ÜB') else line for line in lines_ubung]  # Remove ' ÜB' if it is at the end of the line
    lines_ubung = [line[line.rfind(' '):] for line in lines_ubung]  # Keep only the last word of each line
    lines_ubung = [line[:-2] + '\n' for line in lines_ubung]  # Remove the last two characters and add newline

with open(file_path_final_ubung, 'w') as final_file:
    final_file.writelines(lines_ubung)

with open(file_path, 'r') as final_file:
    lines_word = final_file.readlines()  # Read all lines from the file
    lines_word = [line.strip() + '\n' for line in lines_word]  # Strip leading/trailing whitespace and add newline
    lines_word = [line[:line.find(' ')].strip() + '\n' if ' ' in line else line for line in lines_word]  # Keep only the part before the first space
    lines_word = [line.replace(',', '').replace('|', '') for line in lines_word]  # Remove ',' and '|'
with open(file_path_final_word, 'w') as final_file:
    final_file.writelines(lines_word)


# Read the processed files
with open(file_path_final_word, 'r') as file_word, open(file_path_final_ubung, 'r') as file_ubung:
    words = file_word.readlines()
    ubungs = file_ubung.readlines()
    # Create a DataFrame
    data = {
        'Word': [word.strip() for word in words],
        'Lecture': [ubung.strip().split('/')[0] for ubung in ubungs],
        'Ubung': [ubung.strip().split('/')[1] if '/' in ubung else '' for ubung in ubungs]
    }
    df = pd.DataFrame(data)

    # Sort the DataFrame based on the 'Lecture' column
    df['Lecture'] = df['Lecture'].astype(int)
    df['Ubung'] = pd.to_numeric(df['Ubung'], errors='coerce').fillna(0).astype(int)
    df = df.sort_values(by='Lecture')

    # Save the DataFrame to a CSV file
    output_csv_path = './final_table.csv'
    df.to_csv(output_csv_path, index=False)

