import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

def demo_step(row, capital, position, data, buy_signals, sell_signals, stop):
    comission = 0.003

    if row['Buy'] and position == 0:
        entry_price = row['Close']
        shares_to_buy = capital // entry_price  # Целое количество акций
        new_position = shares_to_buy
        new_capital = capital - shares_to_buy * entry_price
        buy_signals[0].append(row['Date'])
        buy_signals[1].append(entry_price)
        df = data[data['Date'] <= row['Date']]
        plt.plot(df['Date'], df['Close'], label='Цена', color='blue')
        plt.scatter(buy_signals[0], buy_signals[1], marker='^', color='green', label='Покупка', s=100)
        plt.scatter(sell_signals[0], sell_signals[1], marker='v', color='red', label='Продажа', s=100)
        plt.xlabel('Дата')
        plt.ylabel('Цена')
        plt.legend()
        plt.grid()

        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)  # Перемещаем указатель в начало буфера
        plt.close()  # Закрываем фигуру после сохранения

        return 'Buy', new_capital, new_position, buf
    
    elif (row['Sell'] or row['Close'] < stop) and position > 0:
        new_capital = capital + position * row['Close'] * (1 - comission)

        sell_signals[0].append(row['Date'])
        sell_signals[1].append(row['Close'])


        df = data[data['Date'] <= row['Date']]
        plt.plot(df['Date'], df['Close'], label='Цена', color='blue')
        plt.scatter(buy_signals[0], buy_signals[1], marker='^', color='green', label='Покупка', s=100)
        plt.scatter(sell_signals[0], sell_signals[1], marker='v', color='red', label='Продажа', s=100)
        plt.xlabel('Дата')
        plt.ylabel('Цена')
        plt.legend()
        plt.grid()

        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)  # Перемещаем указатель в начало буфера
        plt.close()  # Закрываем фигуру после сохранения

        return 'Sell', new_capital, 0, buf
    else:
        return 'nothing', capital, position, None