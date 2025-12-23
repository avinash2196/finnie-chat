# Scripts & Utilities

This folder contains utility scripts for development, testing, and database management.

## 📁 Folder Structure

### `db_utils/` - Database Utilities
Scripts for managing the SQLite database and testing data.

| Script | Purpose |
|--------|---------|
| `check_db.py` | Inspect database contents and verify data integrity |
| `demo_database.py` | Set up demo database with sample data |
| `create_user_001.py` | Create test user (user_001) with sample holdings |
| `verify_user_001.py` | Verify user_001 data is correctly stored |
| `verify_all_users.py` | Check all users in the database |
| `quick_check.py` | Quick database health check |
| `resync_test.py` | Test portfolio synchronization |
| `test_sync.py` | Sync test for external providers |

### Root Scripts
| Script | Purpose |
|--------|---------|
| `test_new_features.py` | Test newly implemented features |
| `test_rag_improvement.py` | Test RAG system improvements |

## 🚀 Usage Examples

### Check Database
```bash
cd C:\Users\avina\Codes\finnie-chat
.\venv\Scripts\python.exe scripts\db_utils\check_db.py
```

### Create Test User
```bash
.\venv\Scripts\python.exe scripts\db_utils\create_user_001.py
```

### Verify Data
```bash
.\venv\Scripts\python.exe scripts\db_utils\verify_all_users.py
```

### Test Portfolio Sync
```bash
.\venv\Scripts\python.exe scripts\db_utils\test_sync.py
```

## 📝 Notes

- All scripts assume the virtual environment is activated
- Database scripts work with `finnie_chat.db` in the project root
- Test scripts may require the backend server to be running
