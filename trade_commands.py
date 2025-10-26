#!/usr/bin/env python3
import sys
from paper_trading_journal import PaperTradingJournal

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 trade_commands.py open <strategy> <asset> <price> [notes]")
        print("  python3 trade_commands.py close <trade_id> <exit_price> [reason]")
        print("  python3 trade_commands.py status")
        print("  python3 trade_commands.py history [count]")
        return
    
    journal = PaperTradingJournal()
    command = sys.argv[1].lower()
    
    if command == "open":
        if len(sys.argv) < 5:
            print("Usage: python3 trade_commands.py open <strategy> <asset> <price> [notes]")
            return
        
        strategy = sys.argv[2]
        asset = sys.argv[3]
        price = float(sys.argv[4])
        notes = sys.argv[5] if len(sys.argv) > 5 else ""
        
        trade_id = journal.open_trade(strategy, asset, price, notes=notes)
    
    elif command == "close":
        if len(sys.argv) < 4:
            print("Usage: python3 trade_commands.py close <trade_id> <exit_price> [reason]")
            return
        
        trade_id = sys.argv[2]
        exit_price = float(sys.argv[3])
        reason = sys.argv[4] if len(sys.argv) > 4 else "Manual"
        
        journal.close_trade(trade_id, exit_price, reason)
    
    elif command == "status":
        journal.show_portfolio_status()
    
    elif command == "history":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        journal.show_trade_history(count)
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
