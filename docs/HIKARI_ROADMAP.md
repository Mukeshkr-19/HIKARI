# HIKARI Enhancement Roadmap

## Current Status
✅ Working: Multi-agent system, Voice I/O, Memory, Knowledge Graph, Scheduler
✅ Added: Ollama/Gemma 4 as ULTIMATE fallback

## Features to Add (from JARVIS + Similar Projects)

### Priority 1: Desktop Awareness
- Screen capture capability
- OCR for reading screen content
- Window/activity detection

### Priority 2: Browser Automation  
- Web browsing capability
- Form filling
- Data extraction

### Priority 3: MCP Integration
- MCP server support (like JARVIS)
- Tool plugins system

### Priority 4: Workflow Automation
- Cron-based task execution
- File watching automation
- Conditional triggers

### Priority 5: Advanced Features
- Multi-device sidecar (like JARVIS)
- Visual dashboard
- Goal/OKR tracking

## Implementation Notes

### Desktop Awareness (Priority 1)
- Use `mss` + `pytesseract` for screenshots
- Track active window with `pygetwindow` or ` Quartz` (macOS)
- Analyze screen for context awareness

### Browser Automation (Priority 2)
- Use Playwright/Selenium for browser control
- Or use CDP (Chrome DevTools Protocol)

### MCP Integration (Priority 3)
- Implement MCP client to connect to servers
- Support filesystem, memory, GitHub, slack servers

### Quick Wins
1. Add search_browse tool to agents
2. Add screenshot capability
3. Add system_tray for background running
4. Add cron-like scheduler for automated tasks
