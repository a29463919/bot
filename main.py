import os
import discord
from discord.ext import commands, tasks
import datetime
from keep_alive import keep_alive  # 確保有這個檔案

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

reminder_data = {}

@bot.event
async def on_ready():
    print(f"✅ 登入為 {bot.user}")
    check_reminders.start()

@bot.command(name="r")
async def remind(ctx, date: str, time: str, *, thing: str):
    try:
        remind_time = datetime.datetime.strptime(f"{date} {time}", "%Y%m%d %H%M")
        now = datetime.datetime.now()
        if remind_time < now:
            await ctx.send("❗提醒時間已經過了")
            return

        guild_id = str(ctx.guild.id)
        if guild_id not in reminder_data:
            reminder_data[guild_id] = []

        reminder_data[guild_id].append({
            "user_id": ctx.author.id,
            "channel_id": ctx.channel.id,
            "time": remind_time,
            "thing": thing
        })

        await ctx.send(f"✅ 已設定提醒：{remind_time.strftime('%Y-%m-%d %H:%M')} 「{thing}」")
              print("現在時間：", datetime.datetime.now())

    except ValueError:
        await ctx.send("❗格式錯誤，請輸入：!r YYYYMMDD HHMM 事情（例如 `!r 20250608 1400 吃便當`）")

@bot.command(name="cancel")
async def cancel_reminder(ctx, index: int = None):
    guild_id = str(ctx.guild.id)
    user_id = ctx.author.id

    if guild_id not in reminder_data:
        await ctx.send("⚠️ 沒有任何提醒。")
        return

    user_reminders = [(i, r) for i, r in enumerate(reminder_data[guild_id]) if r["user_id"] == user_id]

    if not user_reminders:
        await ctx.send("⚠️ 你沒有提醒。")
        return

    if index is None:
        msg = "📋 你目前的提醒如下：\n"
        for i, (real_index, r) in enumerate(user_reminders, start=1):
            msg += f"{i}. {r['time'].strftime('%Y-%m-%d %H:%M')}：{r['thing']}\n"
        msg += "用 `!cancel 編號` 來刪除（例如 `!cancel 2`）"
        await ctx.send(msg)
        return

    if index < 1 or index > len(user_reminders):
        await ctx.send("❗無效的編號，請用 `!cancel` 查看提醒")
        return

    real_index = user_reminders[index - 1][0]
    removed = reminder_data[guild_id].pop(real_index)
    await ctx.send(f"🗑️ 已刪除提醒：「{removed['thing']}」")

@tasks.loop(seconds=30)
async def check_reminders():
    now = datetime.datetime.now()
    for guild_id in list(reminder_data.keys()):
        reminders = reminder_data[guild_id]
        for reminder in reminders[:]:
            if now >= reminder["time"]:
                channel = bot.get_channel(reminder["channel_id"])
                if channel:
                    user_mention = f"<@{reminder['user_id']}>"
                    await channel.send(f"{user_mention} 🔔 提醒你：{reminder['thing']}（時間已到）")
                reminders.remove(reminder)

keep_alive()
bot.run(TOKEN)
