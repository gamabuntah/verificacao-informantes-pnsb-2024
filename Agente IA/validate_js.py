#!/usr/bin/env python3
import re
import sys

def validate_javascript_syntax(filename):
    """Validate JavaScript syntax in HTML file"""
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract all JavaScript content from script tags
    script_pattern = r'<script[^>]*>(.*?)</script>'
    scripts = re.findall(script_pattern, content, re.DOTALL)
    
    print(f"Found {len(scripts)} script blocks")
    
    for i, script in enumerate(scripts):
        print(f"\n=== Script Block {i+1} ===")
        lines = script.split('\n')
        
        # Check for common syntax errors
        brace_count = 0
        paren_count = 0
        bracket_count = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip comments
            if line.startswith('//') or line.startswith('/*') or line.startswith('*'):
                continue
            
            # Count braces, parentheses, brackets
            brace_count += line.count('{') - line.count('}')
            paren_count += line.count('(') - line.count(')')
            bracket_count += line.count('[') - line.count(']')
            
            # Check for return statements outside functions
            if 'return' in line and not line.startswith('//'):
                # Simple heuristic: if we're not inside a function, it's likely an error
                before_lines = lines[:line_num-1]
                function_count = 0
                for prev_line in before_lines:
                    if 'function' in prev_line or '=>' in prev_line:
                        function_count += prev_line.count('{')
                    function_count -= prev_line.count('}')
                
                if function_count <= 0:
                    print(f"  WARNING: Potential orphaned return at line {line_num}: {line}")
        
        print(f"  Final counts - Braces: {brace_count}, Parens: {paren_count}, Brackets: {bracket_count}")
        
        if brace_count != 0:
            print(f"  ERROR: Unmatched braces in script block {i+1}")
        if paren_count != 0:
            print(f"  ERROR: Unmatched parentheses in script block {i+1}")
        if bracket_count != 0:
            print(f"  ERROR: Unmatched brackets in script block {i+1}")

if __name__ == "__main__":
    validate_javascript_syntax('gestao_visitas/templates/mapa_progresso.html')