#!/usr/bin/env python3
"""
Comprehensive tests for the agent memory system.
"""

import json
import os
import tempfile
import time
from agent_memory import AgentMemory


def test_basic_remember_and_recall():
    """Test basic remember and recall functionality."""
    print("Testing basic remember and recall...")
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        mem = AgentMemory(temp_path, auto_save=False)
        
        # Clear any existing data
        mem.memory = {"episodic": [], "semantic": [], "working": []}
        
        # Add a memory
        mem_id = mem.remember("User prefers dark mode", kind="semantic", tags=["preferences"])
        
        # Recall it
        results = mem.recall("dark mode")
        assert len(results) == 1
        assert results[0]["content"] == "User prefers dark mode"
        assert results[0]["id"] == mem_id
        assert results[0]["kind"] == "semantic"
        assert "preferences" in results[0]["tags"]
        
        print("✓ Basic remember and recall passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_recall_recent():
    """Test recalling recent memories."""
    print("Testing recall_recent...")
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        mem = AgentMemory(temp_path, auto_save=False)
        mem.memory = {"episodic": [], "semantic": [], "working": []}
        
        # Add memories with small delays to ensure different timestamps
        mem.remember("First memory", kind="episodic")
        time.sleep(0.01)  # Small delay
        mem.remember("Second memory", kind="episodic")
        time.sleep(0.01)
        mem.remember("Third memory", kind="episodic")
        
        # Get recent memories
        recent = mem.recall_recent(2)
        assert len(recent) == 2
        assert recent[0]["content"] == "Third memory"  # Most recent first
        assert recent[1]["content"] == "Second memory"
        
        print("✓ Recall recent passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_forget():
    """Test forgetting memories by ID."""
    print("Testing forget...")
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        mem = AgentMemory(temp_path, auto_save=False)
        mem.memory = {"episodic": [], "semantic": [], "working": []}
        
        # Add a memory
        mem_id = mem.remember("To be forgotten", kind="semantic")
        
        # Verify it exists
        results = mem.recall("forgotten")
        assert len(results) == 1
        
        # Forget it
        assert mem.forget(mem_id) == True
        
        # Verify it's gone
        results = mem.recall("forgotten")
        assert len(results) == 0
        
        # Trying to forget again should return False
        assert mem.forget(mem_id) == False
        
        print("✓ Forget passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_working_memory_eviction():
    """Test that working memory evicts to episodic when full."""
    print("Testing working memory eviction...")
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        mem = AgentMemory(temp_path, auto_save=False, working_memory_size=3)
        mem.memory = {"episodic": [], "semantic": [], "working": []}
        
        # Add 5 items to working memory (should evict 2 to episodic)
        for i in range(5):
            mem.remember(f"Working item {i}", kind="working")
        
        # Check working memory has at most 3 items
        assert len(mem.working) == 3
        
        # Check episodic has 2 items (the evicted ones)
        episodic_contents = [m["content"] for m in mem.memory["episodic"]]
        assert "Working item 0" in episodic_contents
        assert "Working item 1" in episodic_contents
        assert "Working item 2" not in episodic_contents  # Still in working
        
        print("✓ Working memory eviction passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_persistence():
    """Test that memory saves and loads correctly."""
    print("Testing persistence...")
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        # Create and populate first instance
        mem1 = AgentMemory(temp_path, auto_save=True)
        mem1.memory = {"episodic": [], "semantic": [], "working": []}
        
        mem1.remember("Persistent memory", kind="semantic", tags=["test"])
        mem_id = mem1.remember("Another memory", kind="episodic")
        
        # Create second instance to test loading
        mem2 = AgentMemory(temp_path, auto_save=False)
        
        # Verify the memories were loaded
        results = mem2.recall("Persistent")
        assert len(results) == 1
        assert results[0]["content"] == "Persistent memory"
        assert results[0]["kind"] == "semantic"
        assert "test" in results[0]["tags"]
        
        results = mem2.recall("Another")
        assert len(results) == 1
        assert results[0]["content"] == "Another memory"
        assert results[0]["id"] == mem_id
        assert results[0]["kind"] == "episodic"
        
        print("✓ Persistence passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_corrupted_file_handling():
    """Test graceful handling of corrupted JSON files."""
    print("Testing corrupted file handling...")
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        # Write invalid JSON to the file
        with open(temp_path, 'w') as f:
            f.write("{ invalid json content")
        
        # Should gracefully handle corruption and start with empty memory
        mem = AgentMemory(temp_path, auto_save=False)
        
        # Should have empty memory
        assert len(mem.memory["episodic"]) == 0
        assert len(mem.memory["semantic"]) == 0
        assert len(mem.memory["working"]) == 0
        
        # Should be able to add new memories
        mem_id = mem.remember("New memory after corruption", kind="semantic")
        results = mem.recall("New memory")
        assert len(results) == 1
        assert results[0]["content"] == "New memory after corruption"
        
        print("✓ Corrupted file handling passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_empty_search():
    """Test searching when no matches exist."""
    print("Testing empty search...")
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        mem = AgentMemory(temp_path, auto_save=False)
        mem.memory = {"episodic": [], "semantic": [], "working": []}
        
        mem.remember("Some content", kind="semantic")
        
        # Search for non-existent term
        results = mem.recall("nonexistent")
        assert len(results) == 0
        
        print("✓ Empty search passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_tag_search():
    """Test searching by tags."""
    print("Testing tag search...")
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        mem = AgentMemory(temp_path, auto_save=False)
        mem.memory = {"episodic": [], "semantic": [], "working": []}
        
        mem.remember("User likes Python", kind="semantic", tags=["preferences", "language"])
        mem.remember("User likes JavaScript", kind="semantic", tags=["preferences", "language"])
        mem.remember("User had a meeting", kind="episodic", tags=["work", "meeting"])
        
        # Search by tag
        results = mem.recall("preferences")
        assert len(results) == 2
        assert all("preferences" in r["tags"] for r in results)
        
        results = mem.recall("meeting")
        assert len(results) == 1
        assert results[0]["content"] == "User had a meeting"
        assert "meeting" in results[0]["tags"]
        
        print("✓ Tag search passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_summary():
    """Test the summarize function."""
    print("Testing summary...")
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        mem = AgentMemory(temp_path, auto_save=False)
        mem.memory = {"episodic": [], "semantic": [], "working": []}
        
        # Add various memories
        mem.remember("Semantic memory", kind="semantic")
        mem.remember("Episodic memory", kind="episodic")
        mem.remember("Working memory", kind="working")
        
        stats = mem.summarize()
        
        assert stats["total"] == 3
        assert stats["counts"]["semantic"] == 1
        assert stats["counts"]["episodic"] == 1
        assert stats["counts"]["working"] == 1
        assert stats["oldest"] is not None
        assert stats["newest"] is not None
        assert stats["newest"] >= stats["oldest"]
        
        print("✓ Summary passed")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def run_all_tests():
    """Run all tests and report results."""
    print("Running agent memory tests...\n")
    
    test_functions = [
        test_basic_remember_and_recall,
        test_recall_recent,
        test_forget,
        test_working_memory_eviction,
        test_persistence,
        test_corrupted_file_handling,
        test_empty_search,
        test_tag_search,
        test_summary
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} FAILED: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)