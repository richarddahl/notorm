"""
Simple script to verify Python package installation
"""

def check_dependencies():
    """Check if all required dependencies are installed correctly"""
    dependencies = {
        "dash": "Dashboard framework",
        "plotly": "Interactive plotting library",
        "pandas": "Data analysis library",
        "numpy": "Numerical computing library"
    }
    
    missing = []
    installed = []
    
    for package, description in dependencies.items():
        try:
            module = __import__(package)
            version = getattr(module, "__version__", "unknown")
            installed.append(f"{package} (v{version})")
        except ImportError:
            missing.append(f"{package} - {description}")
    
    print("===== Dependency Check =====")
    
    if installed:
        print("\nSuccessfully installed:")
        for pkg in installed:
            print(f"  ✓ {pkg}")
    
    if missing:
        print("\nMissing dependencies:")
        for pkg in missing:
            print(f"  ✗ {pkg}")
        print("\nRun 'pip install -r requirements.txt' to install missing dependencies")
    else:
        print("\nAll required dependencies are installed! 🎉")

if __name__ == "__main__":
    check_dependencies()