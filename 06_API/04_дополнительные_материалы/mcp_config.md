# MCP-серверы для Cursor — готовая конфигурация

> Файл `.cursor/mcp.json` в корне проекта:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/your/project"]
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "YOUR_KEY"
      }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxxxxxxxxxx"
      }
    },
    "sqlite": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite", "data.db"]
    }
  }
}
```

## Как подключить
1. Создай файл `.cursor/mcp.json`
2. Вставь конфиг выше
3. Замени пути и ключи на свои
4. Перезапусти Cursor
5. В чате агента появятся новые инструменты (поиск, файлы, GitHub)

## Где взять ключи
- **Brave Search**: https://brave.com/search/api/ (бесплатно 2000 запросов/мес)
- **GitHub**: Settings → Developer settings → Personal access tokens
- **Для SQLite**: ключ не нужен, укажи путь к .db файлу
