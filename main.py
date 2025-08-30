import requests
import json
from datetime import datetime, timedelta
import time
import random

class BinanceCandlestickAnalyzer:
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
        # Headers do obejścia blokad
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def get_top_coins(self, limit=50):
        """Pobiera najpopularniejsze coiny na podstawie 24h volume"""
        # Lista fallback coinów gdyby API nie działało
        fallback_coins = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT', 
            'SOLUSDT', 'DOTUSDT', 'DOGEUSDT', 'AVAXUSDT', 'SHIBUSDT',
            'MATICUSDT', 'LTCUSDT', 'LINKUSDT', 'ATOMUSDT', 'FTMUSDT',
            'NEARUSDT', 'ALGOUSDT', 'XLMUSDT', 'VETUSDT', 'FILUSDT',
            'TRXUSDT', 'ETCUSDT', 'THETAUSDT', 'ICPUSDT', 'EOSUSDT',
            'AAVEUSDT', 'MKRUSDT', 'COMPUSDT', 'SNXUSDT', 'YFIUSDT',
            'UNIUSDT', 'SUSHIUSDT', 'CAKEUSDT', 'ALPHAUSDT', 'CHZUSDT',
            'ENJUSDT', 'MANAUSDT', 'SANDUSDT', 'GALAUSDT', 'AXSUSDT',
            'FLOWUSDT', 'FTMUSDT', 'ONEUSDT', 'HARMONYUSDT', 'ZILUSDT',
            'WAVESUSDT', 'KSMUSDT', 'QNTUSDT', 'BATUSDT', 'ZRXUSDT'
        ]
        
        try:
            # Próba 1: Podstawowe API
            url = f"{self.base_url}/ticker/24hr"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            tickers = response.json()
            usdt_pairs = [ticker for ticker in tickers if ticker['symbol'].endswith('USDT')]
            sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['volume']), reverse=True)
            
            return [pair['symbol'] for pair in sorted_pairs[:limit]]
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Problem z API Binance (błąd {e})")
            print(f"🔄 Używam listy fallback coinów...")
            return fallback_coins[:limit]
        except Exception as e:
            print(f"⚠️  Nieoczekiwany błąd: {e}")
            print(f"🔄 Używam listy fallback coinów...")
            return fallback_coins[:limit]
    
    def get_kline_data(self, symbol, interval='1d', limit=5):
        """Pobiera dane świeczek dla danego symbolu"""
        try:
            url = f"{self.base_url}/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            # Dodanie losowego opóźnienia
            time.sleep(random.uniform(0.1, 0.3))
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            klines = response.json()
            candles = []
            
            for kline in klines:
                candle = {
                    'timestamp': int(kline[0]),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                }
                candles.append(candle)
            
            return candles
        except Exception as e:
            print(f"⚠️  Błąd dla {symbol}: {e}")
            return []
    
    def is_doji(self, candle, tolerance=0.1):
        """Sprawdza czy świeca to Doji (open ≈ close)"""
        body_size = abs(candle['close'] - candle['open'])
        full_range = candle['high'] - candle['low']
        
        if full_range == 0:
            return False
        
        body_ratio = body_size / full_range
        return body_ratio <= tolerance
    
    def is_hammer(self, candle):
        """Sprawdza czy świeca to Hammer (długi dolny cień, krótki korpus)"""
        body_size = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        if body_size == 0:
            return False
        
        # Hammer: dolny cień ≥ 2x korpus, górny cień ≤ 0.5x korpus
        return (lower_shadow >= 2 * body_size and 
                upper_shadow <= 0.5 * body_size and
                lower_shadow > 0)
    
    def is_shooting_star(self, candle):
        """Sprawdza czy świeca to Shooting Star (długi górny cień, krótki korpus)"""
        body_size = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        if body_size == 0:
            return False
        
        # Shooting Star: górny cień ≥ 2x korpus, dolny cień ≤ 0.5x korpus
        return (upper_shadow >= 2 * body_size and 
                lower_shadow <= 0.5 * body_size and
                upper_shadow > 0)
    
    def is_engulfing(self, prev_candle, current_candle):
        """Sprawdza czy wystąpił wzorzec Engulfing"""
        prev_body_top = max(prev_candle['open'], prev_candle['close'])
        prev_body_bottom = min(prev_candle['open'], prev_candle['close'])
        curr_body_top = max(current_candle['open'], current_candle['close'])
        curr_body_bottom = min(current_candle['open'], current_candle['close'])
        
        # Bullish Engulfing: poprzednia czerwona, obecna zielona i większa
        bullish = (prev_candle['close'] < prev_candle['open'] and
                  current_candle['close'] > current_candle['open'] and
                  curr_body_bottom < prev_body_bottom and
                  curr_body_top > prev_body_top)
        
        # Bearish Engulfing: poprzednia zielona, obecna czerwona i większa
        bearish = (prev_candle['close'] > prev_candle['open'] and
                  current_candle['close'] < current_candle['open'] and
                  curr_body_bottom < prev_body_bottom and
                  curr_body_top > prev_body_top)
        
        return bullish, bearish
    
    def is_marubozu(self, candle, tolerance=0.05):
        """Sprawdza czy świeca to Marubozu (brak cieni)"""
        body_size = abs(candle['close'] - candle['open'])
        full_range = candle['high'] - candle['low']
        
        if full_range == 0:
            return False
        
        body_ratio = body_size / full_range
        return body_ratio >= (1 - tolerance)
    
    def analyze_candlestick_patterns(self, symbol):
        """Analizuje wzorce świec japońskich dla danego symbolu"""
        candles = self.get_kline_data(symbol, '1d', 5)
        
        if len(candles) < 2:
            return None
        
        latest_candle = candles[-1]
        prev_candle = candles[-2] if len(candles) >= 2 else None
        
        patterns = []
        
        # Sprawdzanie wzorców dla najnowszej świecy
        if self.is_doji(latest_candle):
            patterns.append("Doji")
        
        if self.is_hammer(latest_candle):
            patterns.append("Hammer")
        
        if self.is_shooting_star(latest_candle):
            patterns.append("Shooting Star")
        
        if self.is_marubozu(latest_candle):
            if latest_candle['close'] > latest_candle['open']:
                patterns.append("Bullish Marubozu")
            else:
                patterns.append("Bearish Marubozu")
        
        # Sprawdzanie wzorców dwuświecowych
        if prev_candle:
            bullish_eng, bearish_eng = self.is_engulfing(prev_candle, latest_candle)
            if bullish_eng:
                patterns.append("Bullish Engulfing")
            if bearish_eng:
                patterns.append("Bearish Engulfing")
        
        return {
            'symbol': symbol,
            'timestamp': datetime.fromtimestamp(latest_candle['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
            'ohlc': {
                'open': latest_candle['open'],
                'high': latest_candle['high'],
                'low': latest_candle['low'],
                'close': latest_candle['close']
            },
            'patterns': patterns,
            'price_change': ((latest_candle['close'] - latest_candle['open']) / latest_candle['open']) * 100
        }
    
    def run_analysis(self):
        """Uruchamia analizę dla top 50 coinów"""
        print("🔍 Pobieranie listy najpopularniejszych coinów...")
        top_coins = self.get_top_coins(50)
        
        if not top_coins:
            print("❌ Nie udało się pobrać listy coinów")
            return
        
        print(f"✅ Znaleziono {len(top_coins)} coinów")
        print("\n" + "="*80)
        print("📊 ANALIZA WZORCÓW ŚWIEC JAPOŃSKICH")
        print("="*80)
        
        coins_with_patterns = []
        
        for i, symbol in enumerate(top_coins, 1):
            print(f"Analizuję {symbol} ({i}/{len(top_coins)})...", end=' ')
            
            result = self.analyze_candlestick_patterns(symbol)
            
            if result and result['patterns']:
                coins_with_patterns.append(result)
                print(f"✅ Znaleziono wzorce: {', '.join(result['patterns'])}")
            else:
                print("⚪ Brak wzorców")
            
            # Małe opóźnienie żeby nie przeciążyć API
            time.sleep(0.1)
        
        # Wyświetlanie wyników
        print("\n" + "="*80)
        print("🎯 PODSUMOWANIE - COINY Z WZORCAMI ŚWIEC JAPOŃSKICH")
        print("="*80)
        
        if not coins_with_patterns:
            print("❌ Nie znaleziono żadnych znaczących wzorców świec japońskich")
            return
        
        for result in coins_with_patterns:
            print(f"\n🪙 {result['symbol']}")
            print(f"⏰ Data: {result['timestamp']}")
            print(f"📈 OHLC: O:{result['ohlc']['open']:.4f} H:{result['ohlc']['high']:.4f} L:{result['ohlc']['low']:.4f} C:{result['ohlc']['close']:.4f}")
            print(f"📊 Zmiana: {result['price_change']:+.2f}%")
            print(f"🕯️  Wzorce: {', '.join(result['patterns'])}")
        
        print(f"\n📋 Łącznie znaleziono wzorce w {len(coins_with_patterns)} coinach z {len(top_coins)} sprawdzonych")
        
        # Statystyki wzorców
        pattern_counts = {}
        for result in coins_with_patterns:
            for pattern in result['patterns']:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        print("\n📈 STATYSTYKI WZORCÓW:")
        for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {pattern}: {count} wystąpień")

def main():
    print("🚀 Binance Candlestick Pattern Analyzer")
    print("=" * 50)
    
    analyzer = BinanceCandlestickAnalyzer()
    
    try:
        analyzer.run_analysis()
    except KeyboardInterrupt:
        print("\n⏹️  Analiza przerwana przez użytkownika")
    except Exception as e:
        print(f"\n❌ Wystąpił błąd: {e}")

if __name__ == "__main__":
    main()