"""
AI Item Matching Engine
Uses TF-IDF vectorization + Cosine Similarity to match lost items
with found items based on name, description, and category.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def build_text(item):
    """Combine item fields into a single text for vectorization."""
    parts = [
        str(item['name'] or ''),
        str(item['description'] or ''),
        str(item['category'] or ''),
    ]
    return ' '.join(parts).lower()


def find_matches(lost_item, found_items, top_n=5):
    """
    Match a lost item against a list of found items using TF-IDF + cosine similarity.

    Returns list of (found_item, score_percent) sorted by score descending.
    """
    if not found_items:
        return []

    lost_text = build_text(lost_item)
    found_texts = [build_text(f) for f in found_items]

    # Need at least 2 docs for TF-IDF to be meaningful
    all_texts = [lost_text] + found_texts

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),   # unigrams + bigrams
        stop_words='english',
        min_df=1
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(all_texts)
    except ValueError:
        return []

    # lost item is index 0, found items are 1..n
    lost_vec = tfidf_matrix[0]
    found_vecs = tfidf_matrix[1:]

    scores = cosine_similarity(lost_vec, found_vecs)[0]

    # Pair each found item with its score
    results = []
    for i, score in enumerate(scores):
        pct = round(float(score) * 100, 1)
        if pct > 0:
            results.append((found_items[i], pct))

    # Sort by score descending, return top N
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]


def accuracy_summary(matches):
    """
    Returns a simple accuracy summary string for display.
    Based on the top match score.
    """
    if not matches:
        return "No matches found", 0
    top_score = matches[0][1]
    if top_score >= 75:
        label = "High Confidence Match"
    elif top_score >= 45:
        label = "Moderate Match"
    elif top_score >= 20:
        label = "Low Confidence Match"
    else:
        label = "Weak Match"
    return label, top_score
