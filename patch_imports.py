import os
import glob

sports_dir = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\sports_model"
for py_file in glob.glob(os.path.join(sports_dir, "*.py")):
    with open(py_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    original = content
    # Add sys.path if not there
    if "import sys" not in content and "core" in content:
        # Just simple replacement for devig
        pass
        
    content = content.replace("from devig import", "import sys\nimport os\nsys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\nfrom core.devig import")
    
    # Fix acca_tracker.json path references
    content = content.replace('"acca_tracker.json"', 'os.path.join(os.path.dirname(__file__), "acca_tracker.json")')
    content = content.replace("'acca_tracker.json'", "os.path.join(os.path.dirname(__file__), 'acca_tracker.json')")
    
    # Fix odds_cache.json path references
    content = content.replace('"odds_cache.json"', 'os.path.join(os.path.dirname(__file__), "odds_cache.json")')
    content = content.replace("'odds_cache.json'", "os.path.join(os.path.dirname(__file__), 'odds_cache.json')")
    
    if original != content:
        with open(py_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Patched {py_file}")
