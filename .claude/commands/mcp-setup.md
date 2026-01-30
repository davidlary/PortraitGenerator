# MCP Setup Command

Initialize and test MCP (Model Context Protocol) server connections.

## Purpose

This command helps you set up and verify MCP servers for:
1. **Memory Server**: Persistent context across sessions
2. **Filesystem Server**: Enhanced file operations (optional)

## Prerequisites

- Node.js and npm installed (for npx)
- `.mcp.json` file exists in project root
- Internet connection (to download MCP servers)

## Actions

### 1. Verify MCP Configuration

Check that `.mcp.json` exists and is valid:
```bash
cat .mcp.json | jq empty
```

### 2. Test Memory Server Connection

Try to connect to memory server:
```
mcp__memory__create_entities([{
  name: "Setup_Test",
  type: "test",
  observations: ["MCP memory server connection test"]
}])
```

Expected: Success confirmation

### 3. Verify Memory Storage

Check if entity was stored:
```
mcp__memory__search_nodes("Setup_Test")
```

Expected: Should return the test entity

### 4. Create Initial Project Context

Store project information in memory:
```
mcp__memory__create_entities([
  {
    name: "{{PROJECT_NAME}}",
    type: "project",
    observations: [
      "Framework: Context-Preserving v4.1.0",
      "Created: {{DATE}}",
      "Purpose: {{PROJECT_PURPOSE}}"
    ]
  }
])
```

### 5. Test Semantic Search

Query memory to verify search works:
```
mcp__memory__search_nodes("project")
```

Expected: Should return project entity

### 6. Display Setup Summary

```
╔═══════════════════════════════════════════════════════════════════════╗
║ MCP SETUP VERIFICATION                                                 ║
╚═══════════════════════════════════════════════════════════════════════╝

📡 Memory Server:
{{MEMORY_SERVER_STATUS}}

🔍 Search Test:
{{SEARCH_TEST_RESULT}}

💾 Storage Path:
.claude/memory/

✅ Setup Complete!

Next Steps:
1. Use mcp__memory__create_entities() to store module summaries
2. Use mcp__memory__search_nodes() to retrieve context
3. Use mcp__memory__create_relations() to link modules

Example Usage:
```
# Store module completion
mcp__memory__create_entities([{
  name: "Module_1.2_Authentication",
  type: "module",
  observations: ["Complete", "Tests passing", "250 lines"]
}])

# Retrieve in next session
mcp__memory__search_nodes("authentication")
```

╚═══════════════════════════════════════════════════════════════════════╝
```

## Troubleshooting

If memory server doesn't connect:

1. **Check npx is available**:
   ```bash
   npx --version
   ```

2. **Try manual connection**:
   ```bash
   npx -y @anthropic/mcp-server-memory
   ```

3. **Check Claude Code version**:
   - MCP support requires Claude Code with MCP capability
   - Update if necessary

4. **Enable debug logging**:
   - Launch Claude Code with `--mcp-debug` flag
   - Check debug output for connection errors

5. **Verify storage directory**:
   ```bash
   ls -la .claude/memory/
   ```
   - Should be created automatically
   - Check permissions if issues

## Variables

- `{{PROJECT_NAME}}`: Your project name
- `{{DATE}}`: Current date
- `{{PROJECT_PURPOSE}}`: Project description
- `{{MEMORY_SERVER_STATUS}}`: Connection status
- `{{SEARCH_TEST_RESULT}}`: Search test outcome

## Expected Outcome

After running this command:
- ✅ MCP memory server connected
- ✅ Test entities stored and retrieved
- ✅ Project context initialized
- ✅ Ready for automatic context preservation
