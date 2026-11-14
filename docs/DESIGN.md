# Pandaborn - Factions: design

Revision 3, 2026-11-14. Rewritten against `docs/tech/game-mechanics.md` (how the game really behaves),
`docs/tech/water.md` and `docs/tech/two-peoples.md`. The full list of buildings, goods and plants is in
`docs/CONTENT.md`. Numbers are placeholders until the colony model and play tests.

The owner has given the orchestrator executive authority over design, with one yardstick: **player
satisfaction**. Changes and their reasons are logged at the end of this file.

## The test for every idea

1. Would a player enjoy it, and notice it within a minute?
2. Does it work the way the game actually runs, hour by hour? (Checked against the mechanics reference.)
3. Can a new player ignore it and still be fine?
4. Will it survive a game update?

## Fixed by the owner

* One faction, the **Inkpaws** (giant pandas), with **Ringtails** (red pandas) living among them.
* Core identity: **lead the water** rather than hold it back.
* The two peoples keep different hours. The system must be smooth to learn; if it is not, fall back to one
  people with coat variety.
* Signature events are in scope.
* Art volume about what Emberpelts ships, all generated in code / by AI and disclosed.
* Unlocked from the start. Tone cozy and whimsical. Steam Workshop and mod.io, Windows and Mac.

## Pitch

Beavers hold water back; the Inkpaws lead it. Two panda peoples share one village in the misty bamboo
highlands: the big ones work the day and laze through golden afternoons, the small ones keep the lanterns lit
at night, and together they guide mountain water down bamboo flumes into rice terraces.

## Setting

Sichuan, where giant and red pandas really live. One real place, used closely.

| Real thing | In the mod |
|---|---|
| Dujiangyan, a 2,200-year-old system that waters a plain with no dam | Flumes, spouts and norias |
| Rice terraces, hill tea, Sichuan pepper, pickles, hot pot | Farming and food |
| Bamboo mass flowering, which really starves pandas | The Great Flowering |
| The Wooden Ox, a walking hauler of Sichuan legend | The faction's bots |
| The sky lantern, credited to the same inventor | The wonder and the festival |
| Panda nurseries | The Kindergarten |
| The Leshan Giant Buddha | The Great Sitting Panda monument |
| Red pandas being active from dusk to dawn | The Ringtails' hours |

## What the game allows (the facts this design stands on)

| Fact | Consequence for the design |
|---|---|
| Work is one colony-wide block that always starts at dawn; default 16 of 24 hours; night is the last 8 | Inkpaws cannot have a midday break. Their leisure is the afternoon and evening |
| Workers on shift ignore every need that is not critical; attractions are used only off duty | Leisure buildings only matter if pandas have off-duty daylight |
| Colonists sleep about 3 hours, late at night | Evenings are long and free |
| Area effects (decorations, lanterns) reach anyone in range at any hour, including at work | Decorating workplaces has real value |
| Workshop workers fetch their own inputs and carry out their own outputs; haulers only help, with double loads | A colony never needs haulers to function; they are a boost |
| Haulers never supply building sites; builders do, and building is mostly walking | Faster building means better carriers and lighter materials, not more haulers |
| Carrying anything halves walking speed, so load size decides hauling | A good carrier lifts a lot. Walking speed helps everything else |
| Every food fills the same hunger; a dish's bonus needs only a bite every few days | Variety is cheap in volume. The staple can be anything |
| Plants grow on fixed timers; drought only starts a dying countdown; death is permanent; planted plants do not spread | "Regrows by itself" means quick replanting by workers unless we add code |
| Night changes nothing in play | Night work is a rhythm and a mood, plus the gain of work continuing while others rest |
| A workplace holds one kind of worker | Each people has its own buildings |

## Pillar 1 — Lead the water

Inkpaws keep terrace walls, weirs and floodgates, so every vanilla map plays from day one. What they add is a
toolkit for shallow water at many heights.

