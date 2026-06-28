# MicroDB

MicroDB is a tiny JSON database for Python.  
No SQL. No servers. No magic.

You just work with Python dictionaries. They get saved to disk automatically.  
That's it.

---

### Why

Sometimes you don't need PostgreSQL.  
Sometimes you just want to store a few settings, logs, or test data without writing `json.dump()` every time.

MicroDB gives you a thin wrapper over JSON — so you can focus on your code, not on file handling.

---

### Example

```python
from microdb import Storage

db = Storage('data.json')
db.users.insert({'name': 'Alex', 'age': 25})
user = db.users.find(name='Alex')



That's the whole idea. Nothing more.

What's inside
insert, find, update, delete — all the basics

Auto-generated IDs and timestamps

Indexes for faster lookups

Data stored in plain readable JSON

Optional GUI app if you prefer clicking over typing

Quick start

< bash
pip install microdb >

Or just copy microdb.py into your project. It's a single file.

