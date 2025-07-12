import json
from pathlib import Path
from nicegui import ui
from mcrcon_new.rcon_manager import RCONManager

# --- 全局状态和管理器 ---
rcon_manager = RCONManager()
# 用于UI回调的共享对象
rcon_manager.ui_update_callbacks = {}

# --- 数据加载 ---
def load_items():
    
    """从 data/items.json 安全地加载物品数据"""
    items_map = {}
    
    
    try:
        data_path = Path(__file__).parent / 'data/items.json'
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 创建中文名到ID的映射
            if 'items' in data:
                items_map = {item['name']: item['id'] for item in data['items']}
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error loading data: {e}") # 打印错误以供调试
    return items_map

item_map = load_items()

# --- 核心逻辑 ---
def execute_command_with_feedback(command: str):
    """执行命令并根据响应提供用户反馈"""
    if not command:
        ui.notify('命令不能为空!', type='warning', position='bottom')
        return
    response = rcon_manager.command(command)
    
    
    fail_keywords = ['failed', 'nothing', 'unknown', 'incorrect', 'not found', 'invalid']
    if any(keyword in response.lower() for keyword in fail_keywords):
        ui.notify(f"命令可能已失败: {response}", type='negative', position='bottom', multi_line=True)
    else:
        ui.notify(f"命令已发送: {response}", type='positive', position='bottom', multi_line=True)
    return response

# --- 页面内容定义 ---

def dashboard_page():   
    """仪表盘页面"""
    ui.label('仪表盘').classes('text-h4 q-mb-md text-grey-8')

    def update_ui():
        status = rcon_manager.get_server_status()
        status_card.clear()
        with status_card:
            if status['online']:
                ui.icon('check_circle', color='positive', size='lg').classes('q-mr-md')
                with ui.column():
                    ui.label('服务器状态').classes('text-subtitle2')
                    ui.label('在线').classes('text-h6 font-weight-bold text-positive')
            else:
                ui.icon('error', color='negative', size='lg').classes('q-mr-md')
                with ui.column():
                    ui.label('服务器状态').classes('text-subtitle2')
                    ui.label('离线').classes('text-h6 font-weight-bold text-negative')

        player_count_card.clear()
        with player_count_card:
            ui.icon('people', color='blue-grey-5', size='lg').classes('q-mr-md')
            with ui.column():
                ui.label('在线玩家').classes('text-subtitle2')
                ui.label(str(status['player_count'])).classes('text-h6 font-weight-bold')

        player_list.clear()
        with player_list:
            if status['players']:
                for player in status['players']:
                    with ui.item().classes('rounded-borders q-mb-sm bg-grey-2'):
                        with ui.item_section().props('avatar'):
                            ui.icon('person', color='primary')
                        with ui.item_section():
                            ui.label(player).classes('font-weight-medium')
            else:
                with ui.row().classes('items-center text-grey-6'):
                    ui.icon('info', size='sm').classes('q-mr-sm')
                    ui.label('当前没有玩家在线')

    with ui.row().classes('w-full q-col-gutter-md q-mb-md'):
        status_card = ui.card().classes('col-6 row items-center justify-center q-pa-md').style('min-height: 120px')
        player_count_card = ui.card().classes('col-6 row items-center justify-center q-pa-md').style('min-height: 120px')

    with ui.card().classes('w-full'):
        with ui.card_section():
            ui.label('在线玩家列表').classes('text-h6')
        ui.separator()
        player_list = ui.list().classes('q-pa-md')

    ui.timer(5.0, update_ui, once=False)
    update_ui()