| Tool | What it does |
|---|---|
| Bamboo spout | Holds the pool below it at a shallow set depth. A paddy that looks after itself |
| Bamboo flume | An open channel one tile wide. Water runs one way along it, level or downhill, on the ground or on trestles, and cannot leak sideways. Corners use turning boxes |
| Noria | Sits in a current and lifts water with no workers |
| Treadwheel lift | The same lift where there is no current, turned by a Ringtail |
| Dew collector | A trickle of drinking water at dawn, even in drought |
| Clay cisterns | Water storage, from day one |

Why it is fun: water visibly runs along something the player drew across a hillside, farmland can go anywhere a
flume can reach, and each piece has one clear job.

## Pillar 2 — Every kind of land has a use

| Zone | Plants |
|---|---|
| Flooded | Rice (up to one block deep), lotus (deeper) |
| Moist | Bamboo, cabbage, soybean, persimmon and lacquer trees |
| Dry | Tea bushes, Sichuan pepper |

* To a beaver, dry land is dead land. To an Inkpaw it is tea country, and a drought does not touch it.
* Dry-ground plants are luxuries and ingredients, never staple calories, because dry land is unlimited.

### Bamboo, the fast tree

* It uses three jobs players already know: a grove keeper plants it, a forager picks shoots, a woodcutter cuts
  poles. The grove keeper is free to unlock.
* Shoots are ready within three days, because a Normal start has under four days of food.
* **Poles are the Inkpaws' planks, and there is no mill.** Poles are light, so builders carry more per trip
  and everything goes up faster. Fast building is the first thing a player will feel.
* Bamboo is thirsty: it is the first plant to die in a drought. It grows back fast, and grove keepers replant
  marked groves without being asked.
* Two kinds, river bamboo (fast) and cloud bamboo (slower, hardier). This matters in the Flowering.
* Spreading into neighbouring soil needs added code and is decided after the prototype.

## Pillar 3 — The golden afternoon

* **Inkpaws work a shorter day, faster.** A new Inkpaws game starts at twelve working hours instead of sixteen,
  and Inkpaws work quicker to match. The four daylight hours they gain are off duty: hammocks, the teahouse,
  the slide, the hot spring, the kindergarten. This is how "lazy, content pandas" becomes something the player
  watches, inside the game's real schedule.
* **Overwork backfires.** A Rest need, filled in hammocks and on nap platforms, cannot keep up with a
  sixteen-hour day. Rested pandas work fast; tired ones do not. The slider stays in the player's hands.
* **Decorate the workplace.** Lanterns and gardens reach pandas at work, so beauty around workshops pays.
* **Cooking is the ladder.** Shoots keep pandas alive; each dish is a recognisable Sichuan food and a step up
  in wellbeing. Tea is a drink with its own need and makes water go further.
* **Cubs are a joy.** Adults gain wellbeing from the Panda Kindergarten.
* **Population the player can trust.** Inkpaws breed slowly, live long, and each home has a "welcome cubs"
  switch. Runaway breeding into famine, a familiar vanilla frustration, cannot happen by accident.

## Pillar 4 — Two peoples, one village

### The one rule

**Inkpaws keep the day. Ringtails keep the night.**

### How it is learned

1. The game opens with Inkpaws only, and plays like a familiar faction with new crops and tools.
2. The first **loft** — a small lantern-lit home on a rooftop — brings a family of Ringtails. One message, one
   rule, at a moment the player chose.
3. Ringtails work in their own small buildings. There is nothing to configure.
4. A player who never builds a loft has a complete colony.

### A day in the village

| Hours | Inkpaws | Ringtails |
|---|---|---|
| Dawn to mid-morning | At work | Asleep, then at leisure in the gardens |
| Late morning to noon | At work | Starting work: both peoples busy together |
| Afternoon | Off duty: the golden afternoon | At work |
| Evening | Off duty, then asleep | At work under lanterns |
| Night | Asleep | At work |

Each people rests in the spaces the other is keeping. Neither serves the other: the Inkpaws grow, cook and
build by day; the Ringtails carry, craft, perform and watch the stars by night.

### What Ringtails do

