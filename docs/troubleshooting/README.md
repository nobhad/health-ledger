# Troubleshooting Guide

**Last Updated:** December 7, 2025

Complete troubleshooting and debugging guide for the Genetic Profile Database application.

## Documentation

- **[DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md)** - Comprehensive debugging guide covering:
  - Logging system
  - Database debugging
  - API debugging
  - Frontend debugging
  - Performance debugging

- **[DEBUGGING_JAVASCRIPT.md](DEBUGGING_JAVASCRIPT.md)** - JavaScript-specific debugging:
  - Browser console debugging
  - Debug logging system
  - Common JavaScript errors
  - Browser extension issues

- **[COMMON_ISSUES.md](COMMON_ISSUES.md)** - Quick reference for common problems:
  - HTTP 403 errors
  - Port conflicts
  - Database connection issues
  - Module import errors

## Quick Reference

### Database Connection Issues

```bash
# Check database file
ls -la genetic_profile.db

# Remove lock files (if safe)
rm genetic_profile.db-shm genetic_profile.db-wal
```

### Port Conflicts

```bash
# Find process using port
lsof -i:5000

# Kill process
lsof -ti:5000 | xargs kill -9
```

### Module Not Found

```bash
pip3 install -r requirements.txt
```

### View Logs

```bash
# Live logs
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log
```

## Getting Help

1. Check the relevant guide above
2. Review server logs in `logs/app.log`
3. Check browser console for JavaScript errors
4. Verify database integrity: `python3 -c "from database_manager import GeneticProfileDB; db = GeneticProfileDB(); db.verify_integrity(); db.close()"`
