#!/usr/bin/env python3
# PowerShell-safe script
import subprocess
import sys

print("\n" + "="*60)
print("  Installing Dependencies for Network NOC Dashboard")
print("="*60 + "\n")

packages = [
    'flask',
    'flask-cors', 
    'pandas',
    'numpy',
    'scikit-learn',
    'groq'
]

print("📦 Installing packages: " + ", ".join(packages))
print()

try:
    subprocess.check_call([
        sys.executable, '-m', 'pip', 'install',
        '--quiet'
    ] + packages)
    
    print("\n✅ All dependencies installed successfully!\n")
    print("Next steps:")
    print("  1. Generate data: python generate_data.py")
    print("  2. Start dashboard: python app.py")
    print("  3. Open: http://localhost:5000")
    print()
    
except subprocess.CalledProcessError as e:
    print(f"\n❌ Installation failed: {e}")
    sys.exit(1)
