import pandas as pd
import re
from collections import Counter
import random

def read_verbs_with_prepositions(file_path):
    """Read and return verbs with prepositions from CSV file."""
    df = pd.read_csv(file_path, 
                    delimiter='\t',
                    names=['Verb', 'Preposition', 'Example'])
    return df

def display_top_verbs(df, n=5):
    """Display top n rows of the verbs dataframe."""
    print(f"\nTop {n} rows of the verbs with prepositions:")
    print(df.head(n))

def add_additional_verbs_to_exercises():
    """Process reflexive verbs and verbs with prepositions and add them to a new combined CSV file"""
    # Read existing word exercises
    word_exercises_df = pd.read_csv('b1.1/word_exercises.csv', delimiter=';')
    
    # Read reflexive verbs
    reflexive_df = pd.read_csv('b1.1/reflexive_verben_removed_duplicates.csv', 
                              delimiter='\t', 
                              names=['verb', 'example', 'unused'])
    reflexive_words = reflexive_df['verb'].tolist()
    
    # Read verbs with prepositions
    preposition_df = pd.read_csv('b1.1/verbs_with_praposition_removed_duplicates.csv', 
                                delimiter='\t', 
                                names=['verb', 'preposition', 'example'])
    preposition_words = preposition_df['verb'].tolist()
    
    # Combine all words and create new entries
    new_entries = []
    for word in reflexive_words + preposition_words:
        new_entries.append({
            'word': word,
            'lecture': int(random.randint(1, 6)),  # Store as integer
            'exercise': f"{random.randint(1, 10)}a"  # Add 'a' to match format of original file
        })
    
    # Create DataFrame from new entries
    new_df = pd.DataFrame(new_entries)
    
    # Combine with existing exercises
    combined_df = pd.concat([word_exercises_df, new_df], ignore_index=True)
    
    # Convert lecture to numeric for proper sorting
    combined_df['lecture'] = pd.to_numeric(combined_df['lecture'])
    
    # Custom sorting function for exercise column
    def exercise_sort_key(ex):
        # Extract number and letter parts
        match = re.match(r'(\d+)([a-z])?', str(ex))
        if match:
            num = int(match.group(1))
            letter = match.group(2) or 'a'  # Default to 'a' if no letter
            return (num, letter)
        return (float('inf'), 'z')  # Put invalid formats at the end
    
    # Sort by lecture numerically and exercise using custom key
    combined_df = combined_df.sort_values(
        by=['lecture', 'exercise'],
        key=lambda x: x.map(exercise_sort_key) if x.name == 'exercise' else x
    )
    
    # Save to new CSV file
    output_file = 'b1.1/word_exercises_combined_with_the_other_two_files.csv'
    combined_df.to_csv(output_file, index=False, sep=';')
    
    print(f"\nCreated new file '{output_file}' with {len(combined_df)} total words ({len(new_entries)} new words added)")
    print("\nFirst few entries of the combined file:")
    print(combined_df.head(10))  # Show more entries to verify sorting

def find_lines_without_numbers(file_path):
    """Find and return lines that don't contain any numbers."""
    result = []
    with open(file_path, 'r') as file:
        for line_num, line in enumerate(file, 1):
            line = line.strip()
            if line and not any(char.isdigit() for char in line):
                result.append((line_num, line))
    return result

def find_lines_without_pipe(file_path):
    """Find and return lines that don't contain the pipe character."""
    result = []
    with open(file_path, 'r') as file:
        for line_num, line in enumerate(file, 1):
            line = line.strip()
            if line and '|' not in line:
                result.append((line_num, line))
    return result

def display_filtered_lines(filtered_lines, filter_type=""):
    """Display the filtered lines with their line numbers."""
    print(f"\nWords without {filter_type}:")
    for line_num, line in filtered_lines:
        print(f"Line {line_num}: {line}")

def find_suffix_patterns(input_file):
    """Find and count all suffix patterns that start with a hyphen.
    
    Args:
        input_file (str): Path to input text file
    
    Returns:
        dict: Dictionary with suffix patterns and their counts
    """
    # Pattern to match word definitions that might contain suffix patterns
    # This looks for content before the exercise number
    pattern = r'(.*?)\s+\d+/\d+'
    
    # Pattern to find suffixes like -e, -en, -s, etc.
    suffix_pattern = r'(?:,\s*(?:der|die|das)[^,]*,\s*)(-[^,\s\d]+)'
    
    suffixes = []
    with open(input_file, 'r') as file:
        for line in file:
            # Get the word definition part
            match = re.search(pattern, line)
            if match:
                word_def = match.group(1)
                # Find all suffix patterns in the word definition
                suffix_matches = re.findall(suffix_pattern, word_def)
                suffixes.extend(suffix_matches)
    
    # Count occurrences of each suffix
    suffix_counts = Counter(suffixes)
    
    # Sort by frequency and then alphabetically
    sorted_suffixes = sorted(suffix_counts.items(), key=lambda x: (-x[1], x[0]))
    
    return sorted_suffixes

def create_word_exercise_csv(input_file, output_file, sort_by_exercise=False):
    """Create a CSV file with words, lecture numbers, and exercise numbers."""
    # Pattern to match exercise numbers like 4/8b, 1/9a, 5/2b üb at the end of line
    exercise_pattern = r'(.*?)\s+(\d+)/(\d+[a-z]*)(?: üb)?\s*$'
    
    # Write directly to file to avoid pandas quoting issues
    with open(output_file, 'w') as outfile:
        # Write header
        outfile.write('word;lecture;exercise\n')
        
        with open(input_file, 'r') as infile:
            words_and_exercises = []
            for line in infile:
                line = line.strip()
                if line:
                    # Find exercise number and text before it
                    match = re.search(exercise_pattern, line)
                    if match:
                        word_text = match.group(1).strip()
                        lecture_num = match.group(2)
                        exercise_num = match.group(3)
                        words_and_exercises.append((word_text, lecture_num, exercise_num))
            
            # Sort by lecture and then by exercise
            def sort_key(item):
                # Extract lecture and exercise for sorting
                lecture = int(item[1])
                # Extract numeric and alphabetic parts of exercise
                exercise_match = re.match(r'(\d+)([a-z]*)', item[2])
                if exercise_match:
                    exercise_num = int(exercise_match.group(1))
                    exercise_letter = exercise_match.group(2) or ''
                    return (lecture, exercise_num, exercise_letter)
                return (lecture, 0, '')
            
            words_and_exercises.sort(key=sort_key)
            
            # Write to file
            for word, lecture, exercise in words_and_exercises:
                outfile.write(f'{word};{lecture};{exercise}\n')
    
    # Read back for display
    df = pd.read_csv(output_file, delimiter=';')
    print(f"\nCreated CSV file with {len(words_and_exercises)} words and their exercises")
    print("\nFirst few entries of the created CSV:")
    print(df.head())

def main():
    # Process verbs with prepositions
    verbs_df = read_verbs_with_prepositions('b1.1/verbs_with_praposition.csv')
    display_top_verbs(verbs_df)

    # Find and display suffix patterns
    print("\nSuffix patterns found in the word list:")
    suffix_patterns = find_suffix_patterns('b1.1/words.txt')
    for suffix, count in suffix_patterns:
        print(f"{suffix}: {count} occurrences")

    # Create CSV from words.txt with sorting by exercise
    create_word_exercise_csv('b1.1/words.txt', 'b1.1/word_exercises.csv', sort_by_exercise=True)
    
    # Add reflexive verbs and verbs with prepositions to the exercises
    add_additional_verbs_to_exercises()

if __name__ == "__main__":
    main()