def players_page():
    """玩家管理页面"""
    ui.label('玩家管理').classes('text-h4 q-mb-md text-grey-8')

    selects_to_update = []

    def get_player_list():
        return rcon_manager.get_server_status().get('players', [])

    initial_players = get_player_list()

    def ban_and_update(player_name):
        rcon_manager.ban_player(player_name)
        if 'ban_list' in rcon_manager.ui_update_callbacks:
            rcon_manager.ui_update_callbacks['ban_list']()

    with ui.grid(columns=2).classes('w-full q-col-gutter-md'):
        with ui.column().classes('w-full'):
            with ui.card().classes('w-full'):
                with ui.card_section():
                    ui.label('快速操作').classes('text-h6')
                ui.separator()
                with ui.card_section():
                    player_quick = ui.select(options=initial_players, label='选择玩家').classes('w-full')
                    selects_to_update.append(player_quick)
                    with ui.row().classes('q-mt-md q-gutter-sm'):
                        ui.button('杀死', on_click=lambda: execute_command_with_feedback(f'kill {player_quick.value}'), color='red-6').props('icon=medical_services')
                        ui.button('踢出', on_click=lambda: execute_command_with_feedback(f'kick {player_quick.value}'), color='orange-6').props('icon=logout')
                        ui.button('封禁', on_click=lambda: ban_and_update(player_quick.value), color='deep-orange-7').props('icon=gavel')
                        ui.button('清空背包', on_click=lambda: execute_command_with_feedback(f'clear {player_quick.value}'), color='grey-7').props('icon=delete_sweep')

            with ui.card().classes('w-full q-mt-md'):
                with ui.card_section():
                    ui.label('管理员权限').classes('text-h6')
                ui.separator()
                with ui.card_section():
                    player_op = ui.select(options=initial_players, label='选择玩家').classes('w-full')
                    selects_to_update.append(player_op)
                    with ui.row().classes('q-mt-md q-gutter-sm'):
                        ui.button('授予OP', on_click=lambda: rcon_manager.op_player(player_op.value), color='positive')
                        ui.button('撤销OP', on_click=lambda: rcon_manager.deop_player(player_op.value), color='negative')

            with ui.card().classes('w-full q-mt-md'):
                with ui.card_section():
                    ui.label('切换游戏模式').classes('text-h6')
                ui.separator()
                with ui.card_section():
                    player_gamemode = ui.select(options=initial_players, label='选择玩家').classes('w-full')
                    selects_to_update.append(player_gamemode)
                    mode = ui.select(['survival', 'creative', 'adventure', 'spectator'], label='游戏模式', value='survival')
                    ui.button('设置模式', on_click=lambda: execute_command_with_feedback(f'gamemode {mode.value} {player_gamemode.value}'), color='primary').classes('q-mt-md')

            with ui.card().classes('w-full q-mt-md'):
                with ui.card_section():
                    ui.label('传送玩家').classes('text-h6')
                ui.separator()
                with ui.card_section():
                    player_tp = ui.select(options=initial_players, label='传送的玩家').classes('w-full')
                    selects_to_update.append(player_tp)
                    dest = ui.input('目标坐标或玩家').props('clearable')
                    ui.button('执行传送', on_click=lambda: execute_command_with_feedback(f'tp {player_tp.value} {dest.value}'), color='primary').classes('q-mt-md')

        with ui.column().classes('w-full'):
            with ui.card().classes('w-full'):
                with ui.card_section():
                    ui.label('给予物品').classes('text-h6')
                ui.separator()
                with ui.card_section():
                    player_give = ui.select(options=initial_players, label='选择玩家').classes('w-full')
                    selects_to_update.append(player_give)
                    item = ui.select(options=list(item_map.keys()), label='选择物品', with_input=True).props('clearable')
                    count = ui.number('数量', value=1, min=1)
                    ui.button('给予', on_click=lambda: execute_command_with_feedback(f'give {player_give.value} {item_map.get(item.value, item.value)} {int(count.value)}'), color='primary').classes('q-mt-md')

            with ui.card().classes('w-full q-mt-md'):
                with ui.card_section():
                    ui.label('经验管理').classes('text-h6')
                ui.separator()
                with ui.card_section():
                    player_xp = ui.select(options=initial_players, label='选择玩家').classes('w-full')
                    selects_to_update.append(player_xp)
                    with ui.row().classes('items-center w-full'):
                        xp = ui.number('经验值', value=10).classes('flex-grow')
                        xp_type = ui.select(['points', 'levels'], value='points')
                    ui.button('给予经验', on_click=lambda: execute_command_with_feedback(f'experience add {player_xp.value} {int(xp.value)} {xp_type.value}'), color='primary').classes('q-mt-sm')

            with ui.card().classes('w-full q-mt-md'):
                with ui.card_section():
                    ui.label('给予玩家效果').classes('text-h6')
                ui.separator()
                with ui.card_section():
                    player_effect = ui.select(options=initial_players, label='选择玩家').classes('w-full')
                    selects_to_update.append(player_effect)
                    
                    effects = {
                        '速度': 'speed', '急迫': 'haste', '力量': 'strength',
                        '跳跃提升': 'jump_boost', '生命恢复': 'regeneration', '抗性提升': 'resistance',
                        '防火': 'fire_resistance', '水下呼吸': 'water_breathing', '隐身': 'invisibility',
                        '夜视': 'night_vision', '虚弱': 'weakness', '缓慢': 'slowness'
                    }
                    effect_selection = ui.select(options=list(effects.keys()), label='选择效果', value='速度')
                    
                    with ui.row().classes('w-full items-center q-gutter-md'):
                        duration = ui.number('持续时间 (秒)', value=30, min=1).classes('flex-grow')
                        amplifier = ui.number('效果等级', value=1, min=1, max=255).classes('flex-grow')
                    
                    def give_effect():
                        player = player_effect.value
                        effect_id = effects.get(effect_selection.value)
                        dur = int(duration.value)
                        amp = int(amplifier.value) - 1  # 效果等级在命令中是从0开始的
                        if player and effect_id:
                            command = f'effect give {player} {effect_id} {dur} {amp}'
                            execute_command_with_feedback(command)

                    ui.button('给予效果', on_click=give_effect, color='primary').classes('q-mt-md')

    def update_player_options():
        new_players = get_player_list()
        for s in selects_to_update:
            if s.value is not None and s.value not in new_players:
                s.value = None
            s.options = new_players
            s.update()

    ui.timer(5.0, update_player_options, once=False)

