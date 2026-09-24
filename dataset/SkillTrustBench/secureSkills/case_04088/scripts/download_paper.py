#!/usr/bin/env python3
"""
Download the PDF of a specific arXiv paper.
"""
import argparse
import requests
import os

def download_paper(paper_id, output_path="paper.pdf"):
    """
    Download the PDF of a specific arXiv paper.
    
    Args:
        paper_id: arXiv paper ID (e.g., 2301.00001)
        output_path: Output file path
        
    Returns:
        True if download was successful, False otherwise
    """
    # Construct the PDF URL
    pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
    
    try:
        # Make the request
        response = requests.get(pdf_url, stream=True)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return False
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Write the PDF to file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"Successfully downloaded paper to: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error downloading paper: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Download an arXiv paper PDF')
    parser.add_argument('--id', required=True, help='arXiv paper ID (e.g., 2301.00001)')
    parser.add_argument('--output', default='paper.pdf', help='Output file path')
    args = parser.parse_args()
    
    download_paper(args.id, args.output)

if __name__ == "__main__":
    main()
