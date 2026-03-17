# test_setup.py
# Run this to verify your environment is ready

import sys
import importlib

print(f"✅ Python version: {sys.version}")

required_packages = [
    "fastapi", "uvicorn", "httpx", "dotenv",
    "openai", "pydantic", "requests", "streamlit"
]

print("\nChecking installed packages:")
all_good = True
for pkg in required_packages:
    # dotenv is imported as dotenv but installed as python-dotenv
    import_name = "dotenv" if pkg == "dotenv" else pkg
    try:
        importlib.import_module(import_name)
        print(f"  ✅ {pkg}")
    except ImportError:
        print(f"  ❌ {pkg} — NOT FOUND")
        all_good = False

if all_good:
    print("\n🎉 All packages installed correctly! Ready for Step 2.")
else:
    print("\n⚠️  Some packages are missing. Re-run: pip install fastapi uvicorn httpx python-dotenv openai pydantic requests streamlit")