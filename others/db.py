async def gotAddet(bot, guild):
    sID = await bot.db.fetchval('SELECT sid FROM config.guild WHERE sid = $1', guild.id)
    if sID is None:
        query = """
        WITH
            exec0 AS 
                (INSERT INTO config.guild (sid, sname) VALUES ($1, $2)),
            exec1 AS
                (INSERT INTO automod.config (sid) VALUES ($1)),
            exec2 AS
                (INSERT INTO automod.blacklist (sid) VALUES ($1)),
            exec3 AS
                (INSERT INTO automod.caps (sid) VALUES ($1)),
            exec4 AS
                (INSERT INTO automod.invites (sid) VALUES ($1)),
            exec5 AS
                (INSERT INTO automod.mentions (sid) VALUES ($1)),
            exec6 AS
                (INSERT INTO config.joining (sid) VALUES ($1)),
            exec7 AS
                (INSERT INTO config.leaving (sid) VALUES ($1)),
            exec8 AS
                (INSERT INTO config.leveling (sid) VALUES ($1)),
            exec9 AS 
                (INSERT INTO automod.links (sid) VALUES ($1))
            INSERT INTO config.modules (sid) VALUES ($1)
        """

        await bot.db.execute(query, guild.id, guild.name)

    else:
        await bot.db.execute("UPDATE config.guild SET sname = $1 WHERE sid = $2", guild.name, guild.id)
