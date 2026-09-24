#!/usr/bin/env python3
"""
Get detailed information about a specific arXiv paper.
"""
import argparse
import requests
import xml.etree.ElementTree as ET

def get_paper_details(paper_id):
    """
    Get detailed information about a specific arXiv paper.
    
    Args:
        paper_id: arXiv paper ID (e.g., 2301.00001)
        
    Returns:
        Paper details as a dictionary
    """
    base_url = "http://export.arxiv.org/api/query"
    
    # Parameters for the API request
    params = {
        "id_list": paper_id
    }
    
    # Make the request
    response = requests.get(base_url, params=params)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return None
    
    # Parse the response
    root = ET.fromstring(response.content)
    
    # Find the entry
    entry = root.find('{http://www.w3.org/2005/Atom}entry')
    if not entry:
        print("Error: Paper not found")
        return None
    
    # Extract paper details
    paper = {
        "id": entry.find('{http://www.w3.org/2005/Atom}id').text.split('/')[-1],
        "title": entry.find('{http://www.w3.org/2005/Atom}title').text.strip(),
        "summary": entry.find('{http://www.w3.org/2005/Atom}summary').text.strip(),
        "authors": [author.find('{http://www.w3.org/2005/Atom}name').text for author in entry.findall('{http://www.w3.org/2005/Atom}author')],
        "published": entry.find('{http://www.w3.org/2005/Atom}published').text,
        "updated": entry.find('{http://www.w3.org/2005/Atom}updated').text,
        "categories": [cat.attrib['term'] for cat in entry.findall('{http://www.w3.org/2005/Atom}category')],
        "links": [link.attrib for link in entry.findall('{http://www.w3.org/2005/Atom}link')]
    }
    
    return paper

def main():
    parser = argparse.ArgumentParser(description='Get detailed information about an arXiv paper')
    parser.add_argument('--id', required=True, help='arXiv paper ID (e.g., 2301.00001)')
    args = parser.parse_args()
    
    paper = get_paper_details(args.id)
    
    if paper:
        print(f"Paper Details:\n")
        print(f"ID: {paper['id']}")
        print(f"Title: {paper['title']}")
        print(f"Authors: {', '.join(paper['authors'])}")
        print(f"Categories: {', '.join(paper['categories'])}")
        print(f"Published: {paper['published']}")
        print(f"Updated: {paper['updated']}")
        print(f"Summary: {paper['summary']}")
        print("\nLinks:")
        for link in paper['links']:
            print(f"  - {link.get('title', 'Link')}: {link['href']}")

if __name__ == "__main__":
    main()
