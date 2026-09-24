#!/usr/bin/env python3
"""Convert Markdown report to PDF using WeasyPrint"""

import markdown
from weasyprint import HTML, CSS
from pathlib import Path

# Read the Markdown file
md_path = Path("/home/yesf37332/Desktop/jy-wealth-investment-analysis/reports/中邮理财鸿锦一年定开 88 号分析报告_2026-04-02.md")
md_content = md_path.read_text(encoding='utf-8')

# Convert Markdown to HTML
html_body = markdown.markdown(md_content, extensions=['tables', 'toc'])

# Create full HTML document with CJK font support
html_doc = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>中邮理财鸿锦一年定开 88 号分析报告</title>
  <style>
    @page {{
      size: A4;
      margin: 2cm;
      @bottom-right {{
        content: "Page " counter(page) " of " counter(pages);
        font-size: 9pt;
        color: #666;
      }}
    }}
    
    body {{
      font-family: 'Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'Microsoft YaHei', 'PingFang SC', sans-serif;
      font-size: 11pt;
      line-height: 1.6;
      color: #333;
    }}
    
    h1 {{
      font-size: 18pt;
      color: #1a1a1a;
      border-bottom: 2px solid #2563eb;
      padding-bottom: 0.3em;
      margin-top: 1.5em;
      page-break-before: always;
    }}
    
    h1:first-of-type {{
      page-break-before: avoid;
      text-align: center;
      border-bottom: none;
      font-size: 22pt;
      color: #1e40af;
    }}
    
    h2 {{
      font-size: 14pt;
      color: #1e40af;
      margin-top: 1.2em;
      border-bottom: 1px solid #e5e7eb;
      padding-bottom: 0.2em;
    }}
    
    h3 {{
      font-size: 12pt;
      color: #374151;
      margin-top: 1em;
    }}
    
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1em 0;
      font-size: 10pt;
    }}
    
    th, td {{
      border: 1px solid #e5e7eb;
      padding: 0.5em;
      text-align: left;
    }}
    
    th {{
      background-color: #f3f4f6;
      font-weight: 600;
      color: #1f2937;
    }}
    
    tr:nth-child(even) {{
      background-color: #f9fafb;
    }}
    
    ul, ol {{
      margin: 0.5em 0;
      padding-left: 1.5em;
    }}
    
    li {{
      margin: 0.3em 0;
    }}
    
    strong {{
      color: #1f2937;
    }}
    
    .subtitle {{
      text-align: center;
      font-size: 10pt;
      color: #6b7280;
      margin: 0.5em 0 2em 0;
    }}
    
    hr {{
      border: none;
      border-top: 1px solid #e5e7eb;
      margin: 2em 0;
    }}
    
    blockquote {{
      border-left: 3px solid #2563eb;
      padding-left: 1em;
      margin: 1em 0;
      color: #4b5563;
      font-style: italic;
      background-color: #f9fafb;
      padding: 1em;
    }}
  </style>
</head>
<body>
  {html_body}
</body>
</html>
"""

# Generate PDF
output_path = Path("/home/yesf37332/Desktop/jy-wealth-investment-analysis/reports/中邮理财鸿锦一年定开 88 号分析报告_2026-04-02.pdf")
HTML(string=html_doc).write_pdf(output_path)

print(f"✅ PDF generated: {output_path}")
