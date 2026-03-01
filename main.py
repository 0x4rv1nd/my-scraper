import subprocess
import sys
import os
from datetime import datetime

# ---------- SETTINGS ----------
STEPS = [
    ("STEP 1: Collect phone URLs", "urls.py"),
    ("STEP 2: Clean URLs", "urlcleaner.py"),
    ("STEP 3: Download HTML pages + Spec Score", "mpd1.py"),
    ("STEP 4: Parse HTML → Final Dataset", "hparser.py"),
]

# ---------- UTIL ----------
def run_script(step_name, script_file):

    print("\n" + "="*70)
    print(step_name)
    print("="*70)

    if not os.path.exists(script_file):
        print(f"❌ ERROR: {script_file} not found!")
        sys.exit(1)

    start = datetime.now()

    try:
        result = subprocess.run(
            [sys.executable, script_file],
            check=True
        )
    except subprocess.CalledProcessError:
        print(f"\n❌ Pipeline stopped at: {script_file}")
        sys.exit(1)

    end = datetime.now()
    print(f"\n✅ Completed {script_file}  |  Time: {end-start}")


# ---------- PREPARE FOLDERS ----------
def prepare_environment():

    print("Preparing environment...")

    if not os.path.exists("pages_browser"):
        os.makedirs("pages_browser")

    print("Environment ready.\n")


# ---------- MAIN PIPELINE ----------
def main():

    print("\n📱 91Mobiles Automatic Dataset Builder")
    print("Starting full scraping pipeline...\n")

    prepare_environment()

    for step_name, script in STEPS:
        run_script(step_name, script)

    print("\n" + "="*70)
    print("🎉 DATASET BUILD COMPLETE!")
    print("Your file is ready: final_dataset.json")
    print("="*70)


if __name__ == "__main__":
    main()