#!/usr/bin/env python3
"""
Quick Setup and Status Check Script
Run this to verify everything is installed and working correctly.
"""

import subprocess
import os
import sys

def check_python():
    """Check Python version"""
    version = sys.version.split()[0]
    print(f"✅ Python {version} detected")
    return True

def check_files():
    """Check if required files exist"""
    required_files = [
        'agent.py',
        'generate_data.py',
        'app.py',
        'templates/dashboard.html',
        'requirements.txt'
    ]
    
    missing = []
    for f in required_files:
        if not os.path.exists(f):
            missing.append(f)
        else:
            print(f"✅ {f} found")
    
    if missing:
        print(f"\n❌ Missing files: {', '.join(missing)}")
        return False
    return True

def check_packages():
    """Check if required Python packages are installed"""
    required = ['flask', 'pandas', 'numpy', 'scikit-learn', 'groq', 'flask-cors']
    
    print("\nChecking Python packages...")
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print(f"\nTo install, run:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True

def check_data():
    """Check if telemetry data exists"""
    if os.path.exists('telemetry_stream.csv'):
        print(f"✅ telemetry_stream.csv exists")
        return True
    else:
        print(f"⚠️  telemetry_stream.csv not found")
        print(f"   Run: python generate_data.py")
        return False

def main():
    print("=" * 60)
    print("  Network Operations Center - Setup Checker")
    print("=" * 60)
    print()
    
    all_good = True
    
    # Check Python
    check_python()
    print()
    
    # Check files
    print("Checking project files...")
    if not check_files():
        all_good = False
    print()
    
    # Check packages
    if not check_packages():
        all_good = False
    print()
    
    # Check data
    print("Checking data files...")
    data_ok = check_data()
    print()
    
    # Final status
    print("=" * 60)
    if all_good:
        print("✅ All checks passed!")
        print()
        if not data_ok:
            print("📚 Next steps:")
            print("  1. Generate telemetry data:")
            print("     python generate_data.py")
            print()
        print("  2. Start the dashboard:")
        print("     python app.py")
        print()
        print("  3. Open in browser:")
        print("     http://localhost:5000")
    else:
        print("❌ Some checks failed. Please review the errors above.")
        sys.exit(1)
    print()

if __name__ == '__main__':
    main()
