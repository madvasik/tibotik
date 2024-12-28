import numpy as np


def calculate_rsi(df, window=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    return df

def calculate_stochastic(df, k_window=14, d_window=3):
    high = df['High'].rolling(window=k_window).max()
    low = df['Low'].rolling(window=k_window).min()

    df['%K'] = 100 * ((df['Close'] - low) / (high - low))
    df['%D'] = df['%K'].rolling(window=d_window).mean()

    return df

def calculate_bollinger_bands(df, window=20, num_std_dev=2):
    rolling_mean = df['Close'].rolling(window=window).mean()
    rolling_std = df['Close'].rolling(window=window).std()

    df['Middle Band'] = rolling_mean
    df['Upper Band'] = rolling_mean + (rolling_std * num_std_dev)
    df['Lower Band'] = rolling_mean - (rolling_std * num_std_dev)

    return df

def calculate_macd(df, short_window=12, long_window=26, signal_window=9):
    # Рассчитываем короткую и длинную экспоненциальные скользящие средние
    short_ma = df['Close'].ewm(span=short_window, adjust=False).mean()
    long_ma = df['Close'].ewm(span=long_window, adjust=False).mean()

    # Рассчитываем MACD
    df['MACD'] = short_ma - long_ma

    # Рассчитываем сигнальную линию
    df['MACD_Signal'] = df['MACD'].ewm(span=signal_window, adjust=False).mean()

    return df

def calculate_atr(df, period=14):
    # Копируем DataFrame для работы
    df = df.copy()

    # Рассчитываем True Range
    df['Previous_Close'] = df['Close'].shift(1)
    df['High_Low'] = df['High'] - df['Low']
    df['High_PrevClose'] = abs(df['High'] - df['Previous_Close'])
    df['Low_PrevClose'] = abs(df['Low'] - df['Previous_Close'])

    # Находим максимальное значение среди True Range
    df['True_Range'] = df[['High_Low', 'High_PrevClose', 'Low_PrevClose']].max(axis=1)

    # Рассчитываем ATR как скользящее среднее True Range
    df['ATR'] = df['True_Range'].rolling(window=period).mean()

    # Удаляем временные колонки, которые больше не нужны
    df.drop(columns=['Previous_Close', 'High_Low', 'High_PrevClose', 'Low_PrevClose', 'True_Range'], inplace=True)

    return df

def calculate_aroon(df, period=14):
    # Копируем DataFrame для работы
    df = df.copy()

    # Рассчитываем Aroon Up
    aroon_up = 100 * (period - (df['High'].rolling(window=period).apply(lambda x: x.argmax(), raw=True))) / period

    # Рассчитываем Aroon Down
    aroon_down = 100 * (period - (df['Low'].rolling(window=period).apply(lambda x: x.argmin(), raw=True))) / period

    # Добавляем результаты в DataFrame
    df['Aroon_Up'] = aroon_up
    df['Aroon_Down'] = aroon_down

    return df

def calculate_parabolic_sar(df, acceleration_factor=0.02, max_acceleration=0.2):
    # Инициализация переменных
    sar = [df['Low'].iloc[0]]  # Начальное значение SAR
    ep = df['High'].iloc[0]  # Extreme Point (максимум)
    af = acceleration_factor  # Коэффициент ускорения
    trend = 1  # 1 - восходящий тренд, -1 - нисходящий тренд

    for i in range(1, len(df)):
        if trend == 1:
            sar.append(sar[i-1] + af * (ep - sar[i-1]))
            if df['Low'].iloc[i] < sar[i]:  # Если цена пробивает SAR
                trend = -1
                sar[i] = ep  # Переход в нисходящий тренд
                ep = df['Low'].iloc[i]  # Обновляем EP
                af = acceleration_factor  # Сбрасываем AF
            else:
                if df['High'].iloc[i] > ep:
                    ep = df['High'].iloc[i]
                    af = min(af + acceleration_factor, max_acceleration)  # Увеличиваем AF
        else:
            sar.append(sar[i-1] + af * (ep - sar[i-1]))
            if df['High'].iloc[i] > sar[i]:  # Если цена пробивает SAR
                trend = 1
                sar[i] = ep  # Переход в восходящий тренд
                ep = df['High'].iloc[i]  # Обновляем EP
                af = acceleration_factor  # Сбрасываем AF
            else:
                if df['Low'].iloc[i] < ep:
                    ep = df['Low'].iloc[i]
                    af = min(af + acceleration_factor, max_acceleration)  # Увеличиваем AF

    df['Parabolic_SAR'] = sar
    return df

def calculate_ivar(df, n=5):
    df['iVAR'] = df['Close'].rolling(window=2**n).std() / np.max(df['Close'].rolling(window=2**n).std())

    return df

def calculate_mfi(data_, period=14):
    data = data_.copy()
    # Расчет Typical Price
    data['Typical Price'] = (data['High'] + data['Low'] + data['Close']) / 3

    # Расчет Money Flow
    data['Money Flow'] = data['Typical Price'] * data['Vol']

    # Создание колонок для положительного и отрицательного денежного потока
    data['Positive Money Flow'] = 0
    data['Negative Money Flow'] = 0

    for i in range(1, len(data)):
        if data['Typical Price'].iloc[i] > data['Typical Price'].iloc[i - 1]:
            data['Positive Money Flow'].iloc[i] = data['Money Flow'].iloc[i]
        else:
            data['Negative Money Flow'].iloc[i] = data['Money Flow'].iloc[i]

    # Расчет скользящих сумм
    data['Positive Money Flow Sum'] = data['Positive Money Flow'].rolling(window=period).sum()
    data['Negative Money Flow Sum'] = data['Negative Money Flow'].rolling(window=period).sum()

    # Расчет MFI
    data_['MFI'] = 100 - (100 / (1 + (data['Positive Money Flow Sum'] / data['Negative Money Flow Sum'])))

    return data_

def calculate_all_indicators(data):
    df = data.copy()
    df = calculate_rsi(df)
    df = calculate_aroon(df)
    df = calculate_atr(df)
    df = calculate_bollinger_bands(df)
    df = calculate_ivar(df)
    df = calculate_macd(df)
    df = calculate_parabolic_sar(df)
    df = calculate_stochastic(df)
    df = calculate_mfi(df)

    df['Close-Upper'] = df['Close'] - df['Upper Band']
    df['Lower-Close'] = df['Lower Band'] - df['Close']
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    df['PSAR_Hist'] = df['Close'] - df['Parabolic_SAR']

    df['Close-Open'] = df['Close'] - df['Open']
    df['High-Low'] = df['High'] - df['Low']

    for i in range(1, 6):
        df[f'PSAR_Hist-{i}'] = df['PSAR_Hist'].shift(i)
        df[f'MACD_Hist-{i}'] = df['MACD_Hist'].shift(i)

    df = df.dropna()
    cols = ['Open', 'High', 'Low', 'Close', 'Vol', 'RSI',
       'Aroon_Up', 'Aroon_Down', 'ATR', 'Date',
       'iVAR', '%K', 'Close-Open', 'High-Low',
       '%D', 'MFI', 'Close-Upper', 'Lower-Close', 'MACD_Hist', 'PSAR_Hist',
       'PSAR_Hist-1', 'MACD_Hist-1', 'PSAR_Hist-2', 'MACD_Hist-2',
       'PSAR_Hist-3', 'MACD_Hist-3', 'PSAR_Hist-4', 'MACD_Hist-4',
       'PSAR_Hist-5', 'MACD_Hist-5']

    df = df[cols]
    return df