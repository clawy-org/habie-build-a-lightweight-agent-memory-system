# Lightweight Agent Memory System

A self-contained Python module for agent long-term memory — store, search, and retrieve facts with semantic similarity and automatic organization.

## Features

- **Three memory types**:
  - **Episodic**: timestamped events ("user said X at T")
  - **Semantic**: factual key-value pairs ("user name is Misha")
  - **Working**: short-term scratchpad (last N items, auto-evicted to episodic)

- **Keyword search**: Find memories by matching content or tags
- **Ranked results**: Most relevant memories returned first (recency + keyword hits)
- **Persistence**: Human-readable JSON file with graceful corruption handling
- **Zero dependencies**: Standard library only
- **Auto-save**: Optional automatic persistence after each mutation
- **Working memory eviction**: FIFO transfer to episodic when full

## Installation

Copy `agent_memory.py` into your project. No external dependencies required.

## Usage

### Basic usage

```python
from agent_memory import AgentMemory

# Create memory instance (auto-creates/loads JSON file)
mem = AgentMemory("agent_memory.json")

# Store memories
mem.remember("User prefers dark mode", kind="semantic", tags=["preferences", "ui"])
mem.remember("User said hello at conversation start", kind="episodic")
mem.remember("Need to review PR #42", kind="working", tags=["todo"])

# Search memories
results = mem.recall("dark mode")
# Returns: [{"id": "...", "content": "User prefers dark mode", ...}]

# Get recent memories
recent = mem.recall_recent(5)  # Last 5 memories across all types

# Access working memory directly
current_tasks = mem.working  # List of items in working memory

# Get statistics
stats = mem.summarize()
# Returns: {
#   "counts": {"episodic": 5, "semantic": 3, "working": 2},
#   "oldest": 1234567890.0,
#   "newest": 1234567895.0,
#   "total": 10
# }

# Delete a memory
mem.forget(memory_id)

# Manually save (auto-save enabled by default)
mem.save()
```

### Memory Types

#### Episodic Memory
Time-stamped events that happened in sequence.
```python
mem.remember("User clicked the submit button", kind="episodic", tags=["action", "ui"])
mem.remember("System crashed at 2:30 PM", kind="episodic", tags=["error", "system"])
```

#### Semantic Memory
Factual knowledge that doesn't change over time.
```python
mem.remember("User's name is Misha", kind="semantic", tags=["identity"])
mem.remember("Python is good for scripting", kind="semantic", tags=["preferences", "language"])
```

#### Working Memory
Short-term scratchpad for immediate context.
```python
mem.remember("Current task: fix login bug", kind="working", tags=["task"])
mem.remember("Need to check API response", kind="working", tags=["todo"])
```
When working memory exceeds the configured limit (default 20), oldest items are automatically moved to episodic memory.

## API Reference

### `AgentMemory(path="memory.json", auto_save=True, working_memory_size=20)`

Create a new memory instance.

**Parameters**:
- `path`: Path to JSON file for persistence (default: "memory.json")
- `auto_save`: Whether to auto-save after each mutation (default: True)
- `working_memory_size`: Max items in working memory before eviction (default: 20)

### `remember(content, kind="episodic", tags=None) → str`

Store a memory and return its unique ID.

**Parameters**:
- `content`: The text to store
- `kind`: Memory type - "episodic", "semantic", or "working"
- `tags`: Optional list of string tags for categorization

**Returns**: Unique memory ID string

### `recall(query, kind=None, limit=10) → List[Dict]`

Search memories by keyword matching.

**Parameters**:
- `query`: Text to search for (matches in content or tags)
- `kind`: Optional memory type to filter by
- `limit`: Maximum results to return (default: 10)

**Returns**: List of memory dicts, ranked by relevance (most relevant first)

Each memory dict contains:
- `id`: Unique identifier
- `content`: The stored text
- `tags`: List of tags
- `timestamp`: Unix timestamp when stored
- `kind`: Memory type ("episodic", "semantic", "working")

### `recall_recent(n=10, kind=None) → List[Dict]`

Get the most recent memories.

**Parameters**:
- `n`: Number of recent memories to return (default: 10)
- `kind`: Optional memory type to filter by

**Returns**: List of the n most recent memory dicts

### `forget(memory_id) → bool`

Delete a memory by ID.

**Parameters**:
- `memory_id`: The ID of the memory to delete

**Returns**: True if found and deleted, False if not found

### `summarize() → Dict`

Get memory statistics.

**Returns**: Dict with:
- `counts`: Dict of counts per memory type
- `oldest`: Unix timestamp of oldest memory
- `newest`: Unix timestamp of newest memory
- `total`: Total number of memories

### `.working` property

Direct access to current working memory list.

**Returns**: List of memory dicts currently in working memory

### `save()`

Manually persist memory to disk (called automatically if `auto_save=True`).

## Design Notes

### Search Algorithm
The `recall()` method uses a simple but effective scoring system:
- **Recency score**: Newer memories get higher scores (decays over days)
- **Keyword score**: +2 for content match, +1 per tag match
- Results sorted by total score (highest first)

### Memory Eviction
When working memory exceeds `working_memory_size`:
1. Oldest working memory item is removed
2. Item is appended to episodic memory (kind changed to "episodic")
3. Preserves original content, tags, and timestamp

### Corruption Handling
If the JSON file is corrupted or unreadable:
- System starts with empty memory (no crash)
- New memories can still be stored
- Next save attempt will overwrite the corrupted file

## Testing

Run the test suite:
```bash
python -m pytest test_agent_memory.py -v
```
or
```bash
python test_agent_memory.py
```

## License

MIT - feel free to use in your projects!