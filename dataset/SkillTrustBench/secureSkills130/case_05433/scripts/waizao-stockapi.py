#!/usr/bin/env python3
"""
Waizao StockAPI CLI - Query Chinese stock market data via waizaowang.com
基于歪枣网 API 的股票数据查询工具
"""

import argparse
import json
import os
import sys

try:
    from waizao.api_demo import stock_api
    import pandas as pd
except ImportError as e:
    print(f"Error: Missing required package: {e}", file=sys.stderr)
    print("Install with: pip install waizao pandas", file=sys.stderr)
    sys.exit(1)

# API Configuration
TOKEN = os.environ.get("WAIZAO_TOKEN", "")

def check_token():
    """Check if token is configured"""
    if not TOKEN:
        print("Error: WAIZAO_TOKEN not set.", file=sys.stderr)
        print("Please set environment variable:", file=sys.stderr)
        print("  export WAIZAO_TOKEN='your_token_here'", file=sys.stderr)
        print("\nGet token from: http://www.waizaowang.com/", file=sys.stderr)
        sys.exit(1)

def format_output(data, output_format="json"):
    """Format output data"""
    if output_format == "json":
        if isinstance(data, pd.DataFrame):
            print(data.to_json(orient='records', force_ascii=False, indent=2))
        else:
            print(data)
    elif output_format == "table":
        if isinstance(data, pd.DataFrame):
            print(data.to_string(index=False))
        else:
            print(data)
    elif output_format == "csv":
        if isinstance(data, pd.DataFrame):
            print(data.to_csv(index=False))
        else:
            print(data)

def cmd_stock_list(args):
    """Get stock list by type"""
    check_token()
    data = stock_api.getStockType(
        flags=args.type,
        fields="all",
        export=5,  # DataFrame
        token=TOKEN,
        filter=""
    )
    format_output(data, args.format)

def cmd_stock_daily(args):
    """Get daily K-line data for A-shares"""
    check_token()
    data = stock_api.getStockHSADayKLine(
        code=args.code,
        ktype=args.ktype,
        fq=args.fq,
        startDate=args.start_date,
        endDate=args.end_date,
        fields="all",
        export=5,
        token=TOKEN,
        filter=""
    )
    format_output(data, args.format)

def cmd_stock_realtime(args):
    """Get real-time/daily market data"""
    check_token()
    data = stock_api.getStockHSADailyMarket(
        code=args.code,
        fields="all",
        export=5,
        token=TOKEN,
        filter=""
    )
    format_output(data, args.format)

def cmd_index_daily(args):
    """Get index daily K-line data"""
    check_token()
    data = stock_api.getIndexDayKLine(
        code=args.code,
        ktype=args.ktype,
        startDate=args.start_date,
        endDate=args.end_date,
        fields="all",
        export=5,
        token=TOKEN,
        filter=""
    )
    format_output(data, args.format)

def cmd_limit_up(args):
    """Get limit-up stock pool (涨停池)"""
    check_token()
    data = stock_api.getPoolZT(
        startDate=args.date,
        endDate=args.date,
        fields="all",
        export=5,
        token=TOKEN,
        filter=""
    )
    format_output(data, args.format)

def cmd_limit_down(args):
    """Get limit-down stock pool (跌停池)"""
    check_token()
    data = stock_api.getPoolDT(
        startDate=args.date,
        endDate=args.date,
        fields="all",
        export=5,
        token=TOKEN,
        filter=""
    )
    format_output(data, args.format)

def cmd_fund_nav(args):
    """Get fund NAV (净值)"""
    check_token()
    data = stock_api.getFundNav(
        code=args.code,
        startDate=args.start_date,
        endDate=args.end_date,
        fields="all",
        export=5,
        token=TOKEN,
        filter=""
    )
    format_output(data, args.format)

def cmd_fund_rank(args):
    """Get fund ranking"""
    check_token()
    data = stock_api.getFundRank(
        type=args.type,
        fields="all",
        export=5,
        token=TOKEN,
        filter=""
    )
    format_output(data, args.format)

def cmd_indicator_macd(args):
    """Get MACD indicator"""
    check_token()
    data = stock_api.getIndicatorTaMacd(
        code=args.code,
        startDate=args.start_date,
        endDate=args.end_date,
        fields="all",
        export=5,
        token=TOKEN,
        filter=""
    )
    format_output(data, args.format)

def cmd_indicator_rsi(args):
    """Get RSI indicator"""
    check_token()
    data = stock_api.getIndicatorTaRsi(
        code=args.code,
        startDate=args.start_date,
        endDate=args.end_date,
        fields="all",
        export=5,
        token=TOKEN,
        filter=""
    )
    format_output(data, args.format)

def cmd_hsgt_money(args):
    """Get North-South capital flow (沪深港通资金)"""
    check_token()
    data = stock_api.getHSGTMoney(
        startDate=args.start_date,
        endDate=args.end_date,
        fields="all",
        export=5,
        token=TOKEN,
        filter=""
    )
    format_output(data, args.format)