def server_page():
    """服务器管理页面"""
    ui.label('服务器管理').classes('text-h4 q-mb-md text-grey-8')

    with ui.grid(columns=2).classes('w-full q-col-gutter-md'):
        with ui.column().classes('w-full'):
            with ui.card().classes('w-full'):
                with ui.card_section():
                    ui.label('时间和天气').classes('text-h6')
                ui.separator()
                with ui.card_section():
                    with ui.row().classes('q-gutter-sm'):
                        ui.button('白天', on_click=lambda: execute_command_with_feedback('time set day'), icon='light_mode')
                        ui.button('夜晚', on_click=lambda: execute_command_with_feedback('time set night'), icon='dark_mode')
                    with ui.row().classes('q-gutter-sm q-mt-sm'):
                        ui.button('晴天', on_click=lambda: execute_command_with_feedback('weather clear'), icon='wb_sunny')
                        ui.button('雨天', on_click=lambda: execute_command_with_feedback('weather rain'), icon='water_drop')
                        ui.button('雷暴', on_click=lambda: execute_command_with_feedback('weather thunder'), icon='flash_on')
            
            with ui.card().classes('w-full q-mt-md'):
                with ui.card_section():
                    ui.label('游戏设定').classes('text-h6')
                ui.separator()
                with ui.card_section():
                    difficulty = ui.select(['peaceful', 'easy', 'normal', 'hard'], label='游戏难度', value='normal')
                    ui.button('设置难度', on_click=lambda: execute_command_with_feedback(f'difficulty {difficulty.value}'), color='primary').classes('q-mt-md')
                ui.separator().classes('q-my-md')
                with ui.card_section():
                    with ui.row().classes('w-full items-center'):
                        rule = ui.input('游戏规则').classes('flex-grow').props('clearable')
                        value = ui.input('规则值').props('clearable')
                    ui.button('设置规则', on_click=lambda: execute_command_with_feedback(f'gamerule {rule.value} {value.value}'), color='primary').classes('q-mt-md')

            with ui.card().classes('w-full q-mt-md'):
                with ui.card_section():
                    ui.label('白名单管理').classes('text-h6')
                ui.separator()
                
                whitelist_list = ui.list()

                def update_whitelist_list():
                    whitelist_list.clear()
                    players = rcon_manager.get_whitelist()
                    with whitelist_list:
                        if players:
                            for p in players:
                                with ui.item():
                                    with ui.item_section():
                                        ui.label(p)
                                    with ui.item_section(side=True):
                                        ui.button(icon='delete', on_click=lambda name=p: remove_from_whitelist(name), color='negative').props('flat round dense')
                        else:
                            with ui.item():
                                ui.item_section('白名单为空')
                
                def add_to_whitelist():
                    player_name = new_player_input.value
                    if player_name:
                        rcon_manager.add_to_whitelist(player_name)
                        ui.notify(f'已将 {player_name} 添加到白名单')
                        new_player_input.value = ''
                        update_whitelist_list()

                def remove_from_whitelist(player_name):
                    rcon_manager.remove_from_whitelist(player_name)
                    ui.notify(f'已将 {player_name} 从白名单移除')
                    update_whitelist_list()

                with ui.card_section():
                    with ui.row().classes('w-full items-center'):
                        new_player_input = ui.input('玩家名').classes('flex-grow').props('clearable')
                        ui.button('添加', on_click=add_to_whitelist, icon='add')
                
                update_whitelist_list()

        with ui.column().classes('w-full'):
            with ui.card().classes('w-full'):
                with ui.card_section():
                    ui.label('封禁列表').classes('text-h6')
                ui.separator()
                
                ban_list_display = ui.list()

                def update_ban_list():
                    ban_list_display.clear()
                    ban_list = rcon_manager.get_ban_list()
                    with ban_list_display:
                        ui.label('玩家:').classes('text-subtitle2')
                        if ban_list['players']:
                            for p in ban_list['players']:
                                ui.label(p)
                        else:
                            ui.label('无')
                        
                        ui.separator().classes('q-my-md')
                        ui.label('IP 地址:').classes('text-subtitle2')
                        if ban_list['ips']:
                            for ip in ban_list['ips']:
                                ui.label(ip)
                        else:
                            ui.label('无')
                
                rcon_manager.ui_update_callbacks['ban_list'] = update_ban_list
                update_ban_list()

            with ui.card().classes('w-full q-mt-md'):
                with ui.card_section():
                    ui.label('解封玩家/IP').classes('text-h6')
                ui.separator()
                with ui.card_section():
                    pardon_input = ui.input('玩家名或IP地址').props('clearable')
                    def pardon_and_update(target_name):
                        rcon_manager.pardon_target(target_name)
                        update_ban_list()
                    ui.button('解封', on_click=lambda: pardon_and_update(pardon_input.value), color='positive').classes('q-mt-md')


