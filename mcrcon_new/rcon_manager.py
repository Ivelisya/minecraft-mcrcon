import re
import toml
import json
from mcrcon import MCRcon
import logging

class RCONManager:
    def __init__(self, config_path='config/config.toml', ban_file_path='data/banned_players.json'):
        self.config_path = config_path
        self.ban_file_path = ban_file_path
        self.host = None
        self.port = None
        self.password = None
        self.rcon = None
        self.banned_data = {"players": [], "ips": []}
        self.load_config()
        self.load_ban_list_from_file()

    def load_config(self):
        try:
            settings = toml.load(self.config_path)
            self.host = settings['server']['host']
            self.port = int(settings['server']['port'])
            self.password = settings['server']['password']
        except FileNotFoundError:
            logging.error(f"配置文件未找到: {self.config_path}")
            # 在这里可以考虑生成一个默认配置
        except (KeyError, ValueError) as e:
            logging.error(f"配置文件格式错误: {e}")

    def connect(self):
        if not all([self.host, self.port, self.password]):
            return False, "服务器配置不完整"
        
        try:
            self.rcon = MCRcon(self.host, self.password, self.port)
            self.rcon.connect()
            return True, "成功连接到服务器"
        except Exception as e:
            logging.error(f"连接 RCON 服务器失败: {e}")
            return False, f"连接失败: {e}"

    def disconnect(self):
        if self.rcon:
            try:
                self.rcon.disconnect()
            except Exception as e:
                logging.error(f"断开 RCON 连接时出错: {e}")
        self.rcon = None

    def command(self, cmd):
        if not self.rcon:
            status, msg = self.connect()
            if not status:
                return msg

        try:
            response = self.rcon.command(cmd)
            return response
        except Exception as e:
            logging.error(f"执行命令 '{cmd}' 失败: {e}")
            return f"命令执行失败: {e}"
        finally:
            self.disconnect()

    def get_server_status(self):
        """获取服务器状态，包括在线人数和玩家列表"""
        response = self.command('list')
        if response is None or "失败" in response:
            return {"online": False, "player_count": 0, "players": []}

        try:
            # 解析 'There are 1 of a max of 20 players online: player1' 这样的字符串
            parts = response.split(':')
            player_count_str = re.search(r'(\d+)\s+of\s+a\s+max', parts[0])
            player_count = int(player_count_str.group(1)) if player_count_str else 0
            
            players = []
            if player_count > 0 and len(parts) > 1:
                players = [p.strip() for p in parts[1].split(',')]

            return {"online": True, "player_count": player_count, "players": players}
        except (IndexError, ValueError, AttributeError) as e:
            logging.error(f"解析 'list' 命令响应失败: {response} - 错误: {e}")
            # 尝试另一种解析方式，针对 '§6default§r: player1, player2'
            try:
                match_names = re.findall(r'§6default§r: (.*)', response)
                if match_names:
                    name_list = [re.sub(r'§.', '', name) for name in match_names[0].split(',')]
                    return {"online": True, "player_count": len(name_list), "players": name_list}
            except Exception as inner_e:
                 logging.error(f"再次解析 'list' 命令响应失败: {response} - 错误: {inner_e}")

            return {"online": True, "player_count": 0, "players": []} # 至少服务器是在线的

    def get_whitelist(self):
        """获取白名单列表（更健壮的版本）"""
        response = self.command('whitelist list')
        # 检查响应是否有效且包含冒号，以避免空列表时的IndexError
        if response and "whitelisted players" in response and ":" in response:
            try:
                players_str = response.split(':', 1)[1]
                players = players_str.strip().split(',')
                return [p.strip() for p in players if p.strip()]
            except IndexError:
                return []  # 如果分割失败，返回空列表
        return [] # 如果响应不符合预期格式，返回空列表

    def add_to_whitelist(self, player_name):
        """将玩家添加到白名单"""
        return self.command(f'whitelist add {player_name}')

    def remove_from_whitelist(self, player_name):
        """将玩家从白名单移除"""
        return self.command(f'whitelist remove {player_name}')

    def load_ban_list_from_file(self):
        """从文件加载封禁列表"""
        try:
            with open(self.ban_file_path, 'r', encoding='utf-8') as f:
                self.banned_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.save_ban_list_to_file() # 如果文件不存在或无效，则创建一个新的

    def save_ban_list_to_file(self):
        """将封禁列表保存到文件"""
        try:
            with open(self.ban_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.banned_data, f, indent=2)
        except IOError as e:
            logging.error(f"无法写入封禁列表文件: {e}")

    def get_ban_list(self):
        """从内存直接获取封禁列表"""
        return self.banned_data

    def ban_player(self, player_name):
        """封禁玩家并立即更新本地文件"""
        response = self.command(f'ban {player_name}')
        if player_name and player_name not in self.banned_data["players"]:
            self.banned_data["players"].append(player_name)
            self.save_ban_list_to_file()
        return response

    def pardon_target(self, target_name):
        """解封玩家或IP并立即更新本地文件"""
        if not target_name:
            return "目标不能为空"
            
        ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        if ip_pattern.match(target_name):
            response = self.command(f'pardon-ip {target_name}')
            if target_name in self.banned_data["ips"]:
                self.banned_data["ips"].remove(target_name)
        else:
            response = self.command(f'pardon {target_name}')
            if target_name in self.banned_data["players"]:
                self.banned_data["players"].remove(target_name)
            
        self.save_ban_list_to_file()
        return response

    def op_player(self, player_name):
        """授予玩家OP权限"""
        return self.command(f'op {player_name}')

    def deop_player(self, player_name):
        """撤销玩家OP权限"""
        return self.command(f'deop {player_name}')