def cmd_hsgt_stock_rank(args):
    """Get top stocks by northbound capital (北上资金持股榜)"""
    check_token()
    data = stock_api.getHSGTStockRank(
        date=args.date,
        fields="all",
        export=5,
        token=TOKEN,
        filter=""
    )
    format_output(data, args.format)

def cmd_longhuban(args):
    """Get dragon-tiger list (龙虎榜)"""
    check_token()
    data = stock_api.getLonghbDetail(
        code=args.code,
        startDate=args.start_date,
        endDate=args.end_date,
        fields="all",
        export=5,
        token=TOKEN,
        filter=""
    )
    format_output(data, args.format)

def cmd_finance_report(args):
    """Get financial reports"""
    check_token()
    if args.report_type == "yugao":
        data = stock_api.getReportYugao(
            code=args.code,
            startDate=args.start_date,
            endDate=args.end_date,
            fields="all",
            export=5,
            token=TOKEN,
            filter=""
        )
    elif args.report_type == "kuibao":
        data = stock_api.getReportKuaiBao(
            code=args.code,
            startDate=args.start_date,
            endDate=args.end_date,
            fields="all",
            export=5,
            token=TOKEN,
            filter=""
        )
    else:
        print(f"Unknown report type: {args.report_type}", file=sys.stderr)
        sys.exit(1)
    format_output(data, args.format)

