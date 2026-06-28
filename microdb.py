"""
MicroDB - Lightweight JSON database engine.
"""

import json
import os
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime


class Collection:
    def __init__(self, name: str, storage: 'Storage'):
        self.name = name
        self.storage = storage
        self._data = storage._load(name)
        self._lock = threading.RLock()
        self._indexes: Dict[str, Dict[Any, List[int]]] = {}
        self._build_all_indexes()

    def _build_all_indexes(self):
        for field in self.storage.indexes.get(self.name, []):
            self._rebuild_index(field)

    def _rebuild_index(self, field: str):
        index = {}
        for i, item in enumerate(self._data):
            value = item.get(field)
            if value is not None:
                index.setdefault(value, []).append(i)
        self._indexes[field] = index

    def _save(self):
        self.storage._save(self.name, self._data)

    def insert(self, data: Dict[str, Any]) -> Optional[int]:
        with self._lock:
            if not isinstance(data, dict):
                return None
            data = data.copy()
            if 'id' not in data:
                data['id'] = max((item.get('id', 0) for item in self._data), default=0) + 1
            if 'created_at' not in data:
                data['created_at'] = datetime.now().isoformat()
            position = len(self._data)
            self._data.append(data)
            for field, value in data.items():
                if field in self._indexes:
                    self._indexes[field].setdefault(value, []).append(position)
            self._save()
            return data['id']

    def find(self, **kwargs) -> List[Dict]:
        with self._lock:
            if not kwargs:
                return self._data.copy()
            if len(kwargs) == 1:
                field, value = list(kwargs.items())[0]
                if field in self._indexes:
                    return [self._data[i] for i in self._indexes[field].get(value, [])]
            result = self._data.copy()
            for field, value in kwargs.items():
                result = [item for item in result if item.get(field) == value]
            return result

    def find_one(self, **kwargs) -> Optional[Dict]:
        result = self.find(**kwargs)
        return result[0] if result else None

    def update(self, where: Dict, set_data: Dict) -> int:
        with self._lock:
            if not where or not set_data:
                return 0
            updated = 0
            for position, item in enumerate(self._data):
                if not all(item.get(k) == v for k, v in where.items()):
                    continue
                for key in set_data:
                    if key in self._indexes:
                        old_val = item.get(key)
                        if old_val is not None:
                            self._indexes[key][old_val] = [
                                i for i in self._indexes[key][old_val] if i != position
                            ]
                for key, value in set_data.items():
                    item[key] = value
                for key, value in set_data.items():
                    if key in self._indexes:
                        self._indexes[key].setdefault(value, []).append(position)
                updated += 1
            if updated:
                self._save()
            return updated

    def delete(self, **kwargs) -> int:
        with self._lock:
            if not kwargs:
                return 0
            to_delete = []
            for position, item in enumerate(self._data):
                if all(item.get(k) == v for k, v in kwargs.items()):
                    to_delete.append(position)
            if not to_delete:
                return 0
            for position in reversed(to_delete):
                for field, value in self._data[position].items():
                    if field in self._indexes:
                        index = self._indexes[field]
                        if value in index:
                            index[value] = [i for i in index[value] if i != position]
                del self._data[position]
            for field in self._indexes.keys():
                self._rebuild_index(field)
            self._save()
            return len(to_delete)

    def all(self) -> List[Dict]:
        with self._lock:
            return self._data.copy()

    def count(self) -> int:
        with self._lock:
            return len(self._data)

    def create_index(self, field: str) -> bool:
        with self._lock:
            if not isinstance(field, str):
                return False
            existing = self.storage.indexes.get(self.name, [])
            if field in existing:
                return True
            self.storage.indexes.setdefault(self.name, []).append(field)
            self._rebuild_index(field)
            self.storage._save_indexes()
            return True


class Storage:
    def __init__(self, path: str = 'data.json'):
        self.path = path
        self._cache = {}
        self.indexes: Dict[str, List[str]] = {}
        self._lock = threading.RLock()

        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._cache = data.get('data', {})
                        self.indexes = data.get('indexes', {})
            except Exception:
                pass

    def _load(self, name: str) -> List[Dict]:
        with self._lock:
            return self._cache.get(name, [])

    def _save(self, name: str, data: List[Dict]):
        with self._lock:
            self._cache[name] = data
            self._flush()

    def _save_indexes(self):
        with self._lock:
            self._flush()

    def _flush(self):
        with self._lock:
            payload = {
                'data': self._cache,
                'indexes': self.indexes
            }
            try:
                with open(self.path, 'w', encoding='utf-8') as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
            except Exception:
                pass

    def __getattr__(self, name: str) -> Collection:
        return Collection(name, self)

    def create_collection(self, name: str) -> Collection:
        with self._lock:
            if name not in self._cache:
                self._cache[name] = []
                self._flush()
            return Collection(name, self)

    def drop_collection(self, name: str) -> bool:
        with self._lock:
            if name in self._cache:
                del self._cache[name]
                self._flush()
                return True
            return False