#!/usr/bin/env python3
"""
Generate HTML from markdown genetic profile document
"""

import markdown
import re
from pathlib import Path

def convert_citations(text):
    """Convert markdown citations [1,2,3] or [21-42] to HTML with expandable format: [1] for single, [1+] for multiple"""
    def expand_citation_range(citation_str):
        """Expand citation ranges like '21-42' or '5-12,43-53' to list of numbers"""
        numbers = []
        parts = [p.strip() for p in citation_str.split(',')]
        for part in parts:
            if '-' in part:
                # Handle range like '21-42'
                start, end = part.split('-')
                start_num, end_num = int(start.strip()), int(end.strip())
                numbers.extend(range(start_num, end_num + 1))
            else:
                # Handle single number
                numbers.append(int(part.strip()))
        return sorted(set(numbers))  # Remove duplicates and sort
    
    def replace_citation(match):
        citation_str = match.group(1)
        citation_nums = expand_citation_range(citation_str)
        
        if len(citation_nums) == 1:
            # Single citation: [1]
            num = citation_nums[0]
            return f'<sup class="citation"><a href="#ref-{num}" class="cite-link"><span class="cite-num">[{num}]</span></a></sup>'
        else:
            # Multiple citations: [1+] with expandable content
            first_num = citation_nums[0]
            all_nums_str = ','.join(map(str, citation_nums))
            # Create expanded content (hidden by default)
            expanded_links = ','.join([f'<a href="#ref-{num}" class="cite-link"><span class="cite-num">{num}</span></a>' for num in citation_nums])
            return (f'<sup class="citation expandable" data-citations="{all_nums_str}">'
                    f'<span class="cite-compact"><a href="#ref-{first_num}" class="cite-link"><span class="cite-num">[{first_num}+]</span></a></span>'
                    f'<span class="cite-expanded" style="display:none;">{expanded_links}</span>'
                    f'</sup>')
    
    # Pattern matches: [1], [1,2,3], [21-42], [5-12,43-53], [43,63-70], etc.
    pattern = r'\[(\d+(?:-\d+)?(?:\s*,\s*\d+(?:-\d+)?)*)\]'
    return re.sub(pattern, replace_citation, text)

def add_reference_anchors(html_content):
    """Add anchor IDs to reference list items for direct linking"""
    def replace_li(match):
        li_content = match.group(1)
        # Extract the citation number from the start of the list item
        num_match = re.match(r'(\d+)\.', li_content.strip())
        if num_match:
            citation_number = num_match.group(1)
            return f'<li id="ref-{citation_number}">{li_content}</li>'
        return f'<li>{li_content}</li>'
    
    # Apply the replacement to all list items within the HTML content
    return re.sub(r'<li[^>]*>(.*?)</li>', replace_li, html_content, flags=re.DOTALL)

def generate_html(markdown_file, output_file='output/genetic_profile.html'):
    """Generate HTML from markdown file"""
    markdown_path = Path(markdown_file)
    output_path = Path(output_file)
    
    if not markdown_path.exists():
        print(f"❌ Markdown file not found: {markdown_path}")
        return False
    
    with open(markdown_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Convert citations to clickable links
    content = convert_citations(content)
    
    # Convert markdown to HTML
    html_content = markdown.markdown(content, extensions=['extra', 'toc'])
    
    # Add reference anchors
    html_content = add_reference_anchors(html_content)
    
    # Create HTML template - uses external CSS for consistency
    # Note: When served through web app, body content is extracted and wrapped in templates
    # This standalone version includes CSS link for direct file viewing
    html_template = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Genetic Profile - Non-Pharmacogenomic</title>
    <link rel="stylesheet" href="../static/css/dist/health-ledger.css">
    <script>
        // Citation expand/collapse functionality
        document.addEventListener('DOMContentLoaded', function() {{
            document.querySelectorAll('.citation.expandable .cite-compact').forEach(function(compact) {{
                compact.style.cursor = 'pointer';
                compact.addEventListener('click', function(e) {{
                    e.preventDefault();
                    var citation = this.closest('.citation');
                    var expanded = citation.querySelector('.cite-expanded');
                    var compact = citation.querySelector('.cite-compact');
                    
                    if (expanded.style.display === 'none') {{
                        expanded.style.display = 'inline';
                        compact.style.display = 'none';
                    }} else {{
                        expanded.style.display = 'none';
                        compact.style.display = 'inline';
                    }}
                }});
            }});
        }});
    </script>
</head>
<body>
<div class="profile-content">
{content}
</div>
</body>
</html>'''
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template.format(content=html_content))
    
    print(f"✅ HTML generated: {output_path}")
    return True

if __name__ == '__main__':
    import sys
    import os
    # Get script directory and project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # The profile markdown lives with the person's data, outside the repo.
    sys.path.insert(0, str(project_root))
    from config import OUTPUT_DIR
    default_output = OUTPUT_DIR / 'genetic_profile.html'
    
    if len(sys.argv) < 2:
        print("Usage: generate_html.py <profile.md> [output.html]")
        sys.exit(1)
    markdown_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else str(default_output)
    
    generate_html(markdown_file, output_file)