| Building | Job |
|---|---|
| Courier Loft | Hauling: tops up workshop inputs and clears outputs so Inkpaws start the day with full shelves |
| Scaffolders' Loft | Builders: sites are stocked and raised overnight |
| Forager's Nest | Gathering, including bamboo mushrooms from standing groves |
| Lantern and firework workshops | Festival crafts |
| Treadwheel and treadwheel lift | Power and water lifting; a wheel turns faster under a quick walker |
| Star Tower | Science from the night sky |
| Opera Stage | Evening performances for off-duty Inkpaws |

### How they differ

| | Inkpaws | Ringtails |
|---|---|---|
| Strength | Lift more; work faster | Walk faster |
| Homes | Dens, courtyard houses: roomy, few beds | Lofts: tiny, on roofs and scaffolds |
| Lives | Long; cubs arrive slowly | Shorter; kits arrive sooner |

Differences are moderate. Food and wellbeing rules are the same for both, so there is one set of numbers to
learn. The interface shows a sun or a moon.

### What the player gains

* Building work and hauling continue through the night.
* Leisure buildings are shared across two shifts instead of crowding in one evening.
* A village that is alive at every hour, with lanterns lit and small red figures at work.
* The mix is the player's: more dens or more lofts.

### The gate

A prototype must show Ringtails holding their own jobs, working these hours, sleeping, surviving save and
reload, and leaving Folktails games untouched. If it fails, or proves fragile, the faction ships with one
people and Ringtail coats as variety. Nothing else in this design depends on Ringtails.

## Pillar 5 — A third rhythm

### The Great Flowering

* Never before a set cycle; then every few cycles, forecast like a drought. One of the two bamboo kinds
  blooms and dies across the map.
* The hillsides turn gold, and pandas enjoy the blossoms while the player counts the food.
* Answers, all visible in advance: grow both kinds, lean on rice and persimmons, keep a cellar of pickles.
* Cutting the dead groves yields **bamboo rice**, the rarest food in the mod.
* Grove keepers replant by themselves afterwards.
* A setting offers off, rare or normal.

### Lantern Festival

* Called by the player from the Festival Square, at most once per cycle, by spending stockpiled lanterns,
  fireworks and feast food.
* For one evening and night both peoples are off duty together: dancing, rising lanterns, fireworks.
* Rewards: a long-lasting festive wellbeing boost, a wave of cubs and kits, and one step of **Tradition**, a
  permanent count that unlocks lantern colours and decorations.

### The Long Nap (later)

In a drought the player can send the Inkpaws to bed, where they need far less food and water, while the
Ringtails keep the village running. It is all custom code and is built last.

## Pillar 6 — Legend as late game

* **Wooden Oxen** replace bots: slow, tireless haulers with enormous loads.
* **Kite windmills** and **treadwheels** replace fuel engines.
* **Bamboo scaffolding and rope bridges** make tall building cheap and light.
* **The Great Sitting Panda**, carved into a cliff, is the top monument.
* **The wonder** is a colossal sky lantern that carries seeds over the wasteland.

## The first hour (Normal difficulty)

| When | What the player does | What they learn |
|---|---|---|
| First minutes | Nine Inkpaws and four cubs, some berries, no water. Places a water carrier, forager's post and woodcutter | Familiar opening |
| Day 1 | Marks a bamboo grove by the river. Builds dens from logs | Bamboo is a tree you farm |
| Days 2–3 | First shoots and first poles. Buildings go up noticeably faster | Poles need no mill and are light |
| Days 3–8 | Steamer, hammocks, cisterns. Notices pandas off duty in the afternoon | The golden afternoon |
| First drought | Bamboo dies back; cisterns and stored shoots carry the village; groves are replanted by themselves | Droughts are survivable |
| Cycle 2 | First spout-fed paddy; a tea slope on dry ground; pickles | Three zones; a pantry |
| Cycle 2–3 | First flume to a higher terrace; first loft, and the Ringtails arrive | Leading water; the one rule |
| Cycle 3–4 | Cubs, the Kindergarten, lanterns, the first Festival | Happiness pays |
| Later | Flowering forecast, cloud bamboo, Wooden Oxen, the Great Sitting Panda, the sky lantern | The long game |

