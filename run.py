import sys
import subprocess

# Available versions
versions = ['1', '2', '3', '4', '5']

# Get version from command line argument, default to '5'
if len(sys.argv) > 1:
    version = sys.argv[1]
else:
    version = '5'

# Validate version
if version not in versions:
    print(f"Invalid version '{version}'. Available versions: {', '.join(versions)}")
    sys.exit(1)

# Run the corresponding verX.py script
script_name = f'ver{version}.py'
try:
    subprocess.call(['python', script_name])
except FileNotFoundError:
    print(f"Script '{script_name}' not found.")
    sys.exit(1)
except Exception as e:
    print(f"Error running '{script_name}': {e}")
    sys.exit(1)
