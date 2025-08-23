# Tools Directory

This directory contains platform-specific tools and utilities for the AVICAST platform.

## Directory Structure

### `windows/`
Windows-specific batch files and utilities:
- `run_server.bat` - Start Django development server on Windows
- `setup.bat` - Windows environment setup script

### `linux/`
Linux/Unix-specific shell scripts:
- `setup.sh` - Linux environment setup script

## Usage

### Windows
```cmd
tools\windows\run_server.bat
tools\windows\setup.bat
```

### Linux/Unix
```bash
chmod +x tools/linux/setup.sh
./tools/linux/setup.sh
```

## Platform Compatibility

- **Windows**: Use `.bat` files in `tools/windows/`
- **Linux/Mac**: Use `.sh` files in `tools/linux/`
- **Cross-platform**: Use Python scripts in `scripts/` directory

## Note
These tools are designed to simplify common development tasks across different operating systems.
