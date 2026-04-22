#!/usr/bin/env python3
"""
Lightweight agent memory system with episodic, semantic, and working memory.
"""

import json
import os
import time
from typing import List, Dict, Any, Optional, Tuple


class AgentMemory:
    """A lightweight memory system for AI agents."""

    def __init__(self, path: str = "memory.json", auto_save: bool = True, working_memory_size: int = 20):
        """
        Initialize the memory system.

        Args:
            path: Path to the JSON file for persistence
            auto_save: Whether to auto-save after each mutation
            working_memory_size: Maximum items in working memory before eviction to episodic
        """
        self.path = path
        self.auto_save = auto_save
        self.working_memory_size = working_memory_size
        self.memory: Dict[str, List[Dict[str, Any]]] = {
            "episodic": [],
            "semantic": [],
            "working": []
        }
        self._load()

    def _load(self) -> None:
        """Load memory from JSON file, gracefully handling corruption."""
        if not os.path.exists(self.path):
            self.memory = {
                "episodic": [],
                "semantic": [],
                "working": []
            }
            return

        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Validate structure
                if isinstance(data, dict) and all(k in data for k in ["episodic", "semantic", "working"]):
                    self.memory = data
                else:
                    # Corrupted or invalid format - start fresh
                    self.memory = {
                        "episodic": [],
                        "semantic": [],
                        "working": []
                    }
        except (json.JSONDecodeError, IOError):
            # Corrupted file - start fresh
            self.memory = {
                "episodic": [],
                "semantic": [],
                "working": []
            }

    def _save(self) -> None:
        """Save memory to JSON file."""
        try:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Failed to save memory: {e}")

    def remember(self, content: str, kind: str = "episodic", tags: Optional[List[str]] = None) -> str:
        """
        Store a memory.

        Args:
            content: The text content to store
            kind: Type of memory - "episodic", "semantic", or "working"
            tags: Optional list of tags for categorization

        Returns:
            The unique ID of the stored memory
        """
        if kind not in self.memory:
            raise ValueError(f"Invalid kind: {kind}. Must be one of {list(self.memory.keys())}")

        memory_id = self._generate_id()
        memory_entry = {
            "id": memory_id,
            "content": content,
            "tags": tags or [],
            "timestamp": time.time()
        }

        self.memory[kind].append(memory_entry)

        # Handle working memory eviction
        if kind == "working" and len(self.memory["working"]) > self.working_memory_size:
            # Evict oldest working memory to episodic
            evicted = self.memory["working"].pop(0)
            evicted["kind"] = "episodic"  # Change kind when moving
            self.memory["episodic"].append(evicted)

        if self.auto_save:
            self._save()

        return memory_id

    def _generate_id(self) -> str:
        """Generate a unique ID for a memory."""
        return f"mem_{int(time.time() * 1000000)}_{hash(str(time.time())) & 0xFFFFFFFF}"

    def recall(self, query: str, kind: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memories by keyword matching across content and tags.

        Args:
            query: Text to search for
            kind: Optional memory kind to filter by ("episodic", "semantic", "working")
            limit: Maximum number of results to return

        Returns:
            List of memory dicts ranked by relevance (recency + keyword hits)
        """
        if kind and kind not in self.memory:
            raise ValueError(f"Invalid kind: {kind}. Must be one of {list(self.memory.keys())}")

        query_lower = query.lower()
        results = []

        kinds_to_search = [kind] if kind else self.memory.keys()

        for k in kinds_to_search:
            for memory in self.memory[k]:
                # Skip if not matching kind filter
                if kind and memory.get("kind", k) != kind:
                    continue

                # Check for matches in content or tags
                content_match = query_lower in memory["content"].lower()
                tags_match = any(query_lower in tag.lower() for tag in memory.get("tags", []))

                if content_match or tags_match:
                    # Calculate relevance score: recency + keyword hits
                    age_score = 1.0 / (1.0 + (time.time() - memory["timestamp"]) / 86400)  # Newer = higher score
                    keyword_score = (
                        (2 if content_match else 0) +
                        sum(1 for tag in memory.get("tags", []) if query_lower in tag.lower())
                    )
                    relevance = age_score + keyword_score

                    mem_copy = memory.copy()
                    mem_copy["kind"] = k
                    results.append((relevance, mem_copy))

        # Sort by relevance (descending) and return top results
        results.sort(key=lambda x: x[0], reverse=True)
        return [memory for _, memory in results[:limit]]

    def recall_recent(self, n: int = 10, kind: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get the most recent memories.

        Args:
            n: Number of recent memories to return
            kind: Optional memory kind to filter by

        Returns:
            List of the n most recent memory dicts
        """
        if kind and kind not in self.memory:
            raise ValueError(f"Invalid kind: {kind}. Must be one of {list(self.memory.keys())}")

        kinds_to_search = [kind] if kind else self.memory.keys()
        results = []

        for k in kinds_to_search:
            for memory in self.memory[k]:
                if kind and memory.get("kind", k) != kind:
                    continue
                mem_copy = memory.copy()
                mem_copy["kind"] = k
                results.append(mem_copy)

        # Sort by timestamp (descending) and return top n
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        return results[:n]

    def forget(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.

        Args:
            memory_id: The ID of the memory to delete

        Returns:
            True if memory was found and deleted, False otherwise
        """
        for kind in self.memory:
            for i, memory in enumerate(self.memory[kind]):
                if memory["id"] == memory_id:
                    del self.memory[kind][i]
                    if self.auto_save:
                        self._save()
                    return True
        return False

    def summarize(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dict with counts per kind, oldest/newest timestamps, and total size
        """
        stats = {
            "counts": {},
            "oldest": None,
            "newest": None,
            "total": 0
        }

        timestamps = []

        for kind, memories in self.memory.items():
            count = len(memories)
            stats["counts"][kind] = count
            stats["total"] += count

            for memory in memories:
                timestamps.append(memory["timestamp"])

        if timestamps:
            stats["oldest"] = min(timestamps)
            stats["newest"] = max(timestamps)

        return stats

    def save(self) -> None:
        """Manually save memory to disk."""
        self._save()

    @property
    def working(self) -> List[Dict[str, Any]]:
        """Get current working memory list."""
        return self.memory["working"].copy()


def demo():
    """Run a usage demo of the memory system."""
    print("=== Agent Memory Demo ===")
    
    # Create memory instance
    mem = AgentMemory("demo_memory.json", auto_save=True)
    
    # Clear any existing demo data
    mem.memory = {"episodic": [], "semantic": [], "working": []}
    mem._save()
    
    # Add some memories
    print("\nAdding memories...")
    mem.remember("User prefers dark mode", kind="semantic", tags=["preferences", "ui"])
    mem.remember("User said hello at the start of conversation", kind="episodic")
    mem.remember("Need to review the code tomorrow", kind="working", tags=["todo"])
    mem.remember("User likes Python for scripting", kind="semantic", tags=["preferences", "language"])
    mem.remember("Just finished a bug fix", kind="episodic", tags=["work", "achievement"])
    
    # Add some working memories to trigger eviction
    for i in range(25):
        mem.remember(f"Working memory item {i}", kind="working")
    
    # Search memories
    print("\nSearching for 'user':")
    results = mem.recall("user")
    for i, r in enumerate(results[:3], 1):
        print(f"  {i}. [{r['kind']}] {r['content']} (tags: {r['tags']})")
    
    print("\nSearching for 'python':")
    results = mem.recall("python", kind="semantic")
    for i, r in enumerate(results, 1):
        print(f"  {i}. [{r['kind']}] {r['content']}")
    
    # Get recent memories
    print("\nMost recent 3 memories:")
    recent = mem.recall_recent(3)
    for i, r in enumerate(recent, 1):
        print(f"  {i}. [{r['kind']}] {r['content']}")
    
    # Show stats
    print("\nMemory stats:")
    stats = mem.summarize()
    print(f"  Total memories: {stats['total']}")
    for kind, count in stats['counts'].items():
        print(f"  {kind.capitalize()}: {count}")
    if stats['oldest']:
        print(f"  Oldest: {time.ctime(stats['oldest'])}")
    if stats['newest']:
        print(f"  Newest: {time.ctime(stats['newest'])}")
    
    # Show working memory
    print(f"\nWorking memory ({len(mem.working)} items):")
    for i, w in enumerate(mem.working[-3:], 1):  # Last 3 items
        print(f"  {i}. {w['content']}")
    
    # Clean up demo file
    try:
        os.remove("demo_memory.json")
    except FileNotFoundError:
        pass
    
    print("\nDemo complete!")


if __name__ == "__main__":
    demo()