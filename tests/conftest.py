import os
import sys

# Make the project root importable so `import cleanvey` works under pytest.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