## Look

* Palette: ink black and white, bamboo green, lacquer red, paper cream, tea green.
* Vanilla buildings re-themed through the faction's own materials where that proves possible; new models from
  one code-driven kit of parts (poles, lashings, woven panels, curved tile roofs, paper screens, lanterns) for
  everything that carries identity.
* Lanterns and paper windows glow at night.
* Outfits: conical bamboo hats, straw capes, headbands; shoulder poles for couriers.
* Characters: the Reskin's proportions and coats for Inkpaws; a true red panda body for Ringtails if the
  character pipeline allows, a smaller red-coated body if not.

## What sinks faction mods (design against these)

1. Breaking on game updates: data first, small defensive code, automated tests, features that switch
   themselves off rather than crash.
2. Dependency chains: none required.
3. Id clashes: everything prefixed.
4. Brutal or opaque starts.
5. Reusing a vanilla faction's look, emblem or text.
6. Side effects outside the faction.

## Milestones

| # | Goal |
|---|---|
| 0 | Done: the faction loads with its own panda bodies; automated in-game test |
| 1 | Prototypes: water toolkit, Ringtails, re-themed look, measured in game |
| 2 | Playable core: the full catalogue in data on re-themed and stand-in models; first hour tuned |
| 3 | Its own look: materials, building kit, plants, outfits, icons, portraits |
| 4 | Code features: Ringtails, golden afternoon, kindergarten, festival, Flowering, oxen, tutorial, settings |
| 5 | Balance on every difficulty; soak tests; compatibility; Workshop and mod.io pages |

## Quality bar for every milestone

* The automated test starts a new Inkpaws game, runs it for several days, and finds no errors in the log.
* A Folktails game with the mod enabled is unchanged.
* Works with the Reskin installed and without it, and with no other mods at all.
* Save and reload works.

## Change log

| Date | Change | Why |
|---|---|---|
| 2026-11-13 | Two factions cut to one | Depth sells a faction mod; two doubles art and upkeep |
| 2026-11-14 | Three-way workplace toggle, restricted jobs and extreme stats cut | Owner: two species must not be a steep learning curve |
| 2026-11-14 | "Day makes, night moves" split dropped | Owner caught it: workshops supply themselves all day; haulers only help |
| 2026-11-14 | Two crews sharing a workplace dropped; Ringtails get their own buildings | A workplace holds one kind of worker; the switching scheduler was the most fragile code in the plan |
| 2026-11-14 | Pipeline became an open flume | The water system already has one-way, watertight-sided cells; visible water is better than a hidden pipe |
| 2026-11-14 | Midday naps became the golden afternoon (twelve-hour day, faster work) | Workers never nap on shift; work is one block from dawn |
| 2026-11-14 | "Dusk and dawn shared hours" replaced by the day table above | Dawn can never be off duty |
| 2026-11-14 | Night hauling of building materials became night builders | Haulers never supply building sites |
| 2026-11-14 | Ringtails no longer "carry little" | Carrying halves speed whatever the load, so load size is what makes a good carrier |
| 2026-11-14 | "Raw shoots fill little" and the doubled appetite dropped | Every food fills the same; a weaker food only adds walking trips |
| 2026-11-14 | Bamboo "regrows from its roots" became quick replanting by grove keepers | Plant death is permanent without added code |
| 2026-11-14 | Crop rotation in drained paddies dropped | A tile is marked for one crop; re-marking every season is a chore |
| 2026-11-14 | Poles replace planks with no mill; mulberry cut; paper comes from bamboo | Smoother opening; fewer goods |
| 2026-11-14 | Lantern speed bonus dropped; lanterns give beauty to anyone in range | There is no night penalty to remove |
| 2026-11-14 | Charcoal water filter postponed | Lowest value for its risk |
| 2026-11-14 | The Long Nap moved to last | Entirely custom code; the core stands without it |
