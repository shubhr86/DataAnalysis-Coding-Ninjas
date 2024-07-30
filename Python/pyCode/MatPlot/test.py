import requests
from solana.rpc.api import Client
from solana.transaction import Transaction, TransactionInstruction
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.types import TxOpts
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from web3 import Web3

# User configuration
SLIPPAGE = 0.3  # 1%
PRICE_IMPACT = 0.02  # 2%
TX_PRIORITY = "high"  # options: low, medium, high

# Initialize Solana client
client = Client("https://api.mainnet-beta.solana.com")

# Function to get current price from Dexscreener
def get_price_from_dexscreener():
    response = requests.get("https://api.dexscreener.io/latest/dex/pairs/solana")
    if response.status_code == 200:
        data = response.json()
        sol_usdt_pair = next(pair for pair in data['pairs'] if pair['baseToken']['symbol'] == 'SOL' and pair['quoteToken']['symbol'] == 'USDT')
        return float(sol_usdt_pair['priceUsd'])
    else:
        print("Failed to fetch price data.")
        return None

# Function to create and send a transaction
def send_transaction(sender: Keypair, receiver: PublicKey, amount: float):
    transaction = Transaction()
    # Example instruction: transfer SOL
    transfer_instruction = TransactionInstruction(
        program_id=PublicKey("Ecs8tX7rfwMUpaym9HYLEuhbFV5ouVSWND5qKupjY4ro"),  # Replace with actual program ID
        keys=[
            {"pubkey": sender.public_key, "is_signer": True, "is_writable": True},
            {"pubkey": receiver, "is_signer": False, "is_writable": True},
        ],
        data=b''  # No additional data needed for a transfer instruction
    )
    transaction.add(transfer_instruction)
    
    # Set transaction options based on priority
    if TX_PRIORITY == "high":
        tx_opts = TxOpts(skip_confirmation=True)
    elif TX_PRIORITY == "medium":
        tx_opts = TxOpts(preflight_commitment='confirmed')
    else:
        tx_opts = TxOpts(preflight_commitment='processed')
    
    # Send the transaction
    try:
        response = client.send_transaction(transaction, sender, opts=tx_opts)
        print("Transaction response:", response)
    except Exception as e:
        print("Transaction failed:", e)

# Main sniping function
def snipe_sol_tokens():
    # Fetch the current price
    current_price = get_price_from_dexscreener()
    if current_price:
        print(f"Current SOL price: {current_price} USD")

        # Define your price logic here (e.g., if price falls within desired range, execute trade)
        desired_price = current_price * (1 - PRICE_IMPACT)
        
        # Pseudo-code for trading logic
        if current_price <= desired_price:
            # Execute trade
            sender_keypair = Keypair.from_secret_key(b'2dW7skExeken3qneP1Lk2aUVgJj6g7pnSvrH5sztit7dLqg28opowkwQCSmh1yXBT9kSinmFU4LZNq2hoEnQwy2s') 
            receiver_pubkey = PublicKey("Ecs8tX7rfwMUpaym9HYLEuhbFV5ouVSWND5qKupjY4ro")
            amount_to_trade = 1.0  # Define the amount to trade
            
            # Calculate slippage-adjusted amount
            min_amount_to_receive = amount_to_trade * (1 - SLIPPAGE)
            
            send_transaction(sender_keypair, receiver_pubkey, amount_to_trade)
            print(f"Traded {amount_to_trade} SOL at {current_price} USD with slippage {SLIPPAGE*100}% and price impact {PRICE_IMPACT*100}%")

            # Implement selling logic
            original_price = current_price
            amount_remaining = amount_to_trade

            while amount_remaining > 0:
                current_price = get_price_from_dexscreener()
                if current_price:
                    profit_percentage = (current_price - original_price) / original_price
                    if profit_percentage >= 0.6:
                        send_transaction(sender_keypair, receiver_pubkey, amount_remaining)
                        print(f"Sold remaining {amount_remaining} SOL at {current_price} USD (60% profit)")
                        amount_remaining = 0
                    elif profit_percentage >= 0.4 and amount_remaining > 0.3 * amount_to_trade:
                        send_transaction(sender_keypair, receiver_pubkey, 0.3 * amount_to_trade)
                        amount_remaining -= 0.3 * amount_to_trade
                        print(f"Sold 30% of tokens at {current_price} USD (40% profit)")
                    elif profit_percentage >= 0.3 and amount_remaining > 0.5 * amount_to_trade:
                        send_transaction(sender_keypair, receiver_pubkey, 0.5 * amount_to_trade)
                        amount_remaining -= 0.5 * amount_to_trade
                        print(f"Sold 50% of tokens at {current_price} USD (30% profit)")
                    elif profit_percentage <= -0.2:
                        send_transaction(sender_keypair, receiver_pubkey, amount_remaining)
                        print(f"Sold remaining {amount_remaining} SOL at {current_price} USD (20% loss)")
                        amount_remaining = 0

# Function to get Twitter score using BeautifulSoup
def get_twitter_score_bs(username):
    url = f"https://app.tweetscout.io/user/{username}"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        score_element = soup.find(class_='twitter-score')
        
        if score_element:
            score = score_element.text.strip()
            return score
        else:
            return "Twitter score element not found."
    else:
        return f"Failed to retrieve data. Status code: {response.status_code}"

# Function to get Twitter score using Selenium
def get_twitter_score_selenium(username):
    options = Options()
    options.headless = True
    service = Service('path/to/chromedriver')  # Ensure chromedriver is in your PATH or provide the full path

    with webdriver.Chrome(service=service, options=options) as driver:
        url = f"https://app.tweetscout.io/user/{username}"
        driver.get(url)
        
        try:
            score_element = driver.find_element(By.CLASS_NAME, 'twitter-score')
            score = score_element.text.strip()
            return score
        except Exception as e:
            return f"An error occurred: {str(e)}"

# Rug check function
def rug_check(contract_address, infura_url, etherscan_api_key):
    web3 = Web3(Web3.HTTPProvider(infura_url))

    if web3.isConnected():
        print("Connected to Ethereum node")
    else:
        print("Failed to connect to Ethereum node")
