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

def remove_newlines(line):
    return line.replace('\r', '').replace('\n', '')

def log_error(file_path, line_number, message, line, shouldCleanLine = False):
    line = remove_newlines(line)
    line = (clean_line(line) if shouldCleanLine else line)
    print(f'Error in {file_path} (line {line_number}): {message}\n\t"{line}"')

def is_file_valid(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        for line_number, line in enumerate(file, 1):
            if remove_newlines(line) != line.strip():
                log_error(file_path, line_number, "Excess whitespace.", line)
                return False
            cleaned_line = clean_line(line)
            if not cleaned_line:
                continue
            elif cleaned_line.startswith("["):
                if not cleaned_line.endswith("]"):
                    print(f'Error in {file_path} group format (line {line_number}): Unclosed brackets for group.\n\t"{line}"')
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
                if re.match(r",\d{8}(\n|\s*(//.*)*)+(?!.)", line):
                    log_error(file_path, line_number, "Invalid comment syntax at end of patch line.", line, False)
                    return False
            elif cleaned_line.startswith("dpatch"):
                match = re.match(r"^dpatch=(\d+),(\d+),(\d+)((?:,[\dA-Fa-f]+)+)", line)
                if not match:
                    log_error(file_path, line_number, "Invalid dpatch format.", line, True)
                    return False
                num_tuples = int(match.group(2)) + int(match.group(3))
                dat_str = match.group(4).strip(',').split(',')
                if len(dat_str) != num_tuples * 2:
                    log_error(file_path, line_number, "Invalid dpatch format.", line, True)
                    return False
                for i in range(0, num_tuples, 2):
                    # Offsets must be hex
                    if not re.match(r'^[0-9A-Fa-f]+$', dat_str[i]) or not re.match(r'^[0-9A-Fa-f]+$', dat_str[i+1]):
                        log_error(file_path, line_number, "Invalid dpatch format.", line, True)
                        return False
                    # Offsets must be 4 byte aligned
                    if int(dat_str[i], 16) % 4 != 0:
                        log_error(file_path, line_number, "Invalid dpatch offset alignment (must be 4 byte aligned).", line, True)
                        return False
            else:
                log_error(file_path, line_number, "Unknown line format.", line, True)
                return False

    return True

def main():
    error_found = False
    print('Started validating patch files')

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
