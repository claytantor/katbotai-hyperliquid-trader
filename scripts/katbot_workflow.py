import sys, os, time, json, argparse, importlib.util
import requests
from katbot_client import get_token, request_recommendation, poll_recommendation, execute_recommendation, get_portfolio
from token_selector import get_top_tokens

# Mock BMI for now as the obsidian script is external
def get_bmi():
    # In a real setup, we would call the btc_momentum.py script
    # For the skill, we can either include it or fetch it via API if available
    return {"bmi": 25, "signal": "BULLISH", "btc_24h_pct": 3.5}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--portfolio-id', type=int, required=True)
    parser.add_argument('--top', type=int, default=5)
    args = parser.parse_args()

    token = get_token()
    bmi_data = get_bmi()
    bullish = bmi_data['bmi'] >= 15
    bearish = bmi_data['bmi'] <= -15

    if not bullish and not bearish:
        print("Market is neutral. Skipping.")
        return

    tokens = get_top_tokens(args.top, bearish)
    symbols = [t['symbol'] for t in tokens]
    
    msg = f"Market is {'bullish' if bullish else 'bearish'}. Tokens: {symbols}. Get recommendation."
    ticket = request_recommendation(token, args.portfolio_id, msg)
    result = poll_recommendation(token, ticket['ticket_id'])
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
