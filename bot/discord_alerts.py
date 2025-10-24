#!/usr/bin/env python3
"""
DISCORD ALERTS - webhook notifications
"""

import urllib.request
import json
from datetime import datetime

class DiscordAlerter:
    def __init__(self, webhook_url: str = None):
        """
        Создай webhook:
        1. Discord Server Settings → Integrations → Webhooks
        2. Create Webhook → Copy URL
        """
        self.webhook_url = webhook_url or self._load_webhook()
        
        if self.webhook_url:
            print("✅ Discord Alerter initialized")
        else:
            print("⚠️  Discord webhook not set. Create config/discord.json")
    
    def _load_webhook(self):
        """Load webhook from config"""
        try:
            from pathlib import Path
            config_file = Path(__file__).parent.parent / 'config' / 'discord.json'
            if config_file.exists():
                with open(config_file) as f:
                    return json.load(f).get('webhook_url')
        except:
            pass
        return None
    
    def send(self, title: str, message: str, color: int = 3447003):
        """
        Send alert to Discord
        
        Colors:
        - Green (success): 3066993
        - Red (error): 15158332
        - Blue (info): 3447003
        - Yellow (warning): 16776960
        """
        if not self.webhook_url:
            print(f"[ALERT] {title}: {message}")
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
        
        data = json.dumps(embed).encode('utf-8')
        
        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 204:
                    return True
        
        except Exception as e:
            print(f"Discord send error: {e}")
        
        return False
    
    def trade_opened(self, asset: str, strategy: str, entry_price: float, size: float):
        """Alert: trade opened"""
        message = f"""
**Asset:** {asset}
**Strategy:** {strategy}
**Entry:** ${entry_price:,.2f}
**Size:** ${size:,.2f}
        """
        self.send(f"🟢 Trade Opened", message.strip(), color=3066993)
    
    def trade_closed(self, asset: str, strategy: str, pnl: float, pnl_pct: float):
        """Alert: trade closed"""
        color = 3066993 if pnl > 0 else 15158332
        emoji = "🟢" if pnl > 0 else "🔴"
        
        message = f"""
**Asset:** {asset}
**Strategy:** {strategy}
**P&L:** ${pnl:,.2f} ({pnl_pct:+.2f}%)
        """
        self.send(f"{emoji} Trade Closed", message.strip(), color=color)
    
    def system_error(self, error: str):
        """Alert: system error"""
        self.send("🔴 System Error", error, color=15158332)
    
    def system_healthy(self, metrics: dict):
        """Alert: system health check"""
        message = f"""
**Status:** Running
**Capital:** ${metrics.get('capital', 0):,.2f}
**Open Trades:** {metrics.get('open_trades', 0)}
**Win Rate:** {metrics.get('win_rate', 0):.1f}%
        """
        self.send("✅ System Health", message.strip(), color=3066993)
    
    def backtest_complete(self, results: dict):
        """Alert: backtest finished"""
        color = 3066993 if results.get('return', 0) > 0 else 15158332
        
        message = f"""
**Strategy:** {results.get('strategy', 'Unknown')}
**Period:** {results.get('days', 0)} days
**Win Rate:** {results.get('win_rate', 0)*100:.1f}%
**Return:** {results.get('return', 0)*100:+.1f}%
**Trades:** {results.get('trades', 0)}
        """
        self.send("📊 Backtest Complete", message.strip(), color=color)

# CREATE CONFIG TEMPLATE
if __name__ == "__main__":
    from pathlib import Path
    
    config_dir = Path(__file__).parent.parent / 'config'
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / 'discord.json'
    
    if not config_file.exists():
        template = {
            "webhook_url": "YOUR_DISCORD_WEBHOOK_URL_HERE",
            "instructions": [
                "1. Go to Discord Server Settings",
                "2. Integrations → Webhooks",
                "3. Create Webhook",
                "4. Copy webhook URL",
                "5. Paste it here"
            ]
        }
        
        with open(config_file, 'w') as f:
            json.dump(template, f, indent=2)
        
        print(f"✅ Created config template: {config_file}")
        print("\nEdit this file with your Discord webhook URL")
    else:
        # Test
        alerter = DiscordAlerter()
        alerter.send("🚀 Test Alert", "Discord alerts working!", color=3447003)
        print("\n✅ Test alert sent!")
