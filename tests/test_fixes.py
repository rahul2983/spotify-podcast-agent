# Quick fixes for test files
import pytest

# Make MCP_AVAILABLE globally available
MCP_API_AVAILABLE = getattr(pytest, 'MCP_AVAILABLE', False)

def patch_test_file(filename):
    """Add MCP_API_AVAILABLE to a test file."""
    with open(filename, 'r') as f:
        content = f.read()
    
    if 'MCP_API_AVAILABLE' not in content:
        # Add import at the top
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('import') or line.startswith('from'):
                continue
            else:
                lines.insert(i, 'import pytest')
                lines.insert(i+1, 'MCP_API_AVAILABLE = getattr(pytest, "MCP_AVAILABLE", False)')
                break
        
        with open(filename, 'w') as f:
            f.write('\n'.join(lines))