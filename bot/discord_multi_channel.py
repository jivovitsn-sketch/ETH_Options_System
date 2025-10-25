#!/usr/bin/env python3
"""
DISCORD MULTI-CHANNEL SYSTEM with PROXY support
"""
import urllib.request
import urllib.parse
import json
import os
from datetime import datetime
from pathlib import Path

class DiscordMultiChannel:
    def __init__(self):
        """Load webhooks and setup proxy"""
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
        
        # Setup proxy if available
        self._setup_proxy()
        
        print("Discord Multi-Channel with PROXY initialized")
        print(f"   FREE:  {'✅' if self.free_webhook else '❌'}")
        print(f"   VIP:   {'✅' if self.vip_webhook else '❌'}")
        print(f"   ADMIN: {'✅' if self.admin_webhook else '❌'}")
        print(f"   PROXY: {'✅' if self.proxy_enabled else '❌'}")
    
    def _setup_proxy(self):
        """Setup proxy from environment variables"""
        
        proxy_url = os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY')
        
        if proxy_url:
            proxy_handler = urllib.request.ProxyHandler({
                'http': proxy_url,
                'https': proxy_url
            })
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)
            self.proxy_enabled = True
            print(f"   Proxy configured: {proxy_url}")
        else:
            self.proxy_enabled = False
    
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
            
            with urllib.request.urlopen(req, timeout=15) as response:
                success = response.status in [200, 204]
                if success:
                    print(f"✅ Message sent successfully")
                else:
                    print(f"❌ HTTP {response.status}")
                return success
                
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False
    
    def free_signal(self, asset, signal_type, price):
        """FREE: Simple signal"""
        emoji = "🟢" if signal_type == "BUY" else "🔴"
        
        message = f"""
**Asset:** {asset}
**Signal:** {signal_type}
**Price:** ${price:,.2f}
"""
        
        return self._send(
            self.free_webhook,
            f"{emoji} {signal_type} Signal",
            message.strip(),
            color=3066993 if signal_type == "BUY" else 15158332
        )
    
    def vip_trade_opened(self, trade_data):
        """VIP: Detailed trade info"""
        
        fields = [
            {"name": "Asset", "value": trade_data['asset'], "inline": True},
            {"name": "Strategy", "value": trade_data['strategy'], "inline": True},
            {"name": "Entry Price", "value": f"${trade_data['entry']:,.2f}", "inline": True},
            {"name": "Position Size", "value": f"${trade_data['size']:,.2f}", "inline": True},
            {"name": "Delta", "value": f"{trade_data.get('delta', 0):.4f}", "inline": True},
            {"name": "Theta", "value": f"{trade_data.get('theta', 0):.2f}/day", "inline": True}
        ]
        
        return self._send(
            self.vip_webhook,
            "🟢 VIP Trade Opened",
            f"**Signal Quality:** {trade_data.get('quality', 'High')}",
            color=3066993,
            fields=fields
        )
    
    def admin_system_started(self):
        """ADMIN: System started"""
        return self._send(
            self.admin_webhook,
            "🚀 System Started",
            f"Bot started successfully\nMode: Paper Trading\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            color=3066993
        )

if __name__ == "__main__":
    # Тест
    discord = DiscordMultiChannel()
    
    print("\nОтправляю тестовые сообщения...")
    
    # FREE test
    print("\n1️⃣  FREE channel...")
    discord.free_signal('ETHUSDT', 'BUY', 3939.00)
    
    # VIP test  
    print("\n2️⃣  VIP channel...")
    discord.vip_trade_opened({
        'asset': 'ETHUSDT',
        'strategy': 'Bull Call 60DTE', 
        'entry': 3939.00,
        'size': 500,
        'delta': 0.071,
        'theta': 0.05,
        'quality': 'High'
    })
    
    # ADMIN test
    print("\n3️⃣  ADMIN channel...")
    discord.admin_system_started()
    
    print("\n📱 Проверь Discord каналы!")
