import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from database import init_db, add_user, get_users, update_user
from catboost import CatBoostClassifier
from indicators import calculate_all_indicators
from demo import demo_step
from io import BytesIO
import pandas as pd
from load_api import load_df


API_TOKEN = '8001469745:AAH9FAN1dbUwAwuX2OSQp6YJOSLIqh7ezmM'  # Замените на ваш токен

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

model = CatBoostClassifier()
model.load_model('catboost_model_aflt.cbm')

buy = 0.51225478
sell = 0.49253456


aflt_data = pd.read_csv('data/aflt.csv')
data_preds = model.predict_proba(aflt_data.drop(columns=['Date', 'Unnamed: 0']))[:, 1]
aflt_data['Buy'] = data_preds > buy
aflt_data['Sell'] = data_preds < sell



@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я торговый робот, который умеет торговать тикером AFLT. Используйте команду /demo для запуска демо-режима на данных 2024 года. Используйте команду /auth для аутентификации с помощью API ключа Тинькофф и начала торговли")

@dp.message_handler(commands=['demo'])
async def demo(message: types.Message):
    # демо режим (1 секунда - 1 день)
    user_id = message.from_user.id  
    await bot.send_message(user_id, f"Запущен демо-режим на данных 2024 года по тикеру AFLT, начальный капитал 100000 рублей, 0.1 секунды - 1 день")
    capital = 100_000
    position = 0
    buy_signals = [[], []]
    sell_signals = [[], []]
    stop = 0


    for i, row in aflt_data.iterrows():
        if i == 0:
            first_close = row['Close']
        old_pos = position
        signal, capital, position, buf = demo_step(row, capital, position, aflt_data, buy_signals, sell_signals, stop)

        if signal == 'Buy':
            await bot.send_message(user_id, f"Куплено {int(position)} акций по цене {row['Close']:.2f} руб. Остаток на счете {capital:.2f} руб.")
            await bot.send_photo(user_id, photo=buf)
            stop = row['Close'] * 0.93
        elif signal == 'Sell':
            await bot.send_message(user_id, f"Продано {int(old_pos)} акций по цене {row['Close']:.2f} руб. На счете {capital:.2f} руб.")
            await bot.send_photo(user_id, photo=buf)

        last_close = row['Close']
        await asyncio.sleep(0.1)
    
    buy_n_hold = (100000 // first_close) * last_close + 100000 % first_close
    if position > 0:
        capital = capital + position*last_close
    await bot.send_message(user_id, f"Текущая стоимость активов {capital:.2f} руб. Стратегия Buy&Hold принесла бы {buy_n_hold:.2f} руб., разница между роботом и Buy&Hold {capital - buy_n_hold:.2f} руб.")


    


@dp.message_handler(commands=['auth'])
async def set_params(message: types.Message):
    # Сохраняем параметры пользователя (например, просто текст)
    if message.get_args():
        token = message.get_args()
        await message.reply(f"Токен {token} сохранен в базе данных")
    else:
        await message.reply("Укажите API токен в сообщении")
        return
    
    await add_user(message.from_user.id, token)


async def intraday_strategy():
    while True:
        users, tokens, histories = await get_users()
        
        for i in range(len(users)):
            hist = histories[i].copy()
            user_id = users[i]
            data = load_df(tokens[i])
            pred = model.predict_proba(data.drop(columns=['Date']))[:, 1]
            data['Buy'] = pred > buy
            data['Sell'] = pred < sell

            capital = hist['capital']
            position = hist['position']
            old_pos = position
            buy_signals = [[], []]
            sell_signals = [[], []]
            row = data.iloc[-1]
            signal, capital, position, buf = demo_step(row, capital, position, data, buy_signals, sell_signals, 0)

            if signal == 'Buy':
                await bot.send_message(user_id, f"Куплено {int(position)} акций по цене {row['Close']:.2f} руб. Остаток на счете {capital:.2f} руб.")
                await bot.send_photo(user_id, photo=buf)
            elif signal == 'Sell':
                await bot.send_message(user_id, f"Продано {int(old_pos)} акций по цене {row['Close']:.2f} руб. На счете {capital:.2f} руб.")
                await bot.send_photo(user_id, photo=buf)

            hist['capital'] = capital
            hist['position'] = position
            hist['sell_dates'] += [str(date) for date in sell_signals[0]]
            hist['sell_prices'] += sell_signals[1]
            hist['buy_dates'] += [str(date) for date in buy_signals[0]]
            hist['buy_prices'] += buy_signals[1]

            await update_user(user_id, hist)
            
        await asyncio.sleep(3600*24)  # Отправка сообщений каждый день

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    loop.create_task(intraday_strategy())
    executor.start_polling(dp, skip_updates=True)
   
