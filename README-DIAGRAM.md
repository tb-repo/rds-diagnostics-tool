# Architecture Diagram Generation Guide

## Quick Start

To generate the RDS Diagnostics Tool architecture diagram, you need Graphviz installed.

### Step 1: Install Graphviz

#### Windows (Recommended Methods)

**Option A: Using Chocolatey (Easiest)**
```bash
choco install graphviz
```

**Option B: Direct Download**
1. Download from: https://graphviz.org/download/
2. Run the installer
3. During installation, check "Add Graphviz to system PATH"
4. Or manually add to PATH: `C:\Program Files\Graphviz\bin`

**Option C: Using Winget**
```bash
winget install graphviz
```

#### Verify Installation
```bash
dot -V
```
You should see output like: `dot - graphviz version X.X.X`

### Step 2: Generate the Diagram

Once Graphviz is installed, run:

```bash
# Using the batch script
generate-diagram.bat

# Or directly with Python
python generate_architecture_diagram.py

# Or manually with Graphviz
dot -Tpng architecture-diagram.dot -o architecture-diagram.png
```

## Output Files

The generation creates:
- **architecture_diagram.png** - Main architecture diagram with AWS icons

## Troubleshooting

### Error: "failed to execute WindowsPath('dot')"
- Graphviz is not installed or not in PATH
- Solution: Install Graphviz and restart your terminal/IDE

### Error: "The system cannot find the file specified"
- Graphviz bin directory is not in system PATH
- Solution: Add `C:\Program Files\Graphviz\bin` to your PATH environment variable

### Verify Graphviz Installation
```bash
where dot
```
Should return the path to dot.exe

## Alternative: Online Diagram Generation

If you can't install Graphviz locally, you can use online tools:

1. Copy the contents of `architecture-diagram.dot`
2. Visit: https://dreampuf.github.io/GraphvizOnline/
3. Paste the DOT code
4. Download the generated PNG

## Diagram Features

The generated diagram shows:
- Complete system architecture from user to AWS services
- Data flow between components
- Color-coded layers and connections
- Professional AWS service icons
- Clear clustering of related components

## Files in This Project

- `generate_architecture_diagram.py` - Python script using diagrams library
- `generate-diagram.bat` - Windows batch script wrapper
- `architecture-diagram.dot` - Graphviz DOT source (manual option)
- `.kiro/steering/diagram.md` - Architecture documentation
