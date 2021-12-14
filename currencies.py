import time
import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta
from pykrakenapi import KrakenAPI

# Granularities as a global variable to choose from and its equivalence in seconds
g_dict = {'1m': 60, '5m': 300, '15m': 900, '30m': 1800}


class Pair:

    def __init__(self, pair, gran_desc, minutes, api):
        self.pair = pair  # Pair ticker, i.e. 'BTC/EUR'
        self.gran_desc = gran_desc  # Granularity descriptive
        self.gran_s = g_dict[gran_desc]  # Granularity in seconds
        self.minutes = minutes  # Trades historical depth
        self.k = KrakenAPI(api)  # Particular KrakenAPI instance
        # Empty dfs for trades and ohlc data
        self.trades = pd.DataFrame()
        self.ohlc = pd.DataFrame()

    # Specific exception of the Pair class
    class KrakenDataRetrievingError(Exception):
        """Failed to retrieve data from Kraken"""
        pass

    def print_info(self):
        """
        Prints the main attributes of the object
        """
        print(f'Pair: {self.pair}, Width of candlesticks: {self.gran_desc} ({self.gran_s} s.) -- '
              f'Historical depth of trades: {self.minutes} min.')

    def retrieve_minutes_depth(self):
        """
        Given a pair of currencies and a desired historical depth in minutes, return the last
        Kraken API operations with that depth.
        """
        # Loop until the last retrieved date is within X seconds of the desired
        # end date to account for a lack of recent trades.
        res = pd.DataFrame()

        # Start = Current - min (given minutes)
        f_inicial = datetime.now() - timedelta(minutes=self.minutes)
        # End = Current - 30 seconds (to prevent infinite looping)
        f_final = datetime.now() - timedelta(seconds=30)

        # To timestamp format
        f_inicial_t = f_inicial.timestamp()
        f_final_t = f_final.timestamp()

        # Accumulation of trades until the desired time is reached
        while f_inicial_t < f_final_t:
            try:
                ret, l = self.k.get_recent_trades(since=f_inicial_t, pair=self.pair)
            except self.KrakenDataRetrievingError as e:
                raise e

            res = ret[:] if res.empty else ret.append(res)

            # In the next epoch, 'since' will be 1 ns after the
            # time of the most recent trade of the current subset
            f_inicial_t = res.index[0]
            f_inicial_t = f_inicial_t.timestamp() + 0.000000000000001

            # Sleep 3s. to avoid API rate limit
            time.sleep(3)

        # print(f'Size before removing duplicates: {res.shape}')
        res = res[~res.index.duplicated(keep='first')]
        # print(f'Size after removing duplicates: {res.shape}')

        # return res.sort_index()
        self.trades = res.sort_index()

    @staticmethod
    def calculate_vwap(df):
        """
        Given a subset of trades, calculate the volume-weighted average price (VWAP)
        """
        try:
            vwap = sum(df['price'] * df['volume']) / sum(df['volume'])
        except ZeroDivisionError:
            vwap = 0.0

        return vwap

    @staticmethod
    def round_to_upper_dt(dt, g):
        """
        Given a datetime 'dt', returns the following round time associated with it,
        based on the granularity 'g'. The purpose is that the beggining of
        each interval (candle) is round and can be represented aesthetically.

                Parameters:
                        dt (datetime): A datetime to obtain its rounding
                        g (timedelta): Granularity in seconds (1, 5, 15, 30 min. or 1 h.)

                Returns:
                        rounded dt (datetime): New (rounded) datetime

        Example:

        Let dt_ex = 2021-12-05 13:38:49.240554

        1 minute granularity:
        round_to_upper_dt(dt_ex, 60) = 2021-12-05 13:39:00

        5 minutes granularity:
        round_to_upper_dt(dt_ex, 300) = 2021-12-05 13:40:00

        1 hour granularity:
        round_to_upper_dt(dt_ex, 3600) = 2021-12-05 14:00:00
        """
        # When converting using to_pydatetime() we are warned that the last decimal
        # places, corresponding to the nanoseconds, are being discarded. Since the
        # minimum granularity is 1 second, we can omit these digits. Therefore,
        # this particular type of warning is filtered out to prevent verbosity.
        warnings.filterwarnings("ignore",
                                message="Discarding nonzero nanoseconds in conversion")
        try:
            return dt + (datetime.min - dt.to_pydatetime()) % g
        except ZeroDivisionError:
            print('Granularity is equal to 0.')

    def generate_ohlc_from_trades(self, res, i_trades, i):
        """
        This is the core function for calculating VWAP, since it returns a candle (OHLC data) from a subset of trades.

                Parameters:
                        res (dataframe): Candles dataset with uninformed columns
                        i_trades (dataframe): A subset of trades
                        i (int): i-th interval

                Returns:
                        res (dataframe): Candles dataset containing new info. for
                                          the current i-th subset of trades
        """
        # Generate OHLC data: Selected functions on the aggregated set of trades
        if len(i_trades) > 0 and not i_trades.empty:
            # Open price
            res.loc[res.index[i], 'open'] = i_trades['price'].iloc[0]
            # High price
            res.loc[res.index[i], 'high'] = np.max(i_trades['price'])
            # Low price
            res.loc[res.index[i], 'low'] = np.min(i_trades['price'])
            # Close price
            res.loc[res.index[i], 'close'] = i_trades['price'].iloc[-1]
            # Volume-weighted average price (VWAP)
            res.loc[res.index[i], 'vwap'] = self.calculate_vwap(i_trades)
            # Total volume
            res.loc[res.index[i], 'volume'] = np.sum(i_trades['volume'])
            # Total number of trades
            res.loc[res.index[i], 'count'] = i_trades.shape[0]

        else:
            # If there are no trades in the interval: Impute O,H,L,C from the previous interval. Also impute VWAP,
            # since we don't want its value in the graph to decay to 0 and mess up the visualization in that step.
            for col in ['open', 'high', 'low', 'close', 'vwap']:
                res.loc[res.index[i], str(col)] = res.loc[res.index[i - 1], str(col)]
            # Volume & Count equal to 0.
            res.loc[res.index[i], 'volume'] = 0
            res.loc[res.index[i], 'count'] = 0

        return res

    @staticmethod
    def column_format(res, pos):
        """
        Format OHLC dataframe columns

                Parameters:
                        res: Unformatted ohlc dataframe

                        pos: Number of digits (precision)

                Returns:
                        res: Formatted ohlc dataframe
        """
        prec = str(pos)
        format_mapping = {'open': '{:.' + prec + 'f}', 'high': '{:.' + prec + 'f}',
                          'low': '{:.' + prec + 'f}', 'close': '{:.' + prec + 'f}',
                          'vwap': '{:.' + prec + 'f}', 'volume': '{:.6f}'}

        for key, value in format_mapping.items():
            res[key] = res[key].apply(value.format)

        # Conversion to float in order to avoid further plotting issues
        float_cols = ['open', 'high', 'low', 'close', 'vwap', 'volume']
        for col in float_cols:
            try:
                res[col] = pd.to_numeric(res[col], errors='coerce', downcast='float')
            except ValueError:
                pass

        # Same, but to integer
        try:
            res['count'] = pd.to_numeric(res['count'], errors='coerce', downcast='integer')
        except ValueError:
            pass

        # Although 'coerce' fills in any conflicting data with NaN, the try catch structure is preserved so that
        # no conversion is performed in case of error.

        return res

    def get_ohlc(self):
        """
        Starting from the trades dataset and granularity, returns the candles with aggregated
        information, such as: Open, High, Low, Close, VWAP, Volume and # trades.
        """
        # Copy the transaction time as a new column
        self.trades['dtime'] = self.trades.index

        # Capture the whole time frame, creating start & end
        orig_since = self.trades['dtime'].iloc[0]
        orig_till = self.trades['dtime'].iloc[-1]

        # Obtain roundings of start & end points
        since = self.round_to_upper_dt(orig_since, timedelta(minutes=(self.gran_s / 60)))
        till = self.round_to_upper_dt(orig_till, timedelta(minutes=(self.gran_s / 60)))

        # Create an initial data table with entries from 'since' to 'till',
        # which will contain information in 'gran' second intervals.
        timestamps = pd.date_range(since, till, freq=str(self.gran_s) + 's')
        d_cols = ['time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count']
        res = pd.DataFrame(index=timestamps, columns=d_cols)

        # We ignore this type of warning as it alerts of something that does not affect the calculation.
        warnings.simplefilter(action='ignore', category=FutureWarning)

        # Creates time column with the start of the interval in unix time
        res['time'] = res.index.astype(np.int64) // 1000000000

        # Step through each interval in steps of 'gran' seconds
        for i in range(0, len(res.index)):
            # Select the i_trades trades between index and index+1
            i_trades = self.trades[(self.trades['dtime'] >= res.index[i]) &
                                   (self.trades['dtime'] < (res.index[i] +
                                                            timedelta(seconds=self.gran_s)))]

            # Generate OHLC (candles) from trades within the i-th interval
            res = self.generate_ohlc_from_trades(res, i_trades, i)

        # Truncate index to the second for aesthetic purposes
        res.index = res.index.floor('s')

        # Final column formatting: 1 decimal places
        res = self.column_format(res, 1)

        self.ohlc = res
