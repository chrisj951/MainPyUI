import re
import sys

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <filename>")
    sys.exit(1)

filename = sys.argv[1]

try:
    with open(filename, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f]
except FileNotFoundError:
    print(f"File not found: {filename}")
    sys.exit(1)

conversion_map = {}

i = 0
while i < len(lines):
    line = lines[i]

    # Check for NEW_CORE
    core_match = re.match(r'NEW_CORE="(.+?)"', line)
    if core_match:
        core_value = core_match.group(1)

        # Read the next line for NEW_DISPLAY, skipping blank lines
        i += 1
        while i < len(lines) and not lines[i]:
            i += 1

        if i < len(lines):
            display_line = lines[i]
            display_match = re.match(r'NEW_DISPLAY="(.+?)"', display_line)
            if display_match:
                display_value = display_match.group(1)

                # Extract the string inside parentheses starting with ✓
                extracted_disp_match = re.search(r'\(✓(.*?)\)', display_value)
                extracted_disp_value = extracted_disp_match.group(1) if extracted_disp_match else ""

                # Add to conversion map
                conversion_map[extracted_disp_value] = core_value
    i += 1

print("conversion_map = {")
for k, v in conversion_map.items():
    print(f'    "{k}": "{v}",')
print("}")
