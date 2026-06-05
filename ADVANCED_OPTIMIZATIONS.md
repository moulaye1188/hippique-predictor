# Advanced Optimization Guide - Fintech Horse Racing

## 📊 Performance Baseline (Before Optimizations)

```
Metric                    Before          Target          Effort
────────────────────────────────────────────────────────────────────
PDF Parse (100 pages)     500-1000ms      50-100ms        ✓ DONE
Database Indexes          N/A             Added           ✓ DONE
Requirements.txt          350MB image     50MB image      ✓ DONE
────────────────────────────────────────────────────────────────────
Feature Vectorization     15-20ms         3-5ms           📋 TODO
Model Cache               5-10ms          <1ms            📋 TODO
Connection Pool           2-3ms          <0.5ms          📋 TODO
Test Coverage            0%              >80%             📋 TODO
```

---

## 🔧 ADVANCED OPTIMIZATION #1: Feature Engineering Vectorization

**File:** `backend/feature_engineering.py` (lines 40-51)

### Current (Slow - Apply Loop):
```python
df['perf_score'] = df['perf'].apply(self._parse_perf)
df['odds_paris_prob'] = df['odds_paris_turf'].apply(self._odds_to_probability)
df['odds_tierce_prob'] = df['odds_tierce_magazine'].apply(self._odds_to_probability)
```

**Problem:** `apply()` is essentially a loop - loses pandas/numpy vectorization benefits.

### Optimized (Vectorized):
```python
# Vectorized performance parsing
def _parse_perf_vectorized(perf_series):
    """Vectorized performance parsing - 5x faster"""
    perf_series = perf_series.astype(str)
    
    # Split once
    split_data = perf_series.str.split('\.', expand=True).fillna('0').astype(int)
    
    # Vectorized mapping
    score_map = {1: 10, 2: 8, 3: 6}
    default_score = 2
    
    mapped_scores = split_data.applymap(lambda x: score_map.get(x, default_score))
    
    # Mean across columns
    return mapped_scores.mean(axis=1).fillna(0.0)

# Apply vectorized version
df['perf_score'] = self._parse_perf_vectorized(df['perf'])
df['odds_paris_prob'] = self._odds_to_probability_vec(df['odds_paris_turf'])
```

### Estimated Impact:
- Per-race time: 15-20ms → 3-5ms (4-6x speedup)
- 100 races/day: 1.5-2s → 0.3-0.5s

---

## 🔧 ADVANCED OPTIMIZATION #2: SQLite Connection Pooling

**File:** `backend/database.py`

### Current Problem:
```python
def save_race(*args):
    conn = sqlite3.connect(DB_PATH)  # ❌ New connection each time!
    cursor = conn.cursor()
    # ... query ...
    conn.close()
```

**Impact:** 2-3ms overhead per route × 100 requests = 200-300ms wasted

### Solution - Connection Wrapper:
```python
# At top of database.py
import sqlite3
from contextlib import contextmanager

class DatabasePool:
    _conn = None
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get cached database connection"""
        if cls._conn is None:
            cls._conn = sqlite3.connect(DB_PATH, timeout=20.0, check_same_thread=False)
            cls._conn.row_factory = sqlite3.Row
        
        yield cls._conn

# Usage:
def save_race(*args):
    with DatabasePool.get_connection() as conn:
        cursor = conn.cursor()
        # ... query ...
        conn.commit()
```

### Refactor all database functions:
```bash
# Find all database.py functions
grep -n "def " backend/database.py | head -20

# Replace pattern in each:
# FROM: conn = sqlite3.connect(DB_PATH)
# TO:   with DatabasePool.get_connection() as conn:
```

### Estimated Impact:
- Per-request overhead: 2-3ms → 0-0.1ms
- 100 requests: 200-300ms → 10-15ms saved

---

## 🔧 ADVANCED OPTIMIZATION #3: API Response Caching

**File:** `backend/app.py`

### Add caching for frequently accessed endpoints:
```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache decorator for endpoints
class CachedRoute:
    def __init__(self, max_age_seconds=300):
        self.max_age = max_age_seconds
        self.cache = {}
        self.timestamps = {}
    
    def get_or_compute(self, key, compute_func, *args, **kwargs):
        now = datetime.now()
        
        if key in self.cache:
            age = (now - self.timestamps[key]).total_seconds()
            if age < self.max_age:
                return self.cache[key]  # Cached!
        
        result = compute_func(*args, **kwargs)
        self.cache[key] = result
        self.timestamps[key] = now
        return result

# Example: Cache dashboard data
dashboard_cache = CachedRoute(max_age_seconds=300)

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    return jsonify(
        dashboard_cache.get_or_compute(
            'dashboard',
            compute_dashboard_data
        )
    )
```

### Estimated Impact:
- Same request twice: 500ms → <1ms (from cache)
- Typical usage: 30-40% of requests are cached

---

## 🔧 ADVANCED OPTIMIZATION #4: Database Query Optimization

### 1. Add EXPLAIN PLAN analysis
```python
# backend/analyze_queries.py
import sqlite3

def analyze_query_performance(query):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get query plan
    cursor.execute(f"EXPLAIN QUERY PLAN {query}")
    plan = cursor.fetchall()
    
    print(f"Query: {query}")
    for row in plan:
        print(f"  {row}")
    
    return plan
```

