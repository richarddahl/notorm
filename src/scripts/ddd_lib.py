#!/usr/bin/env python3
"""
d d d - l i b: CLI tool for DDD library scaffolding and utilities.
"""
import argparse
import shutil
import sys
from pathlib import Path

def create_context(context_name: str, output: str = None):
    """
    Scaffold a new bounded context with standard packages.
    """
    base = Path(output) if output else Path('contexts') / context_name
    if base.exists():
        print(f"Error: Context directory '{base}' already exists.")
        sys.exit(1)
    # Create base directory
    base.mkdir(parents=True)
    # Layers to scaffold
    for layer in ('domain', 'application', 'infrastructure', 'api'):
        src_dir = Path('contexts_template') / layer
        dest_dir = base / layer
        try:
            shutil.copytree(src_dir, dest_dir)
        except Exception as e:
            print(f"Error copying {layer}: {e}")
            sys.exit(1)
    print(f"Context '{context_name}' created at {base}")

def main():
    parser = argparse.ArgumentParser(prog='ddd-lib')
    sub = parser.add_subparsers(dest='command')
    # create-context command
    pc = sub.add_parser('create-context', help='Scaffold a new bounded context')
    pc.add_argument('context_name', help='Name of the context to create')
    pc.add_argument('-o', '--output', help='Output directory path')
    args = parser.parse_args()
    if args.command == 'create-context':
        create_context(args.context_name, args.output)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()