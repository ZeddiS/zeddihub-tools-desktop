/**
 * Shared data for game tools (Sensitivity, eDPI, Ping Tester).
 * Mirrors legacy/gui/panels/game_tools.py constants.
 */

/**
 * Sensitivity multipliers per game.
 * Formula: cm_per_360 = 36000 / (dpi * sens * mult)
 */
export const SENS_GAMES: Record<string, number> = {
  "CS2 / CS:GO":         0.022,
  "Rust":                0.1,
  "Valorant":            0.07,
  "Apex Legends":        0.022,
  "Overwatch 2":         0.0066,
  "Rainbow Six Siege":   0.00572957795,
  "PUBG":                0.00571428571,
  "Fortnite":            0.05555555556,
  "Battlefield 2042":    0.022,
  "Quake / Source":      0.022,
  "Team Fortress 2":     0.022,
  "Left 4 Dead 2":       0.022,
  "Hunt: Showdown":      0.03333333333,
  "Escape From Tarkov":  0.03,
  "DayZ":                0.09090909091,
  "ARMA 3":              0.01,
  "Splitgate":           0.022,
  "Halo Infinite":       0.0182,
  "Destiny 2":           0.0166666667,
  "The Finals":          0.022,
};

export const SENS_GAME_NAMES = Object.keys(SENS_GAMES);

/** Gaming server endpoints for ping test. */
export const PING_SERVERS: { name: string; host: string; port: number }[] = [
  { name: "Valve (CS2/TF2)",      host: "sto.steampowered.com", port: 443 },
  { name: "Valve (EU Amsterdam)", host: "ams.steampowered.com", port: 27019 },
  { name: "Cloudflare DNS",       host: "1.1.1.1",              port: 53 },
  { name: "Google DNS",           host: "8.8.8.8",              port: 53 },
  { name: "Riot Games (EU)",      host: "euw.op.gg",            port: 443 },
  { name: "Ubisoft (EU)",         host: "ubisoft.com",          port: 443 },
  { name: "Epic Games (Fortnite)",host: "epicgames.com",        port: 443 },
  { name: "Bungie (Destiny 2)",   host: "bungie.net",           port: 443 },
  { name: "Faceit EU",            host: "www.faceit.com",       port: 443 },
  { name: "Cloudflare Speed",     host: "speed.cloudflare.com", port: 443 },
];

/** CS2 pro player reference table (eDPI). */
export const CS2_PROS: { name: string; dpi: number; sens: number }[] = [
  { name: "s1mple",  dpi: 400, sens: 3.09 },
  { name: "ZywOo",   dpi: 400, sens: 2.0  },
  { name: "NiKo",    dpi: 400, sens: 1.35 },
  { name: "device",  dpi: 400, sens: 1.6  },
  { name: "ropz",    dpi: 400, sens: 1.0  },
  { name: "sh1ro",   dpi: 400, sens: 2.5  },
  { name: "m0NESY",  dpi: 400, sens: 1.4  },
  { name: "broky",   dpi: 400, sens: 1.05 },
];
