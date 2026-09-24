#!/usr/bin/env python3
"""
Search arXiv for papers matching specified criteria.
"""
import argparse
import requests
import json

def search_papers(query, max_results=10, category=None, sort_by="relevance", start=0):
    """
    Search arXiv for papers.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        category: arXiv category to filter by
        sort_by: Sort results by relevance, lastUpdatedDate, or submittedDate
        start: Start index for paginated results
        
    Returns:
        List of paper results
    """
    base_url = "http://export.arxiv.org/api/query"
    
    # Build the query
    search_query = f"all:{query}"
    if category:
        search_query = f"cat:{category} AND {search_query}"
    
    # Parameters for the API request
    params = {
        "search_query": search_query,
        "start": start,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": "descending"
    }
    
    # Make the request
    response = requests.get(base_url, params=params)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return []
    
    # Parse the response
    import xml.etree.ElementTree as ET
    root = ET.fromstring(response.content)
    
    papers = []
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
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
        papers.append(paper)
    
    return papers

def main():
    parser = argparse.ArgumentParser(description='Search arXiv for papers')
    parser.add_argument('--query', required=True, help='Search query')
    parser.add_argument('--max-results', type=int, default=10, help='Maximum number of results')
    parser.add_argument('--category', help='arXiv category (e.g., cs.AI)')
    parser.add_argument('--sort-by', choices=['relevance', 'lastUpdatedDate', 'submittedDate'], default='relevance', help='Sort by')
    parser.add_argument('--start', type=int, default=0, help='Start index')
    args = parser.parse_args()
    
    papers = search_papers(
        query=args.query,
        max_results=args.max_results,
        category=args.category,
        sort_by=args.sort_by,
        start=args.start
    )
    
    # Print results
    print(f"Found {len(papers)} papers:\n")
    for i, paper in enumerate(papers, 1):
        print(f"{i}. {paper['title']}")
        print(f"   Authors: {', '.join(paper['authors'])}")
        print(f"   ID: {paper['id']}")
        print(f"   Categories: {', '.join(paper['categories'])}")
        print(f"   Published: {paper['published']}")
        print(f"   Summary: {paper['summary'][:200]}...")
        print()

if __name__ == "__main__":
    main()
