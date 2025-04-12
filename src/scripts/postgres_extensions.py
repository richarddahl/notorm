"""
PostgreSQL extension installation and management utilities.

This module provides tools for:
- Installing PostgreSQL extensions like AGE, pgvector, pgjwt
- Configuring extensions in a PostgreSQL database
- Managing extension lifecycle
"""

import os
import sys
import tempfile
import shutil
import subprocess
import argparse
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple


class ExtensionManagerError(Exception):
    """Base exception for extension manager errors."""
    pass


def run_command(
    command: Union[str, List[str]], 
    check: bool = True,
    shell: bool = True,
    capture_output: bool = False,
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[str] = None
) -> subprocess.CompletedProcess:
    """
    Run a shell command and handle errors.
    
    Args:
        command: Command to run (string or list of arguments)
        check: Whether to raise an exception on non-zero exit code
        shell: Whether to run the command through the shell
        capture_output: Whether to capture stdout and stderr
        env: Optional environment variables to set
        cwd: Optional working directory
        
    Returns:
        CompletedProcess instance with command results
        
    Raises:
        ExtensionManagerError: If command fails and check is True
    """
    try:
        current_env = os.environ.copy()
        if env:
            current_env.update(env)
            
        result = subprocess.run(
            command,
            shell=shell,
            check=False,  # We'll handle this ourselves
            capture_output=capture_output,
            text=True,
            env=current_env,
            cwd=cwd
        )
        
        if check and result.returncode != 0:
            error_message = f"Command failed with exit code {result.returncode}:\n{command}"
            if capture_output and result.stderr:
                error_message += f"\nError output:\n{result.stderr}"
            raise ExtensionManagerError(error_message)
            
        return result
    except Exception as e:
        if not isinstance(e, ExtensionManagerError):
            raise ExtensionManagerError(f"Error running command: {e}")
        raise


def install_system_dependencies(sudo_required: bool = True) -> None:
    """
    Install system dependencies required for building PostgreSQL extensions.
    
    Args:
        sudo_required: Whether sudo is required for installation
        
    Raises:
        ExtensionManagerError: If dependency installation fails
    """
    system = platform.system().lower()
    
    if system == "linux":
        # Detect distribution
        if os.path.exists("/etc/debian_version"):
            # Debian/Ubuntu
            cmd_prefix = "sudo " if sudo_required else ""
            cmd = f"{cmd_prefix}apt-get update && {cmd_prefix}apt-get install -y "
            dependencies = [
                "git", 
                "build-essential", 
                "postgresql-server-dev-16", 
                "cmake", 
                "flex", 
                "bison", 
                "curl", 
                "unzip", 
                "libcurl4-openssl-dev"
            ]
            run_command(f"{cmd} {' '.join(dependencies)}")
            print("Installed system dependencies")
        elif os.path.exists("/etc/redhat-release"):
            # RHEL/CentOS/Fedora
            cmd_prefix = "sudo " if sudo_required else ""
            cmd = f"{cmd_prefix}yum install -y "
            dependencies = [
                "git", 
                "gcc", 
                "gcc-c++", 
                "make", 
                "postgresql-devel", 
                "cmake", 
                "flex", 
                "bison", 
                "curl", 
                "unzip", 
                "libcurl-devel"
            ]
            run_command(f"{cmd} {' '.join(dependencies)}")
            print("Installed system dependencies")
        else:
            print("Unknown Linux distribution, skipping system dependency installation")
            print("You may need to install dependencies manually")
    elif system == "darwin":
        # macOS
        try:
            # Check if brew is installed
            run_command("which brew", capture_output=True)
            
            # Install dependencies with Homebrew
            dependencies = [
                "postgresql@16", 
                "cmake", 
                "flex", 
                "bison", 
                "curl"
            ]
            run_command(f"brew install {' '.join(dependencies)}")
            print("Installed system dependencies with Homebrew")
        except ExtensionManagerError:
            print("Homebrew not found, skipping system dependency installation")
            print("You may need to install dependencies manually")
    else:
        print(f"Unsupported system: {system}, skipping system dependency installation")
        print("You may need to install dependencies manually")


def download_and_build_age(build_dir: str, sudo_required: bool = True) -> None:
    """
    Download and build the AGE (Apache Graph Extension) extension.
    
    Args:
        build_dir: Directory to build in
        sudo_required: Whether sudo is required for installation
        
    Raises:
        ExtensionManagerError: If build fails
    """
    print("Building AGE (Apache Graph Extension)...")
    
    # Download AGE
    run_command("curl -L -o age.zip https://github.com/apache/age/archive/refs/heads/master.zip", cwd=build_dir)
    run_command("unzip age.zip", cwd=build_dir)
    
    # Build and install
    age_dir = os.path.join(build_dir, "age-master")
    
    install_cmd = "make install"
    if sudo_required and platform.system().lower() != "windows":
        install_cmd = f"sudo {install_cmd}"
    
    run_command("make", cwd=age_dir)
    run_command(install_cmd, cwd=age_dir)
    
    print("AGE extension built and installed successfully")


