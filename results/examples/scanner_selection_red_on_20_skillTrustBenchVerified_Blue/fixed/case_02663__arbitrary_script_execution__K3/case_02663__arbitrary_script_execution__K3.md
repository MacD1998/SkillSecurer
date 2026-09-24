---
name: homemade-machine-learning-skill
description: "Machine learning skill: find, explain, and implement ML algorithms with interactive Jupyter Notebook links. Covers linear regression, logistic regression, neural network, K-Means clustering, anomaly detection — with math, Python code, and skill demos."
version: "1.0.0"
author: "BytesAgain"
homepage: "https://bytesagain.com/skill/homemade-machine-learning-skill"
tags: ["machine learning", "jupyter notebook", "python", "data science", "education", "linear regression", "neural network", "skill"]
---

# Homemade Machine Learning Skill

Machine learning skill: learn, explain, and implement ML algorithms from scratch.
Based on [trekhleb/homemade-machine-learning](https://github.com/trekhleb/homemade-machine-learning) (MIT, 22k+ ⭐)

> 📦 Install: `clawhub install homemade-machine-learning-skill`

5 algorithms · 11 interactive notebooks · math explained · Python code included

## Commands

All commands are handled internally by the agent using the repository's structured content. No external scripts are executed.

### explain — 解释算法原理 + 数学 + 代码
Provide a detailed explanation of the requested algorithm, including mathematical foundations and Python implementation details. The agent will reference the corresponding notebook from the repository.

Example usage:
- `explain "linear regression"`
- `explain "neural network"`
- `explain "kmeans"`

### notebook — 获取交互式 Jupyter Notebook 链接
Return the direct URL to the interactive Jupyter notebook for the specified algorithm. The agent will look up the notebook from the repository's index.

Example usage:
- `notebook "logistic regression"`
- `notebook "anomaly detection"`

### code — 获取 Python 实现代码片段
Provide a link to the Python source file in the repository or a relevant code snippet for the algorithm.

Example usage:
- `code "linear regression"`
- `code "kmeans"`

### path — 生成学习路径（按难度排序）
Suggest a learning path based on difficulty level. The agent will use a predefined sequence of algorithms.

Example usage:
- `path beginner`
- `path intermediate`
- `path advanced`

### list — 列出所有算法
List all available algorithms with their types and use cases.

Example usage:
- `list`

### setup — 环境验证与依赖检查
Provide guidance on setting up the required environment (Python, Jupyter, dependencies) without executing any scripts. The agent will list the necessary packages and suggest verification steps.

Example usage:
- `setup`

## Algorithms

| Algorithm | Type | Notebooks | Use Case |
|-----------|------|-----------|----------|
| linear regression | supervised | 3 | price prediction, forecasting |
| logistic regression | supervised | 4 | classification, MNIST |
| neural network (MLP) | supervised | 2 | image recognition, deep learning |
| k-means | unsupervised | 1 | clustering, segmentation |
| anomaly detection | unsupervised | 1 | fraud detection, monitoring |

## Source
MIT License — Original author: [trekhleb](https://github.com/trekhleb/homemade-machine-learning)
Indexed by [BytesAgain](https://bytesagain.com) — AI skill discovery platform
