"""
DuckDuckGo Instant Answer API Integration
Uses the DuckDuckGo Instant Answer API for quick factual queries
"""

import httpx
from typing import Dict, Optional, List
import json


class DuckDuckGoInstantAnswer:
    """
    Client for DuckDuckGo Instant Answer API
    API Documentation: https://duckduckgo.com/api
    """

    BASE_URL = "https://api.duckduckgo.com/"

    def __init__(self):
        self.client = httpx.Client(timeout=10.0)

    def query(self, search_query: str, format: str = "json") -> Dict:
        """
        Query the DuckDuckGo Instant Answer API

        Args:
            search_query: The search query
            format: Response format (json or xml)

        Returns:
            Dict containing the API response
        """
        params = {
            "q": search_query,
            "format": format,
            "no_html": 1,  # Remove HTML from text
            "skip_disambig": 1  # Skip disambiguation
        }

        try:
            response = self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error querying DuckDuckGo Instant Answer API: {e}")
            return {}

    def get_abstract(self, search_query: str) -> Optional[str]:
        """
        Get the abstract/summary for a query

        Args:
            search_query: The search query

        Returns:
            Abstract text or None
        """
        result = self.query(search_query)

        # Try to get abstract
        abstract = result.get("Abstract")
        if abstract:
            return abstract

        # Try definition if no abstract
        definition = result.get("Definition")
        if definition:
            return definition

        # Try first related topic
        related_topics = result.get("RelatedTopics", [])
        if related_topics and isinstance(related_topics, list):
            first_topic = related_topics[0]
            if isinstance(first_topic, dict) and "Text" in first_topic:
                return first_topic["Text"]

        return None

    def get_definition(self, search_query: str) -> Optional[str]:
        """
        Get definition for a query

        Args:
            search_query: The search query

        Returns:
            Definition text or None
        """
        result = self.query(search_query)
        return result.get("Definition")

    def get_related_topics(self, search_query: str) -> List[Dict]:
        """
        Get related topics for a query

        Args:
            search_query: The search query

        Returns:
            List of related topic dictionaries
        """
        result = self.query(search_query)
        related = result.get("RelatedTopics", [])

        topics = []
        for item in related:
            if isinstance(item, dict):
                # Direct topic
                if "Text" in item:
                    topics.append({
                        "text": item.get("Text", ""),
                        "url": item.get("FirstURL", "")
                    })
                # Nested topics
                elif "Topics" in item:
                    for sub_item in item.get("Topics", []):
                        if isinstance(sub_item, dict) and "Text" in sub_item:
                            topics.append({
                                "text": sub_item.get("Text", ""),
                                "url": sub_item.get("FirstURL", "")
                            })

        return topics

    def get_instant_answer(self, search_query: str) -> Dict:
        """
        Get comprehensive instant answer including all available information

        Args:
            search_query: The search query

        Returns:
            Dict with structured instant answer data
        """
        result = self.query(search_query)

        return {
            "heading": result.get("Heading", ""),
            "abstract": result.get("Abstract", ""),
            "abstract_text": result.get("AbstractText", ""),
            "abstract_source": result.get("AbstractSource", ""),
            "abstract_url": result.get("AbstractURL", ""),
            "definition": result.get("Definition", ""),
            "definition_source": result.get("DefinitionSource", ""),
            "definition_url": result.get("DefinitionURL", ""),
            "answer": result.get("Answer", ""),
            "answer_type": result.get("AnswerType", ""),
            "type": result.get("Type", ""),
            "image": result.get("Image", ""),
            "related_topics": self.get_related_topics(search_query),
            "infobox": result.get("Infobox", {}),
            "results": result.get("Results", [])
        }

    def search_for_learning(self, topic: str) -> Dict:
        """
        Optimized search for learning content

        Args:
            topic: Learning topic to search for

        Returns:
            Dict with learning-relevant information
        """
        instant_answer = self.get_instant_answer(topic)

        # Compile learning-friendly response
        learning_content = {
            "topic": topic,
            "summary": instant_answer.get("abstract") or instant_answer.get("definition") or "",
            "source": instant_answer.get("abstract_source") or instant_answer.get("definition_source") or "",
            "source_url": instant_answer.get("abstract_url") or instant_answer.get("definition_url") or "",
            "related_topics": instant_answer.get("related_topics", []),
            "has_content": bool(instant_answer.get("abstract") or instant_answer.get("definition"))
        }

        return learning_content

    def __del__(self):
        """Clean up HTTP client"""
        if hasattr(self, 'client'):
            self.client.close()


# Convenience functions for agents to use

def search_topic_info(topic: str) -> Dict:
    """
    Search for topic information using DuckDuckGo Instant Answer API

    Args:
        topic: Topic to search

    Returns:
        Dict with topic information
    """
    ddg = DuckDuckGoInstantAnswer()
    return ddg.search_for_learning(topic)


def get_quick_definition(term: str) -> Optional[str]:
    """
    Get a quick definition for a term

    Args:
        term: Term to define

    Returns:
        Definition string or None
    """
    ddg = DuckDuckGoInstantAnswer()
    return ddg.get_abstract(term) or ddg.get_definition(term)


def get_related_learning_topics(topic: str) -> List[str]:
    """
    Get related topics for learning exploration

    Args:
        topic: Main topic

    Returns:
        List of related topic names
    """
    ddg = DuckDuckGoInstantAnswer()
    related = ddg.get_related_topics(topic)
    return [r["text"].split(" - ")[0] for r in related if r.get("text")][:5]


# Example usage
if __name__ == "__main__":
    ddg = DuckDuckGoInstantAnswer()

    # Test query
    result = ddg.search_for_learning("Python programming")
    print(json.dumps(result, indent=2))

    # Test definition
    definition = get_quick_definition("machine learning")
    print(f"\nDefinition: {definition}")

    # Test related topics
    related = get_related_learning_topics("data science")
    print(f"\nRelated topics: {related}")
