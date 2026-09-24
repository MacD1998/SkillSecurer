---
name: arxiv-papers-search
description: Search, retrieve, and analyze academic papers from arXiv. Use when: (1) searching for specific research papers, (2) retrieving paper details and abstracts, (3) downloading paper PDFs, (4) analyzing research trends, or (5) getting paper metadata.
---

# Arxiv Skill

## Overview

This skill enables searching and retrieving academic papers from the arXiv preprint server. It provides functionality to search for papers by keywords, authors, or categories, retrieve paper details and abstracts, download PDF files, and analyze research trends.

## Quick Start

### Searching for Papers

To search for papers on arXiv, use the `search_papers` script with relevant keywords:

```bash
python scripts/search_papers.py --query "machine learning" --max-results 10
```

### Retrieving Paper Details

To get detailed information about a specific paper:

```bash
python scripts/get_paper_details.py --id 2301.00001
```

### Downloading Papers

To download a paper's PDF:

```bash
python scripts/download_paper.py --id 2301.00001 --output paper.pdf
```

## Core Functions

### Search Papers

Searches arXiv for papers matching specified criteria. Supports keyword search, author search, and category filtering.

**Parameters:**
- `--query`: Search query (required)
- `--max-results`: Maximum number of results to return (default: 10)
- `--category`: Filter by arXiv category (e.g., cs.AI, stat.ML)
- `--sort-by`: Sort results by relevance, lastUpdatedDate, or submittedDate
- `--start`: Start index for paginated results

**Example:**
```bash
python scripts/search_papers.py --query "transformer architecture" --category cs.CL --max-results 5
```

### Get Paper Details

Retrieves detailed information about a specific paper, including title, authors, abstract, categories, and links.

**Parameters:**
- `--id`: arXiv paper ID (required, e.g., 2301.00001)

**Example:**
```bash
python scripts/get_paper_details.py --id 2301.00001
```

### Download Paper

Downloads the PDF of a specific paper.

**Parameters:**
- `--id`: arXiv paper ID (required)
- `--output`: Output file path (default: paper.pdf)

**Example:**
```bash
python scripts/download_paper.py --id 2301.00001 --output transformer-paper.pdf
```

## Workflows

### Research Literature Review

1. Search for papers on a topic
2. Retrieve details for relevant papers
3. Download PDFs for in-depth analysis
4. Summarize key findings

**Example Workflow:**
```bash
# Search for recent papers on large language models
python scripts/search_papers.py --query "large language models" --max-results 10 --sort-by lastUpdatedDate

# Get details for a promising paper
python scripts/get_paper_details.py --id 2301.00001

# Download the PDF
python scripts/download_paper.py --id 2301.00001 --output llm-paper.pdf
```

### Trend Analysis

1. Search for papers in a specific category over time
2. Analyze publication trends
3. Identify emerging research areas

**Example Workflow:**
```bash
# Search for papers in machine learning category
python scripts/search_papers.py --query "" --category cs.LG --max-results 100 --sort-by submittedDate
```

## Resources

### scripts/
- `search_papers.py`: Search arXiv for papers
- `get_paper_details.py`: Get detailed information about a paper
- `download_paper.py`: Download paper PDFs
- `analyze_trends.py`: Analyze research trends based on arXiv data

### references/
- `api_reference.md`: arXiv API documentation and usage examples
- `categories.md`: List of arXiv categories and their descriptions

### assets/
- `templates/`: Templates for generating research summaries

## API Reference

For detailed information about the arXiv API, see `references/api_reference.md`.
