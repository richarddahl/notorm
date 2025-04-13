#!/usr/bin/env python
"""
Uno Framework Benchmark Dashboard - Simple Launcher

This script provides a simplified, direct way to run the benchmark dashboard
without relying on shell scripts. It handles dependency checking and runs
the dashboard application.
"""
import os
import sys
import subprocess
import importlib.util
from pathlib import Path


def check_dependency(package_name):
    """Check if a Python package is installed"""
    return importlib.util.find_spec(package_name) is not None


def install_dependencies():
    """Install required packages for the dashboard"""
    required_packages = ['dash', 'plotly', 'pandas', 'numpy']
    missing_packages = [pkg for pkg in required_packages if not check_dependency(pkg)]
    
    if missing_packages:
        print(f"Installing missing dependencies: {', '.join(missing_packages)}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
        print("Dependency installation complete!")
    else:
        print("All required dependencies are already installed.")


def prepare_directories():
    """Ensure necessary directories exist"""
    # Create data and assets directories
    os.makedirs('data/summaries', exist_ok=True)
    os.makedirs('assets', exist_ok=True)
    
    # Check if the sample benchmark file exists, create it if needed
    sample_file = Path('data/sample_benchmark.json')
    if not sample_file.exists():
        print("Creating sample benchmark file...")
        subprocess.check_call([sys.executable, 'app.py'])


def run_dashboard():
    """Process benchmark data and run the dashboard"""
    # Process benchmark results
    print("Processing benchmark results...")
    subprocess.check_call([sys.executable, 'process_results.py', '--sample'])
    
    # Run the dashboard
    print("\nStarting Uno Framework Benchmark Dashboard at http://127.0.0.1:8050/")
    print("Press Ctrl+C to stop the dashboard\n")
    subprocess.check_call([sys.executable, 'app.py'])


if __name__ == "__main__":
    # Change to the script's directory
    os.chdir(Path(__file__).parent)
    
    print("=== Uno Framework Benchmark Dashboard ===\n")
    
    try:
        # Ensure dependencies are installed
        install_dependencies()
        
        # Prepare necessary directories
        prepare_directories()
        
        # Run the dashboard
        run_dashboard()
        
    except KeyboardInterrupt:
        print("\nDashboard stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError running dashboard: {e}")
        sys.exit(1)