import os
import re
import sys
import glob

patches_folder_path = os.path.abspath('./patches/')
patches_glob_path = './patches/*.pnach'

def remove_comments(line):
    return line[0:line.index('//')] if ("//" in line) else line

def clean_line(line):
    return remove_comments(line).strip()

def log_error(file_path, line_number, message, line, shouldCleanLine = False):
    line = line.replace("\n", "")
    line = (clean_line(line) if shouldCleanLine else line)
    print(f'Error in {file_path} (line {line_number}): {message}\n\t"{line}"')

def is_file_valid(file_path):
    with open(file_path, 'r') as file:
        for line_number, line in enumerate(file, 1):
            cleaned_line = clean_line(line)
            if cleaned_line == "":
                continue
            elif cleaned_line.startswith("["):
                if not cleaned_line.endswith("]"):
                    print(f'Error in {file_path} group format (line {line_number}): Unclosed brackets for group.\n\T"{line}"')
                    return False
                continue
            elif re.match(r'^(\s*(gametitle|comment|gsaspectratio|gsinterlacemode|author|description)\s*=)', line, re.IGNORECASE):
                # Incorrect case will cause the line to be ignored by the emulator.
                # Conditional is case insensitive to catch any case issues and compare to lower.
                line_keyword = cleaned_line.split('=')[0]
                if line_keyword != line_keyword.lower():
                    log_error(file_path, line_number, "Invalid keyword format.", line)
                    return False
                # We can do more validations here, but for now skip these so they don't appear as unknown syntax error.
                continue
            elif cleaned_line.startswith("patch"):
                if not re.match(r'^patch=(0|1|2),(EE|IOP),[0-9A-Fa-f]{1,8},(byte|short|word|double|extended|beshort|beword|bedouble|bytes),[0-9A-Fa-f]{1,8}', line):
                    log_error(file_path, line_number, "Invalid patch format.", line, True)
                    return False
                if re.match(",\d{8}(\n|\s*(//.*)*)+(?!.)", line):
                    log_error(file_path, line_number, "Invalid comment syntax at end of patch line.", line, False)
                    return False
            else:
                log_error(file_path, line_number, "Unknown line format.", line, True)
                return False
            
    return True

def main():
    error_found = False
    print('Started validating patches files')

    files = glob.glob(patches_glob_path)
    file_count = len(files)
    print(f'Validating {file_count} patch files:')
    if file_count > 0:
        for file_path in files:
            if not is_file_valid(file_path):
                error_found = True
    else:
        print(f'[Error]: No patch files found to validate in \'{patches_folder_path}\'')
        error_found = True

    if error_found:
        print('[Failed]: Patch validation issues were detected. Ending checks.')
        sys.exit(1)

    print('[Success]: All patch files passed the validation checks.')
    sys.exit(0)

if __name__ == '__main__':
    main()