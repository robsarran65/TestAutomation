import os
import shutil

# ---------------------------------------------------------
# Helper: Safe move (only if file exists)
# ---------------------------------------------------------
def safe_move(src, dest):
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.move(src, dest)
        print(f"Moved: {src} → {dest}")
    else:
        print(f"Skipped (not found): {src}")

# ---------------------------------------------------------
# Create clean folder structure
# ---------------------------------------------------------
def create_structure():
    folders = [
        "framework",
        "tests/ui",
        "tests/api",
        "tests/suites/smoke",
        "tests/suites/regression",
        "data",
        "reports",
        "logs/screenshots"
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"Ensured folder: {folder}")

# ---------------------------------------------------------
# Move framework files
# ---------------------------------------------------------
def move_framework_files():
    safe_move("keyword_engine.py", "framework/keyword_engine.py")
    safe_move("ai_engine.py", "framework/ai_engine.py")
    safe_move("test_runner.py", "framework/test_runner.py")
    safe_move("utils.py", "framework/utils.py")  # optional if exists

# ---------------------------------------------------------
# Move test files
# ---------------------------------------------------------
def move_test_files():
    test_files = [
        "login_test.xlsx",
        "login_data_driven.xlsx",
        "weather_orlando.xlsx",
    ]
    for f in test_files:
        if "weather" in f.lower():
            safe_move(f, f"tests/api/{f}")
        else:
            safe_move(f, f"tests/ui/{f}")

# ---------------------------------------------------------
# Move data files
# ---------------------------------------------------------
def move_data_files():
    data_files = [
        "generated_data.xlsx",
        "sample_users.xlsx",
    ]
    for f in data_files:
        safe_move(f, f"data/{f}")

# ---------------------------------------------------------
# Move logs and reports
# ---------------------------------------------------------
def move_logs_and_reports():
    if os.path.exists("logs"):
        shutil.move("logs", "logs_old")
        print("Moved old logs → logs_old")

    os.makedirs("logs/screenshots", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    print("\n=== Creating Clean Folder Structure ===")
    create_structure()

    print("\n=== Moving Framework Files ===")
    move_framework_files()

    print("\n=== Moving Test Files ===")
    move_test_files()

    print("\n=== Moving Data Files ===")
    move_data_files()

    print("\n=== Preparing Logs & Reports Folders ===")
    move_logs_and_reports()

    print("\nMigration complete. Your project is now organized cleanly.\n")