def console_page():
    """实时控制台页面"""
    ui.label('实时控制台').classes('text-h4 q-mb-md')
    log = ui.log(max_lines=50).classes('w-full h-96')
    
    def send_command():
        cmd = command_input.value
        log.push(f'--> {cmd}')
        response = execute_command_with_feedback(cmd)
        log.push(response)
        command_input.value = ''

    with ui.row().classes('w-full items-center'):
        command_input = ui.input(placeholder='输入命令...').classes('flex-grow')
        ui.button('发送', on_click=send_command)
    
    with ui.expansion('常用命令示例', icon='help_outline').classes('w-full q-mt-md'):
        ui.label('/help - 查看帮助').classes('text-grey')
        ui.label('/list - 查看在线玩家').classes('text-grey')
        ui.label('/say <消息> - 全服广播').classes('text-grey')

def automation_page():
    """自动化任务页面"""
    ui.label('自动化任务').classes('text-h4 q-mb-md')

    known_players = set(rcon_manager.get_server_status().get('players', []))

    with ui.card().classes('w-full'):
        with ui.card_section():
            ui.label('玩家监控与欢迎').classes('text-h6')
        
        with ui.card_section():
            welcome_messages_input = ui.textarea(
                label='欢迎消息 (每行一条)',
                value='欢迎来到服务器!\n请遵守服务器规则，享受游戏！'
            ).classes('w-full')
            
            monitor_log = ui.log(max_lines=20).classes('w-full h-64 q-my-md')

            def send_welcome_message(player_name):
                messages = welcome_messages_input.value.strip().split('\n')
                for msg in messages:
                    execute_command_with_feedback(f'tell {player_name} {msg}')

            def player_monitor_task():
                nonlocal known_players
                status = rcon_manager.get_server_status()
                if not status.get('online'):
                    return
                
                current_players = set(status.get('players', []))
                
                new_players = current_players - known_players
                for player in new_players:
                    monitor_log.push(f'玩家 {player} 加入了服务器。')
                    send_welcome_message(player)

                left_players = known_players - current_players
                for player in left_players:
                    monitor_log.push(f'玩家 {player} 离开了服务器。')
                
                known_players = current_players

            monitor_timer = ui.timer(10.0, player_monitor_task, active=False)
            
            def toggle_monitoring(e):
                if e.value:
                    monitor_log.push('玩家监控已启动...')
                    monitor_timer.activate()
                else:
                    monitor_log.push('玩家监控已停止。')
                    monitor_timer.deactivate()

            ui.switch('启用玩家监控', on_change=toggle_monitoring)

    with ui.card().classes('w-full q-mt-md'):
        with ui.card_section():
            ui.label('定时清理掉落物').classes('text-h6')
        
        with ui.card_section():
            clear_interval_input = ui.number(label='清理间隔 (分钟)', value=30, min=1)
            
            def clear_items_task():
                execute_command_with_feedback('kill @e[type=item]')

            clear_timer = ui.timer(clear_interval_input.value * 60, clear_items_task, active=False)

            def toggle_clearing(e):
                if e.value:
                    clear_timer.interval = clear_interval_input.value * 60
                    clear_timer.activate()
                    ui.notify(f'已启动定时清理，每 {clear_interval_input.value} 分钟执行一次。')
                else:
                    clear_timer.deactivate()
                    ui.notify('定时清理已停止。')
            
            ui.switch('启用定时清理', on_change=toggle_clearing)

# --- UI 布局和应用启动 ---

with ui.header(elevated=True).style('background-color: #3874c8').classes('items-center justify-between'):
    with ui.row().classes('items-center'):
        ui.icon('gamepad', size='lg', color='white')
        ui.label('Minecraft RCON 面板').classes('text-h5')

with ui.tabs().classes('w-full') as tabs:
    ui.tab('仪表盘', icon='dashboard')
    ui.tab('玩家管理', icon='people')
    ui.tab('服务器管理', icon='storage')
    ui.tab('实时控制台', icon='terminal')
    ui.tab('自动化', icon='smart_toy')

with ui.tab_panels(tabs, value='仪表盘').classes('w-full'):
    with ui.tab_panel('仪表盘'):
        dashboard_page()
    with ui.tab_panel('玩家管理'):
        players_page()
    with ui.tab_panel('服务器管理'):
        server_page()
    with ui.tab_panel('实时控制台'):
        console_page()
    with ui.tab_panel('自动化'):
        automation_page()

ui.run()