def cmd_test(args):
    """Test API connection"""
    check_token()
    print(f"Testing connection to waizaowang.com...")
    print(f"Token configured: Yes")
    
    # Try a simple request - get stock type
    try:
        data = stock_api.getStockType(
            flags=1,  # 上证 A 股
            fields="code,name",
            export=5,
            token=TOKEN,
            filter=""
        )
        if isinstance(data, pd.DataFrame) and len(data) > 0:
            print("✓ API connection successful!")
            print(f"  Token status: Valid")
            print(f"  Sample data: Retrieved {len(data)} stocks")
        else:
            print("✗ API request returned empty data")
    except Exception as e:
        print(f"✗ API request failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Waizao StockAPI CLI - 歪枣网股票数据查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get Shanghai A-share list
  python3 waizao-stockapi.py stock list --type 1
  
  # Get daily K-line for a stock
  python3 waizao-stockapi.py stock daily --code 600004 --start 2024-01-01 --end 2024-01-10
  
  # Get real-time market data
  python3 waizao-stockapi.py stock realtime --code 600004
  
  # Get today's limit-up stocks
  python3 waizao-stockapi.py limit up --date 2024-01-15
  
  # Get MACD indicator
  python3 waizao-stockapi.py indicator macd --code 600004 --start 2024-01-01 --end 2024-01-10
  
  # Get northbound capital flow
  python3 waizao-stockapi.py hsgt money --start 2024-01-01 --end 2024-01-10
  
  # Test API connection
  python3 waizao-stockapi.py test

Environment Variables:
  WAIZAO_TOKEN  - Your Waizao API token (required)

For more API endpoints, visit: http://www.waizaowang.com/
        """
    )
    
    parser.add_argument("--format", "-f", choices=["json", "table", "csv"], default="json",
                       help="Output format (default: json)")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Stock commands
    stock_parser = subparsers.add_parser("stock", help="Stock data commands")
    stock_sub = stock_parser.add_subparsers(dest="stock_cmd")
    
    # Stock list
    list_parser = stock_sub.add_parser("list", help="Get stock list by type")
    list_parser.add_argument("--type", "-t", type=int, required=True, 
                            help="Stock type: 1|上证 A 股; 2|深证 A 股; 3|北证 A 股; 6|创业板; 7|科创板; etc.")
    list_parser.set_defaults(func=cmd_stock_list)
    
    # Stock daily K-line
    daily_parser = stock_sub.add_parser("daily", help="Get daily K-line data")
    daily_parser.add_argument("--code", "-c", required=True, help="Stock code")
    daily_parser.add_argument("--start", "-s", required=True, help="Start date (YYYY-MM-DD)")
    daily_parser.add_argument("--end", "-e", required=True, help="End date (YYYY-MM-DD)")
    daily_parser.add_argument("--ktype", "-k", type=int, default=101, 
                             help="K-line type: 101|日线; 102|周线; 103|月线")
    daily_parser.add_argument("--fq", type=int, default=0,
                             help="复权：0|不复权; 1|前复权; 2|后复权")
    daily_parser.set_defaults(func=cmd_stock_daily)
    
    # Stock real-time
    realtime_parser = stock_sub.add_parser("realtime", help="Get real-time/daily market data")
    realtime_parser.add_argument("--code", "-c", required=True, help="Stock code")
    realtime_parser.set_defaults(func=cmd_stock_realtime)
    
    # Index commands
    index_parser = subparsers.add_parser("index", help="Index data commands")
    index_sub = index_parser.add_subparsers(dest="index_cmd")
    
    index_daily_parser = index_sub.add_parser("daily", help="Get index daily data")
    index_daily_parser.add_argument("--code", "-c", required=True, help="Index code")
    index_daily_parser.add_argument("--start", "-s", required=True, help="Start date")
    index_daily_parser.add_argument("--end", "-e", required=True, help="End date")
    index_daily_parser.add_argument("--ktype", "-k", type=int, default=101,
                                   help="K-line type: 101|日线; 102|周线; 103|月线")
    index_daily_parser.set_defaults(func=cmd_index_daily)
    
    # Limit up/down commands
    limit_parser = subparsers.add_parser("limit", help="Limit up/down pool")
    limit_sub = limit_parser.add_subparsers(dest="limit_cmd")
    
    limit_up_parser = limit_sub.add_parser("up", help="Get limit-up stocks (涨停池)")
    limit_up_parser.add_argument("--date", "-d", required=True, help="Date (YYYY-MM-DD)")
    limit_up_parser.set_defaults(func=cmd_limit_up)
    
    limit_down_parser = limit_sub.add_parser("down", help="Get limit-down stocks (跌停池)")
    limit_down_parser.add_argument("--date", "-d", required=True, help="Date (YYYY-MM-DD)")
    limit_down_parser.set_defaults(func=cmd_limit_down)
    
    # Fund commands
    fund_parser = subparsers.add_parser("fund", help="Fund data commands")
    fund_sub = fund_parser.add_subparsers(dest="fund_cmd")
    
    fund_nav_parser = fund_sub.add_parser("nav", help="Get fund NAV")
    fund_nav_parser.add_argument("--code", "-c", required=True, help="Fund code")
    fund_nav_parser.add_argument("--start", "-s", required=True, help="Start date")
    fund_nav_parser.add_argument("--end", "-e", required=True, help="End date")
    fund_nav_parser.set_defaults(func=cmd_fund_nav)
    
    fund_rank_parser = fund_sub.add_parser("rank", help="Get fund ranking")
    fund_rank_parser.add_argument("--type", "-t", type=int, default=1,
                                 help="Fund type: 1|全部; 2|股票型; 3|混合型; 4|债券型")
    fund_rank_parser.set_defaults(func=cmd_fund_rank)
    
    # Indicator commands
    indicator_parser = subparsers.add_parser("indicator", help="Technical indicators")
    indicator_sub = indicator_parser.add_subparsers(dest="indicator_cmd")
    
    macd_parser = indicator_sub.add_parser("macd", help="MACD indicator")
    macd_parser.add_argument("--code", "-c", required=True, help="Stock code")
    macd_parser.add_argument("--start", "-s", required=True, help="Start date")
    macd_parser.add_argument("--end", "-e", required=True, help="End date")
    macd_parser.set_defaults(func=cmd_indicator_macd)
    
    rsi_parser = indicator_sub.add_parser("rsi", help="RSI indicator")
    rsi_parser.add_argument("--code", "-c", required=True, help="Stock code")
    rsi_parser.add_argument("--start", "-s", required=True, help="Start date")
    rsi_parser.add_argument("--end", "-e", required=True, help="End date")
    rsi_parser.set_defaults(func=cmd_indicator_rsi)
    
    # HSGT (North-South capital) commands
    hsgt_parser = subparsers.add_parser("hsgt", help="North-South capital (沪深港通)")
    hsgt_sub = hsgt_parser.add_subparsers(dest="hsgt_cmd")
    
    hsgt_money_parser = hsgt_sub.add_parser("money", help="Get capital flow")
    hsgt_money_parser.add_argument("--start", "-s", required=True, help="Start date")
    hsgt_money_parser.add_argument("--end", "-e", required=True, help="End date")
    hsgt_money_parser.set_defaults(func=cmd_hsgt_money)
    
    hsgt_stock_parser = hsgt_sub.add_parser("stock", help="Get stock ranking")
    hsgt_stock_parser.add_argument("--date", "-d", required=True, help="Date")
    hsgt_stock_parser.set_defaults(func=cmd_hsgt_stock_rank)
    
    # Dragon-tiger list
    longhu_parser = subparsers.add_parser("longhu", help="Dragon-tiger list (龙虎榜)")
    longhu_parser.add_argument("--code", "-c", required=True, help="Stock code")
    longhu_parser.add_argument("--start", "-s", required=True, help="Start date")
    longhu_parser.add_argument("--end", "-e", required=True, help="End date")
    longhu_parser.set_defaults(func=cmd_longhuban)
    
    # Finance report
    finance_parser = subparsers.add_parser("finance", help="Financial reports")
    finance_parser.add_argument("--code", "-c", required=True, help="Stock code")
    finance_parser.add_argument("--start", "-s", required=True, help="Start date")
    finance_parser.add_argument("--end", "-e", required=True, help="End date")
    finance_parser.add_argument("--type", "-t", required=True, choices=["yugao", "kuibao"],
                               help="Report type: yugao|预告; kuibao|快报")
    finance_parser.set_defaults(func=cmd_finance_report)
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test API connection")
    test_parser.set_defaults(func=cmd_test)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
