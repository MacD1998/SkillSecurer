# arXiv API Reference

## Overview

The arXiv API provides programmatic access to the arXiv preprint server. It allows users to search for papers, retrieve metadata, and access paper PDFs.

## API Endpoints

### Search API

**Endpoint:** `http://export.arxiv.org/api/query`

**Parameters:**
- `search_query`: Search query string (required)
- `id_list`: Comma-separated list of arXiv paper IDs
- `start`: Start index for paginated results (default: 0)
- `max_results`: Maximum number of results to return (default: 10, maximum: 1000)
- `sortBy`: Sort results by relevance, lastUpdatedDate, or submittedDate
- `sortOrder`: Sort order (ascending or descending)

**Example Request:**
```
http://export.arxiv.org/api/query?search_query=all:machine+learning&start=0&max_results=10&sortBy=relevance&sortOrder=descending
```

### PDF Access

**Endpoint:** `https://arxiv.org/pdf/{paper_id}.pdf`

**Example:**
```
https://arxiv.org/pdf/2301.00001.pdf
```

## Response Format

The API returns responses in Atom XML format. Here's an example of a single paper entry:

```xml
<entry>
  <id>http://arxiv.org/abs/2301.00001v1</id>
  <updated>2023-01-01T00:00:00Z</updated>
  <published>2023-01-01T00:00:00Z</published>
  <title>Example Paper Title</title>
  <summary>Example paper abstract...</summary>
  <author>
    <name>John Doe</name>
  </author>
  <category term="cs.AI"/>
  <link href="http://arxiv.org/abs/2301.00001v1" rel="alternate" type="text/html"/>
  <link title="pdf" href="http://arxiv.org/pdf/2301.00001v1" rel="related" type="application/pdf"/>
</entry>
```

## Rate Limiting

The arXiv API has rate limits to prevent abuse. It's recommended to:
- Make requests at a reasonable rate (no more than one request every few seconds)
- Cache results when possible
- Use the `id_list` parameter for batch requests instead of multiple single requests

## Search Syntax

The search query syntax supports boolean operators and field specifiers:

### Field Specifiers
- `ti`: Title
- `au`: Author
- `abs`: Abstract
- `co`: Comment
- `jr`: Journal reference
- `cat`: Category
- `rn`: Report number
- `id`: ID
- `all`: All fields

### Boolean Operators
- `AND`: Logical AND
- `OR`: Logical OR
- `NOT`: Logical NOT
- `()`: Grouping

**Example:**
```
cat:cs.AI AND (ti:machine OR ti:learning)
```

## Examples

### Search for papers by keyword
```python
import requests

url = "http://export.arxiv.org/api/query"
params = {
    "search_query": "all:machine learning",
    "max_results": 10
}

response = requests.get(url, params=params)
```

### Search for papers by category
```python
import requests

url = "http://export.arxiv.org/api/query"
params = {
    "search_query": "cat:cs.AI",
    "max_results": 10
}

response = requests.get(url, params=params)
```

### Get details for specific papers
```python
import requests

url = "http://export.arxiv.org/api/query"
params = {
    "id_list": "2301.00001,2301.00002"
}

response = requests.get(url, params=params)
```