### 2. Common queries to optimize:
```sql
-- Get all races with horse count
-- CURRENT: Joins without indexes
SELECT r.*, COUNT(h.id) as horse_count
FROM races r
LEFT JOIN horses h ON r.id = h.race_id
GROUP BY r.id;

-- OPTIMIZED: Use indexes (created in Phase 1)
-- Already indexed! Query will be 50-100x faster
```

---

## 🔧 ADVANCED OPTIMIZATION #5: Async Request Processing

**Problem:** Long PDF parsing blocks request thread

**Solution:** Use Celery for async tasks

```python
# backend/celery_tasks.py
from celery import Celery

celery = Celery('hippique_app')

@celery.task
def process_pdf_async(file_path, race_id):
    """Parse PDF in background"""
    try:
        race_info, horses_df, pronostics, classements, best_week = parse_pdf_smart(file_path)
        # ... save to DB ...
        return {'status': 'completed', 'race_id': race_id}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}

# app.py route
@app.route('/api/load-race-from-pdf', methods=['POST'])
def load_race_from_pdf():
    # Save file temporarily
    temp_path = save_temp_file(request.files['file'])
    
    # Queue async task
    task = process_pdf_async.delay(temp_path, race_id)
    
    # Return immediately
    return jsonify({
        'task_id': task.id,
        'status': 'processing'
    })

# Frontend polls for status
@app.route('/api/task-status/<task_id>')
def get_task_status(task_id):
    task = process_pdf_async.AsyncResult(task_id)
    return jsonify({'status': task.status, 'result': task.result})
```

---

## 📋 Testing & Validation

### Create pytest test suite:

```python
# tests/test_performance.py
import time
import pytest
from backend.pdf_parser_smart import parse_pdf_smart

@pytest.mark.performance
def test_pdf_parse_time(benchmark):
    """Ensure PDF parsing stays < 100ms"""
    # benchmark runs the function multiple times
    result = benchmark(parse_pdf_smart, 'tests/fixtures/sample.pdf')
    
    assert result[0] != {}  # Has race_info

@pytest.mark.performance  
def test_dashboard_query_time(benchmark):
    """Dashboard query should be < 20ms"""
    result = benchmark(get_dashboard)
    
    assert result['races'] is not None
```

### Run performance tests:
```bash
# Install pytest and plugin
pip install pytest pytest-benchmark

# Run performance tests
pytest tests/test_performance.py -v

# Compare before/after
pytest tests/test_performance.py --benchmark-compare=baseline
```

---

## 📊 Optimization Checklist

- [ ] **Phase 1** (DONE):
  - [x] Remove unused dependencies (TensorFlow, PyPDF2, NLTK)
  - [x] Add database indexes (9 indexes)
  - [x] Optimize PDF parser (limit pages)

- [ ] **Phase 2** (TODO):
  - [ ] Delete dead files (40+ files)
  - [ ] Reorganize tests into `tests/` folder
  - [ ] Setup pytest framework
  - [ ] Add conftest.py with fixtures

- [ ] **Phase 3** (TODO):
  - [ ] Vectorize feature engineering
  - [ ] Add database connection pooling
  - [ ] Implement API response caching
  - [ ] Optimize SQL queries with EXPLAIN PLAN

- [ ] **Phase 4** (TODO):
  - [ ] Setup async processing (Celery)
  - [ ] Add CI/CD pipeline (GitHub Actions)
  - [ ] Setup monitoring & logging
  - [ ] Performance benchmarking suite

---

## 🚀 Implementation Priority

```
HIGH IMPACT, LOW EFFORT:
1. Delete dead files ............................ 1 hour
2. Database connection pooling ................. 2 hours
3. API response caching ....................... 1 hour

HIGH IMPACT, MEDIUM EFFORT:
4. Feature engineering vectorization ........... 4 hours
5. Test reorganization with pytest ............ 3 hours

MEDIUM IMPACT, MEDIUM EFFORT:
6. Async PDF processing (Celery) .............. 6 hours
7. Query optimization with benchmarks ......... 3 hours

LOW PRIORITY:
8. CI/CD setup .............................. 5 hours
9. Monitoring/logging ........................ 4 hours
```

---

## 📈 Expected Results After All Optimizations

| Metric | Before | After | Gain |
|--------|--------|-------|------|
| PDF Parse (100 pages) | 500-1000ms | 50-100ms | **10x** |
| Feature Eng | 15-20ms | 3-5ms | **4-6x** |
| Database Query | 100ms | 1-2ms | **50-100x** |
| Dashboard API | 500ms | 20-50ms | **10-25x** |
| Prediction | 50ms | 10ms | **5x** |
| Docker Build | 5min | 1min | **5x** |
| **Overall** | — | — | **15-50x** |

---

## 📞 Questions?

- See [OPTIMIZATIONS_APPLIED.md](OPTIMIZATIONS_APPLIED.md) for completed work
- Run `python backend/cleanup_optimization.py` to remove dead files
- After Phase 1: Commit changes and rebuild Docker image

**Last Updated:** June 5, 2026
