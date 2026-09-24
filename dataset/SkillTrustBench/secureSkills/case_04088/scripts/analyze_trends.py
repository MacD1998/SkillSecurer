#!/usr/bin/env python3
"""
Analyze research trends based on arXiv data.
"""
import argparse
import requests
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime

def search_papers(query, max_results=100, category=None, sort_by="submittedDate"):
    """
    Search arXiv for papers.
    """
    base_url = "http://export.arxiv.org/api/query"
    
    # Build the query
    search_query = f"all:{query}"
    if category:
        search_query = f"cat:{category} AND {search_query}"
    
    # Parameters for the API request
    params = {
        "search_query": search_query,
        "start": 0,
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
    root = ET.fromstring(response.content)
    
    papers = []
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        paper = {
            "id": entry.find('{http://www.w3.org/2005/Atom}id').text.split('/')[-1],
            "title": entry.find('{http://www.w3.org/2005/Atom}title').text.strip(),
            "summary": entry.find('{http://www.w3.org/2005/Atom}summary').text.strip(),
            "authors": [author.find('{http://www.w3.org/2005/Atom}name').text for author in entry.findall('{http://www.w3.org/2005/Atom}author')],
            "published": entry.find('{http://www.w3.org/2005/Atom}published').text,
            "categories": [cat.attrib['term'] for cat in entry.findall('{http://www.w3.org/2005/Atom}category')]
        }
        papers.append(paper)
    
    return papers

def analyze_publication_trends(papers):
    """
    Analyze publication trends by month/year.
    """
    monthly_counts = defaultdict(int)
    
    for paper in papers:
        published_date = datetime.fromisoformat(paper['published'].replace('Z', '+00:00'))
        month_year = published_date.strftime('%Y-%m')
        monthly_counts[month_year] += 1
    
    return monthly_counts

def analyze_category_distribution(papers):
    """
    Analyze category distribution.
    """
    category_counts = Counter()
    
    for paper in papers:
        for category in paper['categories']:
            # Get the main category (e.g., cs.AI -> cs)
            main_category = category.split('.')[0]
            category_counts[main_category] += 1
    
    return category_counts

def analyze_authors(papers, top_n=10):
    """
    Analyze top authors.
    """
    author_counts = Counter()
    
    for paper in papers:
        for author in paper['authors']:
            author_counts[author] += 1
    
    return author_counts.most_common(top_n)

def main():
    parser = argparse.ArgumentParser(description='Analyze research trends based on arXiv data')
    parser.add_argument('--query', default='', help='Search query')
    parser.add_argument('--category', help='arXiv category (e.g., cs.AI)')
    parser.add_argument('--max-results', type=int, default=100, help='Maximum number of results')
    args = parser.parse_args()
    
    # Search for papers
    papers = search_papers(
        query=args.query,
        max_results=args.max_results,
        category=args.category
    )
    
    print(f"Analyzing {len(papers)} papers:\n")
    
    # Analyze publication trends
    print("Publication Trends by Month/Year:")
    monthly_counts = analyze_publication_trends(papers)
    for month_year, count in sorted(monthly_counts.items()):
        print(f"  {month_year}: {count} papers")
    
    # Analyze category distribution
    print("\nCategory Distribution:")
    category_counts = analyze_category_distribution(papers)
    for category, count in category_counts.most_common():
        print(f"  {category}: {count} papers")
    
    # Analyze top authors
    print("\nTop Authors:")
    top_authors = analyze_authors(papers)
    for author, count in top_authors:
        print(f"  {author}: {count} papers")

if __name__ == "__main__":
    main()
