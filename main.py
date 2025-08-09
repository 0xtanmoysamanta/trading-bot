import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
import datetime
import warnings
warnings.filterwarnings('ignore')

class StockBot:
    def __init__(self, symbol, period='1y', interval='1d'):
        self.symbol = symbol
        self.period = period
        self.interval = interval
        self.data = None

    def fetch_data(self):
        """Fetch historical stock data using yfinance."""
        try:
            stock = yf.Ticker(self.symbol)
            self.data = stock.history(period=self.period, interval=self.interval)
            if self.data.empty:
                raise ValueError(f"No data found for {self.symbol}")
            return True
        except Exception as e:
            print(f"Error fetching data: {e}")
            return False

    def calculate_indicators(self):
        """Calculate technical indicators: SMA, RSI, MACD."""
        if self.data is None or self.data.empty:
            print("No data available. Please fetch data first.")
            return

        # Calculate Simple Moving Averages (20-day and 50-day)
        self.data['SMA20'] = SMAIndicator(self.data['Close'], window=20).sma_indicator()
        self.data['SMA50'] = SMAIndicator(self.data['Close'], window=50).sma_indicator()

        # Calculate RSI (14-day)
        self.data['RSI'] = RSIIndicator(self.data['Close'], window=14).rsi()

        # Calculate MACD
        macd = MACD(self.data['Close'])
        self.data['MACD'] = macd.macd()
        self.data['MACD_Signal'] = macd.macd_signal()
        self.data['MACD_Hist'] = macd.macd_diff()

    def generate_signals(self):
        """Generate buy/sell signals based on indicators."""
        if self.data is None or self.data.empty:
            print("No data available. Please fetch data first.")
            return None

        signals = pd.DataFrame(index=self.data.index)
        signals['Price'] = self.data['Close']
        signals['Signal'] = 0  # 0: Hold, 1: Buy, -1: Sell

        # Strategy 1: SMA Crossover
        signals['SMA_Signal'] = np.where(
            (self.data['SMA20'] > self.data['SMA50']) & 
            (self.data['SMA20'].shift(1) <= self.data['SMA50'].shift(1)), 1, 0)
        signals['SMA_Signal'] = np.where(
            (self.data['SMA20'] < self.data['SMA50']) & 
            (self.data['SMA20'].shift(1) >= self.data['SMA50'].shift(1)), -1, 
            signals['SMA_Signal'])

        # Strategy 2: RSI (Overbought > 70, Oversold < 30)
        signals['RSI_Signal'] = np.where(self.data['RSI'] < 30, 1, 0)
        signals['RSI_Signal'] = np.where(self.data['RSI'] > 70, -1, signals['RSI_Signal'])

        # Strategy 3: MACD Crossover
        signals['MACD_Signal'] = np.where(
            (self.data['MACD'] > self.data['MACD_Signal']) & 
            (self.data['MACD'].shift(1) <= self.data['MACD_Signal'].shift(1)), 1, 0)
        signals['MACD_Signal'] = np.where(
            (self.data['MACD'] < self.data['MACD_Signal']) & 
            (self.data['MACD'].shift(1) >= self.data['MACD_Signal'].shift(1)), -1, 
            signals['MACD_Signal'])

        # Combine signals (Buy if any strategy suggests Buy, Sell if any suggests Sell)
        signals['Signal'] = signals[['SMA_Signal', 'RSI_Signal', 'MACD_Signal']].max(axis=1)
        signals['Signal'] = signals[['SMA_Signal', 'RSI_Signal', 'MACD_Signal']].min(axis=1).where(
            signals[['SMA_Signal', 'RSI_Signal', 'MACD_Signal']].min(axis=1) < 0, 
            signals['Signal'])

        return signals

    def analyze(self):
        """Perform analysis and print recommendations."""
        if not self.fetch_data():
            return

        self.calculate_indicators()
        signals = self.generate_signals()

        if signals is None:
            return

        latest = signals.iloc[-1]
        latest_price = latest['Price']
        latest_signal = latest['Signal']
        latest_rsi = self.data['RSI'].iloc[-1]
        latest_sma20 = self.data['SMA20'].iloc[-1]
        latest_sma50 = self.data['SMA50'].iloc[-1]
        latest_macd = self.data['MACD'].iloc[-1]
        latest_macd_signal = self.data['MACD_Signal'].iloc[-1]

        print(f"\nStock Analysis for {self.symbol}")
        print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Latest Closing Price: ${latest_price:.2f}")
        print(f"SMA20: ${latest_sma20:.2f}, SMA50: ${latest_sma50:.2f}")
        print(f"RSI: {latest_rsi:.2f}")
        print(f"MACD: {latest_macd:.2f}, MACD Signal: {latest_macd_signal:.2f}")
        
        if latest_signal == 1:
            print("Recommendation: BUY")
        elif latest_signal == -1:
            print("Recommendation: SELL")
        else:
            print("Recommendation: HOLD")

    def get_historical_data(self):
        """Return historical data for further analysis or plotting."""
        if self.data is None:
            self.fetch_data()
        return self.data

# Example usage
if __name__ == "__main__":
    # Initialize bot for a stock (e.g., Apple - AAPL)
    bot = StockBot(symbol="AAPL", period="1y", interval="1d")
    
    # Run analysis
    bot.analyze()
    
    # Optionally, get historical data for further use (e.g., plotting)
    historical_data = bot.get_historical_data()
    print("\nSample Historical Data:")
    print(historical_data.tail())