def download_and_build_pgjwt(build_dir: str, sudo_required: bool = True) -> None:
    """
    Download and build the pgjwt extension.
    
    Args:
        build_dir: Directory to build in
        sudo_required: Whether sudo is required for installation
        
    Raises:
        ExtensionManagerError: If build fails
    """
    print("Building pgjwt extension...")
    
    # Download pgjwt
    run_command("curl -L -o pgjwt.zip https://github.com/michelp/pgjwt/archive/refs/heads/master.zip", cwd=build_dir)
    run_command("unzip pgjwt.zip", cwd=build_dir)
    
    # Build and install
    pgjwt_dir = os.path.join(build_dir, "pgjwt-master")
    
    install_cmd = "make install"
    if sudo_required and platform.system().lower() != "windows":
        install_cmd = f"sudo {install_cmd}"
    
    run_command("make", cwd=pgjwt_dir)
    run_command(install_cmd, cwd=pgjwt_dir)
    
    print("pgjwt extension built and installed successfully")


def download_and_build_supa_audit(build_dir: str, sudo_required: bool = True) -> None:
    """
    Download and build the supa_audit extension.
    
    Args:
        build_dir: Directory to build in
        sudo_required: Whether sudo is required for installation
        
    Raises:
        ExtensionManagerError: If build fails
    """
    print("Building supa_audit extension...")
    
    # Download supa_audit
    run_command("curl -L -o supa_audit.zip https://github.com/supabase/supa_audit/archive/refs/heads/main.zip", cwd=build_dir)
    run_command("unzip supa_audit.zip", cwd=build_dir)
    
    # Build and install
    supa_audit_dir = os.path.join(build_dir, "supa_audit-main")
    
    install_cmd = "make install"
    if sudo_required and platform.system().lower() != "windows":
        install_cmd = f"sudo {install_cmd}"
    
    run_command("make", cwd=supa_audit_dir)
    run_command(install_cmd, cwd=supa_audit_dir)
    
    print("supa_audit extension built and installed successfully")


def setup_plugins_directory(sudo_required: bool = True) -> None:
    """
    Set up the PostgreSQL plugins directory and create symlinks.
    
    Args:
        sudo_required: Whether sudo is required for directory operations
        
    Raises:
        ExtensionManagerError: If directory operations fail
    """
    plugins_dir = "/usr/local/lib/postgresql/plugins"
    
    # Create plugins directory
    mkdir_cmd = f"mkdir -p {plugins_dir}"
    if sudo_required and platform.system().lower() != "windows":
        mkdir_cmd = f"sudo {mkdir_cmd}"
    
    run_command(mkdir_cmd)
    
    # Create symlink for AGE
    ln_cmd = f"ln -sf /usr/local/lib/postgresql/age.so {plugins_dir}/age.so"
    if sudo_required and platform.system().lower() != "windows":
        ln_cmd = f"sudo {ln_cmd}"
    
    run_command(ln_cmd)
    
    print(f"Created plugins directory and symlinks: {plugins_dir}")


def install_extensions(sudo_required: bool = True) -> bool:
    """
    Install all PostgreSQL extensions.
    
    Args:
        sudo_required: Whether sudo is required for operations
        
    Returns:
        True if successful, False otherwise
    """
    try:
        print("===== Installing PostgreSQL Extensions =====")
        
        # Create temporary build directory
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Using temporary build directory: {temp_dir}")
            
            # Install system dependencies
            install_system_dependencies(sudo_required)
            
            # Build and install extensions
            download_and_build_age(temp_dir, sudo_required)
            download_and_build_pgjwt(temp_dir, sudo_required)
            download_and_build_supa_audit(temp_dir, sudo_required)
            
            # Set up plugins directory
            setup_plugins_directory(sudo_required)
            
            print("\n===== PostgreSQL Extensions Installation Complete =====")
            print("The following extensions were installed:")
            print("- AGE (Apache Graph Extension)")
            print("- pgjwt")
            print("- supa_audit")
            print("\nTo enable these in your database, run:")
            print("CREATE EXTENSION IF NOT EXISTS age;")
            print("CREATE EXTENSION IF NOT EXISTS pgjwt;")
            print("CREATE EXTENSION IF NOT EXISTS supa_audit;")
            
            return True
    except ExtensionManagerError as e:
        print(f"\n===== PostgreSQL Extensions Installation Failed =====")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"\n===== PostgreSQL Extensions Installation Failed =====")
        print(f"Unexpected error: {e}")
        return False


def main() -> int:
    """
    Main entry point for PostgreSQL extensions management.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="PostgreSQL extension management tools")
    parser.add_argument(
        "--no-sudo", 
        action="store_true", 
        help="Don't use sudo for operations (for containerized environments)"
    )
    
    args = parser.parse_args()
    
    success = install_extensions(sudo_required=not args.no_sudo)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())