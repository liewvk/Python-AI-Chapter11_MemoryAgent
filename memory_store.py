# memory_store.py
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from settings import (
    MEMORY_FILE, MAX_RECENT_EXCHANGES, MAX_SAVED_MEMORIES,
    MAX_MEMORY_LENGTH, MAX_RECALLED
)

CATEGORIES = ("project", "preference", "goal", "note")
STOPWORDS = {"a", "an", "and", "are", "at", "be", "do", "for", "from",
             "have", "i", "in", "is", "it", "me", "my", "of", "on", "or",
             "the", "to", "was", "what", "which", "with", "you"}


def keywords(value):
    return {word for word in re.findall(r"[a-z0-9]+", value.lower())
            if word not in STOPWORDS and len(word) > 1}


def now_utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class MemoryStore:
    def __init__(self, path=MEMORY_FILE):
        self.path = Path(path)
        self.items = []
        if self.path.exists():
            self.load()

    def load(self):
        if self.path.stat().st_size > 150_000:
            raise ValueError("Memory file is unexpectedly large.")
        data = json.loads(self.path.read_text(encoding="utf-8"))
        items = data.get("memories") if isinstance(data, dict) else None
        if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(items, list):
            raise ValueError("Unsupported memory file format.")
        if len(items) > MAX_SAVED_MEMORIES:
            raise ValueError("Too many saved memories.")
        seen = set()
        for item in items:
            if not isinstance(item, dict) or set(item) != {"id", "category", "text", "created_at", "updated_at"}:
                raise ValueError("Invalid memory record.")
            if (not isinstance(item["id"], str) or
                    not re.fullmatch(r"[0-9a-f]{8}", item["id"]) or item["id"] in seen or
                    item["category"] not in CATEGORIES or
                    not isinstance(item["text"], str) or
                    not item["text"].strip() or len(item["text"]) > MAX_MEMORY_LENGTH or
                    not isinstance(item["created_at"], str) or
                    not isinstance(item["updated_at"], str)):
                raise ValueError("Invalid memory values.")
            seen.add(item["id"])
        self.items = items

    def _commit(self, items):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"version": 1, "memories": items},
                                  indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)
        self.items = items

    def add(self, category, text):
        category = category.strip().lower()
        text = text.strip()
        if category not in CATEGORIES:
            raise ValueError("Category must be project, preference, goal, or note.")
        if not text or len(text) > MAX_MEMORY_LENGTH:
            raise ValueError(f"Memory must contain 1-{MAX_MEMORY_LENGTH} characters.")
        if len(self.items) >= MAX_SAVED_MEMORIES:
            raise ValueError("Memory store has reached its limit.")
        identifier = uuid4().hex[:8]
        while any(item["id"] == identifier for item in self.items):
            identifier = uuid4().hex[:8]
        timestamp = now_utc()
        item = {"id": identifier, "category": category, "text": text,
                "created_at": timestamp, "updated_at": timestamp}
        self._commit(self.items + [item])
        return item

    def update(self, identifier, text):
        text = text.strip()
        if not text or len(text) > MAX_MEMORY_LENGTH:
            raise ValueError(f"Memory must contain 1-{MAX_MEMORY_LENGTH} characters.")
        items = [item.copy() for item in self.items]
        for item in items:
            if item["id"] == identifier:
                item["text"] = text
                item["updated_at"] = now_utc()
                self._commit(items)
                return item
        raise ValueError("Memory ID not found.")

    def forget(self, identifier):
        items = [item for item in self.items if item["id"] != identifier]
        if len(items) == len(self.items):
            raise ValueError("Memory ID not found.")
        self._commit(items)

    def search(self, question, limit=MAX_RECALLED):
        words = keywords(question)
        if not words:
            return []
        ranked = []
        for item in self.items:
            content = keywords(item["text"])
            category = keywords(item["category"])
            score = len(words & content) + 3 * len(words & category)
            if score:
                ranked.append((score, item["updated_at"], item))
        ranked.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
        return [entry[2].copy() for entry in ranked[:limit]]

    def list_all(self):
        return [item.copy() for item in self.items]


class ShortTermChat:
    def __init__(self):
        self.messages = []

    def add_exchange(self, question, answer):
        self.messages.extend([
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer}
        ])
        self.messages = self.messages[-2 * MAX_RECENT_EXCHANGES:]

    def clear(self):
        self.messages.clear()

    def recent(self):
        return [message.copy() for message in self.messages]
