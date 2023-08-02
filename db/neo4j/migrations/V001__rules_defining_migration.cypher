CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (a:DiscordAccount) REQUIRE a.userId IS UNIQUE;
CREATE CONSTRAINT guild_id_unique IF NOT EXISTS
FOR (g:Guild) REQUIRE g.guildId IS UNIQUE;
CREATE INDEX interated_in_dates_index IF NOT EXISTS
FOR ()-[r:INTERACTED_IN]-() ON (r.date);
CREATE INDEX guild_metric_dates_index IF NOT EXISTS
FOR ()-[r:HAVE_METRICS]-() ON (r.date);