# GovStack API Test Suite - Quick Reference

## 🚀 Quick Start

```bash
cd /home/ubuntu/govstack/tests/integration
python test_runner_v2.py
```

## 📊 Current Results

```
Total: 58 tests
✅ Pass: 26 (44.8%)
❌ Fail: 21 (36.2%)
⏭️  Skip: 11 (19.0%)
```

## 🔑 API Keys

```bash
# Test Key (read/write)
GOVSTACK_TEST_API_KEY=63b528c7-2b42-4028-a1b1-ec62c56309f6

# Admin Key
GOVSTACK_ADMIN_API_KEY=b689ccc1-d925-4c4e-871a-379fcd79f269
```

## 🌐 Endpoints

**Base URL:** https://govstack-api.think.ke/

## 🐛 Known Issues

### Critical (Blocking)
1. ❌ `POST /collection-stats/` → 500 error (blocks 13 tests)
2. ❌ All `/chat/ratings/*` → Router conflict (blocks 5 tests)

### High Priority
3. ⚠️ `GET /chat/ratings/stats` → Route ordering issue
4. ⚠️ `GET /documents/indexing-jobs` → Route ordering issue
5. ⚠️ `GET /chat/{session_id}` → 500 error

## ✅ Working Endpoints

```
100% - Audit Logs (4/4)
100% - Transcriptions (1/1)
67%  - Webpages (4/6)
67%  - Crawler (2/3)
60%  - Chat (3/5)
```

## 📁 Files

```
test_runner_v2.py              # Main test suite
config.py                      # Configuration
api_client.py                  # HTTP client
API_ISSUES_DISCOVERED.md       # Bug report
README_V2.md                   # Full documentation
EXECUTIVE_SUMMARY.md           # Summary report
```

## 🔧 Configuration

Edit `.env`:
```bash
GOVSTACK_BASE_URL=https://govstack-api.think.ke
GOVSTACK_TEST_API_KEY=your-key
GOVSTACK_ADMIN_API_KEY=your-admin-key
SKIP_CLEANUP=true
LOG_LEVEL=INFO
```

## 📝 Logs

```bash
# View logs
tail -f logs/test_run_*.log

# Search errors
grep "FAILED" logs/test_run_*.log
```

## 🏃 Run Options

```bash
# All tests
python test_runner_v2.py

# With cleanup
SKIP_CLEANUP=false python test_runner_v2.py

# Debug mode
LOG_LEVEL=DEBUG python test_runner_v2.py
```

## 📚 Documentation

- **Full Docs:** [README_V2.md](./README_V2.md)
- **Bug Report:** [API_ISSUES_DISCOVERED.md](./API_ISSUES_DISCOVERED.md)
- **Summary:** [EXECUTIVE_SUMMARY.md](./EXECUTIVE_SUMMARY.md)

## 🎯 Test Categories

1. ✅ Health Check
2. 📦 Collections (6 tests)
3. 📄 Documents (8 tests)
4. 🔄 Indexing (4 tests)
5. 🌐 Webpages (6 tests)
6. 🕷️ Crawler (3 tests)
7. 💬 Chat (5 tests)
8. ⭐ Ratings (5 tests)
9. 📋 Audit (4 tests)
10. 🎙️ Transcriptions (1 test)

## 💡 Tips

- Run against live API: https://govstack-api.think.ke/
- Tests use THiNK organization (https://think.ke)
- Set SKIP_CLEANUP=true to keep test data
- Check logs/ for detailed execution traces
- See API_ISSUES_DISCOVERED.md for known bugs

## 🆘 Troubleshooting

**"Configuration not valid"**
```bash
cat .env  # Check file exists
```

**"API health check failed"**
```bash
curl https://govstack-api.think.ke/health
```

**"Collection ID not found"**
- Known issue: Collection creation returns 500
- Many tests cascade from this failure

## 📞 Support

- **Organization:** Tech Innovators Network (THiNK)
- **Website:** https://think.ke
- **Test Logs:** `tests/integration/logs/`
- **Issues:** See API_ISSUES_DISCOVERED.md

---

**Version:** 2.0 | **Updated:** 2025-11-07
