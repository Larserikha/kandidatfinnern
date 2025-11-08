#!/usr/bin/env python3
"""
Setup MCP configuration for Claude Desktop and ChatGPT Desktop
Automatically finds and updates MCP config files
"""
import json
import os
import sys
from pathlib import Path
import platform

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def get_project_path():
    """Get absolute path to project root"""
    return Path(__file__).parent.parent.resolve()

def get_mcp_config_paths():
    """Get paths to MCP config files based on OS"""
    system = platform.system()
    home = Path.home()
    
    config_paths = {}
    
    if system == "Darwin":  # macOS
        config_paths["claude_desktop"] = home / "Library/Application Support/Claude/claude_desktop_config.json"
        config_paths["chatgpt_desktop"] = home / "Library/Application Support/OpenAI/ChatGPT/desktop_app_config.json"
    elif system == "Linux":
        config_paths["claude_desktop"] = home / ".config/Claude/claude_desktop_config.json"
        config_paths["chatgpt_desktop"] = home / ".config/OpenAI/ChatGPT/desktop_app_config.json"
    elif system == "Windows":
        appdata = Path(os.getenv("APPDATA", ""))
        config_paths["claude_desktop"] = appdata / "Claude/claude_desktop_config.json"
        config_paths["chatgpt_desktop"] = appdata / "OpenAI/ChatGPT/desktop_app_config.json"
    
    return config_paths

def get_mcp_server_config(project_path: Path):
    """Generate MCP server configuration"""
    python_path = project_path / "venv" / "bin" / "python"
    server_path = project_path / "mcp_server.py"
    
    # On Windows, use python.exe
    if platform.system() == "Windows":
        python_path = project_path / "venv" / "Scripts" / "python.exe"
    
    return {
        "command": str(python_path),
        "args": [str(server_path)],
        "env": {}
    }

def update_mcp_config(config_path: Path, server_config: dict, app_name: str):
    """Update MCP config file with cv-rag server (preserves existing servers)"""
    # Read existing config or create new
    existing_servers = {}
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Preserve all existing servers
                if "mcpServers" in config:
                    existing_servers = config["mcpServers"].copy()
        except json.JSONDecodeError as e:
            print(f"⚠️  Warning: {config_path} contains invalid JSON: {e}")
            print(f"   Creating backup and starting fresh...")
            backup_path = config_path.with_suffix('.json.backup')
            config_path.rename(backup_path)
            config = {}
            existing_servers = {}
    else:
        config = {}
        existing_servers = {}
    
    # Ensure mcpServers exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Preserve all existing servers (except cv-rag which we'll update)
    for server_name, server_config_existing in existing_servers.items():
        if server_name != "cv-rag":
            config["mcpServers"][server_name] = server_config_existing
    
    # Check if cv-rag already exists
    if "cv-rag" in config["mcpServers"]:
        existing = config["mcpServers"]["cv-rag"]
        if existing.get("command") == server_config["command"]:
            print(f"✅ {app_name}: cv-rag server already configured correctly")
            # Show other servers if any
            other_servers = [s for s in config["mcpServers"].keys() if s != "cv-rag"]
            if other_servers:
                print(f"   Other servers in config: {', '.join(other_servers)}")
            return True
        else:
            print(f"⚠️  {app_name}: cv-rag server exists but with different path")
            print(f"   Updating cv-rag configuration...")
    
    # Add or update cv-rag server (preserving all other servers)
    config["mcpServers"]["cv-rag"] = server_config
    
    # Show what servers will be in the config
    all_servers = list(config["mcpServers"].keys())
    if len(all_servers) > 1:
        print(f"   Config will contain {len(all_servers)} servers: {', '.join(all_servers)}")
    
    # Write back to file
    try:
        # Create parent directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ {app_name}: Configuration updated successfully")
        print(f"   Config file: {config_path}")
        return True
    except Exception as e:
        print(f"❌ {app_name}: Failed to write config: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("MCP Configuration Setup")
    print("=" * 60)
    print()
    
    project_path = get_project_path()
    print(f"📁 Project path: {project_path}")
    
    # Check if venv exists
    venv_python = project_path / "venv" / "bin" / "python"
    if platform.system() == "Windows":
        venv_python = project_path / "venv" / "Scripts" / "python.exe"
    
    if not venv_python.exists():
        print("❌ Error: Virtual environment not found!")
        print(f"   Expected: {venv_python}")
        print()
        print("   Please run ./scripts/setup.sh first to create the virtual environment.")
        return 1
    
    print(f"✅ Virtual environment found: {venv_python}")
    print()
    
    # Get server configuration
    server_config = get_mcp_server_config(project_path)
    print("🔧 MCP Server Configuration:")
    print(f"   Command: {server_config['command']}")
    print(f"   Args: {server_config['args']}")
    print()
    
    # Get config file paths
    config_paths = get_mcp_config_paths()
    
    # Update configurations
    updated = []
    for app_name, config_path in config_paths.items():
        print(f"🔍 Checking {app_name}...")
        if config_path.exists():
            print(f"   Found config file: {config_path}")
            if update_mcp_config(config_path, server_config, app_name):
                updated.append(app_name)
        else:
            print(f"   ⚠️  Config file not found: {config_path}")
            print(f"      {app_name} may not be installed, or config file is in a different location")
        print()
    
    # Summary
    print("=" * 60)
    if updated:
        print("✅ Setup complete!")
        print()
        print("Updated configurations for:")
        for app in updated:
            print(f"  - {app}")
        print()
        print("📝 Next steps:")
        print("  1. Restart Claude Desktop / ChatGPT Desktop")
        print("  2. The cv-rag MCP server should now be available")
        print("  3. Test by asking: 'List all candidates' or 'Search for candidates with Azure experience'")
    else:
        print("⚠️  No MCP config files found")
        print()
        print("This could mean:")
        print("  - Claude Desktop / ChatGPT Desktop is not installed")
        print("  - Config files are in a different location")
        print()
        print("Manual setup:")
        print("  See mcp_config_examples/ for example configurations")
        print("  Add the cv-rag server configuration to your MCP config file")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

