#!/usr/bin/env python3
"""
DISCORD MULTI-CHANNEL SYSTEM
- FREE channel (базовые сигналы)
- VIP channel (детальная аналитика)
- ADMIN channel (служебная информация)
"""
import urllib.request
import json
from datetime import datetime
from pathlib import Path

class DiscordMultiChannel:
    def __init__(self):
        """Load webhooks from config"""
        config_file = Path(__file__).parent.parent / 'config' / 'discord.json'
        
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
                self.free_webhook = config.get('free_channel')
                self.vip_webhook = config.get('vip_channel')
                self.admin_webhook = config.get('admin_channel')
        else:
            self.free_webhook = None
            self.vip_webhook = None
            self.admin_webhook = None
        
        print("✅ Discord Multi-Channel initialized")
        print(f"   FREE:  {'✅' if self.free_webhook else '❌'}")
        print(f"   VIP:   {'✅' if self.vip_webhook else '❌'}")
        print(f"   ADMIN: {'✅' if self.admin_webhook else '❌'}")
    
    def _send(self, webhook_url, title, message, color=3447003, fields=None):
        """Send to specific webhook"""
        if not webhook_url or webhook_url == "YOUR_WEBHOOK_URL":
            return False
        
        embed = {
            "embeds": [{
                "title": title,
                "description": message,
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {"text": "ETH Options System"}
            }]
        }
        
        if fields:
            embed["embeds"][0]["fields"] = fields
        
        data = json.dumps(embed).encode('utf-8')
        
        try:
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 204
        except Exception as e:
            print(f"Send error: {e}")
            return False
    
    # ===== FREE CHANNEL (базовые сигналы) =====
    
    def free_signal(self, asset, signal_type, price):
        """FREE: Простой сигнал"""
        emoji = "🟢" if signal_type == "BUY" else "🔴"
        
        message = f"""
**Asset:** {asset}
**Signal:** {signal_type}
**Price:** ${price:,.2f}
"""
        
        self._send(
            self.free_webhook,
            f"{emoji} {signal_type} Signal",
            message.strip(),
            color=3066993 if signal_type == "BUY" else 15158332
        )
    
    # ===== VIP CHANNEL (детальная аналитика) =====
    
    def vip_trade_opened(self, trade_data):
        """VIP: Детальная информация о входе"""
        
        fields = [
            {"name": "Asset", "value": trade_data['asset'], "inline": True},
            {"name": "Strategy", "value": trade_data['strategy'], "inline": True},
            {"name": "Entry Price", "value": f"${trade_data['entry']:,.2f}", "inline": True},
            {"name": "Position Size", "value": f"${trade_data['size']:,.2f}", "inline": True},
            {"name": "Stop Loss", "value": f"${trade_data.get('sl', 0):,.2f}", "inline": True},
            {"name": "Take Profit", "value": f"${trade_data.get('tp', 0):,.2f}", "inline": True},
            {"name": "Risk/Reward", "value": f"1:{trade_data.get('rr', 2)}", "inline": True},
            {"name": "Delta", "value": f"{trade_data.get('delta', 0):.4f}", "inline": True},
            {"name": "Theta", "value": f"{trade_data.get('theta', 0):.2f}/day", "inline": True}
        ]
        
        self._send(
            self.vip_webhook,
            "🟢 VIP Trade Opened",
            f"**Signal Quality:** {trade_data.get('quality', 'High')}",
            color=3066993,
            fields=fields
        )
    
    def vip_trade_closed(self, trade_data):
        """VIP: Детальная информация о выходе"""
        
        color = 3066993 if trade_data['pnl'] > 0 else 15158332
        emoji = "🟢" if trade_data['pnl'] > 0 else "🔴"
        
        fields = [
            {"name": "Asset", "value": trade_data['asset'], "inline": True},
            {"name": "Entry", "value": f"${trade_data['entry']:,.2f}", "inline": True},
            {"name": "Exit", "value": f"${trade_data['exit']:,.2f}", "inline": True},
            {"name": "P&L", "value": f"${trade_data['pnl']:,.2f}", "inline": True},
            {"name": "P&L %", "value": f"{trade_data['pnl_pct']:+.2f}%", "inline": True},
            {"name": "Hold Time", "value": f"{trade_data['hold_hours']:.1f}h", "inline": True},
            {"name": "Exit Reason", "value": trade_data['exit_reason'], "inline": True},
            {"name": "Commission", "value": f"${trade_data['commission']:.2f}", "inline": True},
            {"name": "New Capital", "value": f"${trade_data['capital']:,.2f}", "inline": True}
        ]
        
        self._send(
            self.vip_webhook,
            f"{emoji} VIP Trade Closed",
            f"**Result:** {'WIN' if trade_data['pnl'] > 0 else 'LOSS'}",
            color=color,
            fields=fields
        )
    
    def vip_daily_report(self, report_data):
        """VIP: Ежедневный отчёт"""
        
        fields = [
            {"name": "Trades Today", "value": str(report_data['trades']), "inline": True},
            {"name": "Win Rate", "value": f"{report_data['wr']*100:.1f}%", "inline": True},
            {"name": "Daily P&L", "value": f"${report_data['pnl']:,.2f}", "inline": True},
            {"name": "Sharpe Ratio", "value": f"{report_data['sharpe']:.2f}", "inline": True},
            {"name": "Max Drawdown", "value": f"{report_data['max_dd']*100:.1f}%", "inline": True},
            {"name": "Total Capital", "value": f"${report_data['capital']:,.2f}", "inline": True}
        ]
        
        self._send(
            self.vip_webhook,
            "📊 Daily Performance Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
            color=3447003,
            fields=fields
        )
    
    # ===== ADMIN CHANNEL (служебная информация) =====
    
    def admin_system_started(self):
        """ADMIN: Система запущена"""
        self._send(
            self.admin_webhook,
            "🚀 System Started",
            f"Bot started successfully\nMode: Paper Trading\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            color=3066993
        )
    
    def admin_system_stopped(self):
        """ADMIN: Система остановлена"""
        self._send(
            self.admin_webhook,
            "⏹️ System Stopped",
            f"Bot stopped\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            color=16776960
        )
    
    def admin_error(self, error_msg, traceback=None):
        """ADMIN: Ошибка системы"""
        msg = f"**Error:** {error_msg}"
        if traceback:
            msg += f"\n\n```\n{traceback[:1000]}\n```"
        
        self._send(
            self.admin_webhook,
            "🔴 System Error",
            msg,
            color=15158332
        )
    
    def admin_backup_complete(self, backup_info):
        """ADMIN: Backup завершён"""
        self._send(
            self.admin_webhook,
            "💾 Backup Complete",
            f"Files: {backup_info['files']}\nSize: {backup_info['size']}\nLocation: {backup_info['path']}",
            color=3447003
        )
    
    def admin_health_check(self, health_data):
        """ADMIN: Health check"""
        
        status = "🟢 HEALTHY" if health_data['status'] == 'ok' else "🔴 ISSUES"
        
        fields = [
            {"name": "CPU", "value": f"{health_data.get('cpu', 0):.1f}%", "inline": True},
            {"name": "Memory", "value": f"{health_data.get('memory', 0):.1f}%", "inline": True},
            {"name": "Disk", "value": f"{health_data.get('disk', 0):.1f}%", "inline": True},
            {"name": "Open Trades", "value": str(health_data.get('trades', 0)), "inline": True},
            {"name": "Uptime", "value": f"{health_data.get('uptime', 0):.1f}h", "inline": True}
        ]
        
        self._send(
            self.admin_webhook,
            f"{status} Health Check",
            f"**Last Check:** {datetime.now().strftime('%H:%M:%S')}",
            color=3066993 if health_data['status'] == 'ok' else 15158332,
            fields=fields
        )
    
    def admin_github_sync(self, sync_info):
        """ADMIN: GitHub sync"""
        self._send(
            self.admin_webhook,
            "📁 GitHub Sync Complete",
            f"Commit: {sync_info['commit']}\nFiles: {sync_info['files']}\nBranch: main",
            color=3447003
        )

# CREATE CONFIG TEMPLATE
def create_config_template():
    """Создать шаблон конфига"""
    config_dir = Path(__file__).parent.parent / 'config'
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / 'discord.json'
    
    template = {
        "free_channel": "YOUR_FREE_WEBHOOK_URL",
        "vip_channel": "YOUR_VIP_WEBHOOK_URL",
        "admin_channel": "YOUR_ADMIN_WEBHOOK_URL",
        "setup_instructions": [
            "1. Create Discord server",
            "2. Create 3 channels: #free-signals, #vip-analytics, #admin-logs",
            "3. For each channel: Edit → Integrations → Webhooks → Create",
            "4. Copy webhook URLs and paste here"
        ]
    }
    
    with open(config_file, 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"✅ Config template created: {config_file}")
    return config_file

if __name__ == "__main__":
    config_file = create_config_template()
    
    print(f"\n📝 SETUP INSTRUCTIONS:")
    print(f"1. Edit: {config_file}")
    print(f"2. Add your 3 webhook URLs")
    print(f"3. Test: python3 bot/discord_multi_channel.py")
