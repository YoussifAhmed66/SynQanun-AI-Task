import os
import sys
# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import docx2txt
from config.settings import Settings


def check_file(path, label):
    # print(f"\n--- {label} ({os.path.basename(path)}) ---")
    try:
        text = docx2txt.process(path)

        return text
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return ""


# check_file(Settings.fatwas + "/fatwa1_1960.docx", "FATWAS")