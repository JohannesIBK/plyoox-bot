async def gotAddet(bot, guild):
    sID = await bot.db.fetchval('SELECT sid FROM config.guild WHERE sid = $1', guild.id)
    if sID is None:
        query = "WITH exec0 AS (INSERT INTO config.guild (sid, sname) VALUES ($1, $2)) INSERT INTO config.modules (sid) VALUES ($1)"
        await bot.db.execute(query, guild.id, guild.name)
    else:
        await bot.db.execute("UPDATE config.guild SET sname = $1 WHERE sid = $2", guild.name, guild.id)
