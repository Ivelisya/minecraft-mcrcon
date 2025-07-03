# Minecraft RCON 管理工具

这是一个使用 Python 开发的 Minecraft 服务器 RCON 管理工具集，它允许您通过命令行或图形用户界面（GUI）来管理您的 Minecraft 服务器。

## 功能

-   **命令行界面 (`command.py`)**: 一个菜单驱动的工具，用于执行常见的服务器命令，如更改游戏模式、传送玩家、给予物品、管理玩家（封禁/踢出）等。
-   **图形用户界面 (`visualization.py`)**: 一个使用 Tkinter 构建的 GUI 应用，提供了与命令行版本相同的大部分功能，操作更直观。
-   **自动化脚本 (`automation.py`)**: 一个在后台运行的脚本，用于：
    -   监控玩家的加入和离开，并发送欢迎消息。
    -   定期自动清理服务器上的掉落物。
    -   启动 GUI 管理界面。
-   **共享工具模块 (`utils.py`)**: 包含所有脚本共享的辅助函数，如加载配置、连接到 RCON 等。
-   **配置文件 (`config/config.toml`)**: 用于配置您的服务器地址、RCON 端口和密码。

## 项目结构

```
.
├── config/
│   └── config.toml
├── log/
│   └── server.log
├── mcrcon_py/
│   ├── automation.py
│   ├── command.py
│   ├── id.txt
│   ├── utils.py
│   └── visualization.py
├── joined_players.txt
├── quickly_command.py  (建议删除)
└── README.md
```

## 安装

1.  确保您已经安装了 Python 3。
2.  安装所需的依赖库：
    ```bash
    pip install mcrcon toml
    ```

## 使用方法

### 1. 配置服务器

编辑 `config/config.toml` 文件，填入您的 Minecraft 服务器的 RCON 信息：

```toml
[server]
host = "YOUR_SERVER_IP"
port = 25575
password = "YOUR_RCON_PASSWORD"
```

### 2. 运行工具

您可以根据需要选择运行以下任一脚本：

-   **运行自动化和 GUI:**

    ```bash
    python mcrcon_py/automation.py
    ```

    这将启动玩家监控、物品清理，并同时打开 GUI 管理窗口。

-   **仅运行命令行工具:**

    ```bash
    python mcrcon_py/command.py
    ```

    这将在您的终端中启动一个菜单，让您可以选择并执行各种服务器命令。

-   **仅运行 GUI 工具:**
    ```bash
    python mcrcon_py/visualization.py
    ```
    这将直接打开 GUI 管理窗口，而不运行后台自动化任务。

## 注意

-   请确保您的 Minecraft 服务器已经启用了 RCON，并且防火墙设置允许连接到 RCON 端口。
-   日志文件将记录在 `log/server.log` 中。
-   `quickly_command.py` 是一个功能有限的旧脚本，建议删除以避免混淆。
