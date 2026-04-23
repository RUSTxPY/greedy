#!/usr/bin/env python3
"""Build native shared library for current platform."""

import subprocess
import sys
import platform
from pathlib import Path


def get_rust_target() -> str:
    """Get Rust target triple for current platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    targets = {
        ('linux', 'x86_64'): 'x86_64-unknown-linux-gnu',
        ('linux', 'amd64'): 'x86_64-unknown-linux-gnu',
        ('linux', 'aarch64'): 'aarch64-unknown-linux-gnu',
        ('linux', 'arm64'): 'aarch64-unknown-linux-gnu',
        ('darwin', 'x86_64'): 'x86_64-apple-darwin',
        ('darwin', 'amd64'): 'x86_64-apple-darwin',
        ('darwin', 'arm64'): 'aarch64-apple-darwin',
    }
    
    target = targets.get((system, machine))
    if not target:
        print(f"Unsupported platform: {system} {machine}")
        sys.exit(1)
    
    return target


def build_native():
    """Build Rust shared library."""
    native_dir = Path(__file__).parent
    
    # Check for Rust
    result = subprocess.run(['cargo', '--version'], capture_output=True)
    if result.returncode != 0:
        print("Error: Rust/Cargo not found. Install from https://rustup.rs/")
        sys.exit(1)
    
    target = get_rust_target()
    print(f"Building for target: {target}")
    
    # Add target if needed
    subprocess.run(['rustup', 'target', 'add', target], check=False)
    
    # Build release version
    result = subprocess.run(
        ['cargo', 'build', '--release', '--target', target],
        cwd=native_dir,
    )
    
    if result.returncode != 0:
        print("Build failed!")
        sys.exit(1)
    
    # Determine library name
    system = platform.system().lower()
    if system == 'linux':
        lib_name = 'libddgs_native.so'
    elif system == 'darwin':
        lib_name = 'libddgs_native.dylib'
    else:
        lib_name = 'ddgs_native.dll'
    
    src = native_dir / 'target' / target / 'release' / lib_name
    
    if not src.exists():
        # Try non-target path (if building for host)
        src = native_dir / 'target' / 'release' / lib_name
    
    if src.exists():
        print(f"Built: {src}")
        
        # Copy to package data
        data_dir = native_dir.parent / 'ddgs' / 'data'
        data_dir.mkdir(exist_ok=True)
        
        import shutil
        dst = data_dir / lib_name
        shutil.copy2(src, dst)
        print(f"Copied to: {dst}")
    else:
        print(f"Error: Library not found at {src}")
        sys.exit(1)


if __name__ == '__main__':
    build_native()
