# Google Sheets Batch Update Optimization

## Overview

Optimized Google Sheets writes using `batchUpdate` API to reduce API calls by 5-10x.

## Key Optimizations

### 1. Batch Updates
- **Before**: Each `update_bsr()` call = 1 API call
- **After**: All updates buffered, flushed in single `batchUpdate` call
- **Reduction**: 31 books = 1 API call instead of 31 calls (31x reduction)

### 2. Metadata Caching
- **Cache TTL**: 5 minutes
- **Cached Data**: Headers, max_rows, max_cols, avg_col
- **Benefit**: Avoids reading headers repeatedly

### 3. Write Only Changed Cells
- Updates are buffered and only flushed when needed
- Duplicate updates to same cell overwrite previous value
- No unnecessary writes

### 4. Optimized Reads
- `get_today_row()`: Reads only column A instead of all values
- `get_all_books()`: Uses cached headers when available
- `calculate_and_update_average()`: Reads only specific row instead of all values

## Usage

### Automatic Batch Updates

```python
from google_sheets_transposed import GoogleSheetsManager

manager = GoogleSheetsManager(credentials_path, spreadsheet_id)

# Updates are automatically buffered
for book in books:
    manager.update_bsr(book['col'], today_row, bsr_value, worksheet_name)

# Flush all buffered updates in one API call
manager.flush_batch_updates(worksheet_name)
```

### Manual Immediate Write

```python
# Write immediately (bypasses batch buffer)
manager.update_bsr(col, row, bsr_value, worksheet_name, batch=False)
```

## Performance Improvements

### Example: 31 Books Update

**Before (Individual Updates)**:
- 31 `update_cell()` calls = 31 API calls
- Plus 1 `update_cell()` for average = 32 total API calls

**After (Batch Updates)**:
- 31 updates buffered
- 1 `batchUpdate()` call for all BSR values = 1 API call
- 1 `batchUpdate()` call for average = 1 API call
- **Total: 2 API calls (16x reduction)**

### Cache Benefits

**Before**:
- `get_all_books()`: Reads all values every time
- `get_today_row()`: Reads all values every time
- `calculate_and_update_average()`: Reads all values every time

**After**:
- `get_all_books()`: Uses cached headers (reads only rows 2-4)
- `get_today_row()`: Reads only column A
- `calculate_and_update_average()`: Reads only specific row

## API Call Reduction

| Operation | Before | After | Reduction |
|-----------|--------|-------|-----------|
| 31 BSR updates | 31 calls | 1 call | 31x |
| Average update | 1 call | 1 call | Same |
| get_all_books() | Full read | Cached headers | ~80% faster |
| get_today_row() | Full read | Column A only | ~95% faster |
| **Total (31 books)** | **~35 calls** | **~3 calls** | **~12x reduction** |

## Implementation Details

### Batch Buffer Structure

```python
_batch_buffer = {
    'worksheet_name': {
        (row, col): value,
        (row, col): value,
        ...
    }
}
```

### Flush Process

1. Group updates by row
2. Build range strings (e.g., "B5:D5" for row 5, cols B-D)
3. Execute single `batch_update()` call
4. Clear buffer

### Cache Structure

```python
WorksheetMetadata(
    worksheet_name: str,
    max_rows: int,
    max_cols: int,
    headers: List[str],
    avg_col: Optional[int],
    cached_at: float
)
```

## Monitoring

Check batch buffer status:
```python
print(f"Buffered updates: {len(manager._batch_buffer)} worksheets")
for ws_name, updates in manager._batch_buffer.items():
    print(f"  {ws_name}: {len(updates)} updates")
```

## Best Practices

1. **Always flush after batch operations**:
   ```python
   # After processing all books
   manager.flush_batch_updates(worksheet_name)
   ```

2. **Use cache for repeated reads**:
   ```python
   books = manager.get_all_books(worksheet_name, use_cache=True)
   ```

3. **Invalidate cache when structure changes**:
   ```python
   from app.services.sheets_cache import get_metadata_cache
   get_metadata_cache().invalidate(worksheet_name)
   ```

