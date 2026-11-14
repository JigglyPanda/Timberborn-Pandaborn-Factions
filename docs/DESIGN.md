# Pandaborn - Factions: design

Revision 4, 2026-11-14. Revision 3 was reviewed by four independent critics (in `docs/reviews/`) against
`docs/tech/game-mechanics.md`. This revision resolves what they found. The catalogue is `docs/CONTENT.md`;
engineering rules are `docs/ENGINEERING.md`.

The owner has given the orchestrator executive authority over design, with one yardstick: **player
satisfaction**. Every change and its reason is logged at the end.

## The test for every idea

1. Would a player enjoy it, and notice it within a minute?
2. Does it work the way the game actually runs, hour by hour?
3. Can a new player ignore it and still be fine?
4. Will it survive a game update, and fail safely if it does not?

## Fixed by the owner

* One faction, the **Inkpaws** (giant pandas), with **Ringtails** (red pandas) living among them.
* Core identity: **lead the water** rather than hold it back.
* The two peoples keep different hours. The system must be smooth to learn; if it is not, fall back to one
  people with coat variety.
* Signature events are in scope.
* Art volume about what Emberpelts ships, all generated in code / by AI and disclosed.
* Unlocked from the start. Tone cozy and whimsical. Steam Workshop and mod.io, Windows and Mac.

## Pitch

The cozy panda faction: you run bamboo aqueducts down to rice terraces, and when the afternoon bell rings the
big pandas put down their tools and the red pandas take over the village for the night.

## Setting

The bamboo-grove farmsteads of Sichuan, where giant and red pandas really live. One real place, used closely.

| Real thing | In the mod |
|---|---|
| Dujiangyan, a 2,200-year-old system that waters a plain with no dam | Flumes, spouts and scoop wheels |
| The water-powered trip-hammer | A mill driven straight from a flume |
| Rice terraces, hill tea, Sichuan pepper, pickles, hot pot, bamboo mushrooms | Farming and food |
| Bamboo mass flowering, which really starves pandas | The Great Flowering |
| The night watchman's clapper | The Ringtails as the village's Night Watch |
| Face-changing opera | The Opera Stage |
| The Wooden Ox of legend; the sky lantern | Late-game haulers; the wonder and the festival |
| Panda nurseries | The Kindergarten |

Cultural rules: no writing on any texture; nothing Japanese-coded; no imperial red-and-gold; no religious
imagery; both peoples share one architecture, differing only in scale. Details are in the art direction
section.

## What the game allows (the facts this design stands on)

| Fact | Consequence |
|---|---|
| Work is one colony-wide block from dawn; default 16 of 24 hours; the first day has only 12 | Leisure is the afternoon and evening. Shortening the day must never be the default at minute one |
| Workers on shift ignore every need that is not critical | Leisure only happens off duty |
| A leisure visit lasts under two hours and holds for about a week; colonists sleep about three hours | Off-duty time is mostly empty unless there are daily rituals |
| Working speed does not speed walking, and building, hauling and foraging are mostly walking | A shorter day needs a walking bonus too, or those jobs lose a quarter of their output |
| Workshop workers supply themselves; haulers only help, with double loads | A colony never needs haulers to function |
| Haulers never supply building sites; builders do | Night builders, not night couriers, are what a player feels |
| Carrying halves walking speed whatever the load | A colonist who keeps full speed while loaded is a natural courier |
| Every food fills the same hunger; a dish's bonus needs a bite every few days | The staple can be anything; variety is cheap in volume |
| Plants grow on fixed timers; dryness starts a dying countdown that resets when water returns; death is permanent | Drought tolerance is one number per plant. Dead plants must be cleared |
| Any soil contamination kills plants within hours | Flumes must never carry badwater |
| Power wheels only turn while staffed | Staffed power belongs to the people who use it |
| Night changes nothing in play | Night work is rhythm, mood, and work that continues while others rest |
| A workplace holds one kind of worker; homes cannot be restricted by kind | Each people has its own workplaces; any home takes anyone |
| Unknown data in goods, needs, recipes or the faction file crashes every game, not just ours | Global data stays plain and validated; our own code only ever adds |

## Pillar 1 — Lead the water

Inkpaws keep levees, dams and floodgates under their vanilla names, so every map plays from day one. What they
add is a toolkit for shallow water at many heights.

| Tool | What it does |
|---|---|
| Flume | An open bamboo aqueduct one tile wide. Water runs one way, along the arrow, level or downhill. It never climbs and never leaks |
| Flume Corner, Drop, Bridge | Turn, step down, and cross above the ground |
| Flume Gate | The intake. Sets the flow, and **shuts itself when the water turns bad** |
| Paddy Spout | Keeps the field in front of it flooded to a shallow set depth |
| Scoop Wheel | Sits in a current and lifts water with no workers |
| Treadwheel Lift | Lifts water where there is no current, turned by a worker |
| Trip-Hammer Mill | A mill driven straight from a flume or stream, with no shafts |
| Dew Collector | A little drinking water each dawn, less in drought |
| Cistern and Cistern Tap | Store water; pour it into a flume to keep one strip alive in a drought |

Rules that keep it pleasant:

* **A flume never fails silently.** A dry intake, a missing corner and a starved run each say so on the piece.
* **The taught unit is flume, spout, pool.** A flume carries; the pool at its end is what waters a field.
* **Bamboo along a flume is the first payoff**, reachable in the first hour: the strip beside a ground flume
  is moist.
* **Drought has its own moment.** Sources stop and scoop wheels fall still; a cistern tap keeps the best strip
  alive; when the water returns it races back down every flume.

## Pillar 2 — Every kind of land has a use

| Zone | Plants |
|---|---|
| Flooded | Rice |
| Moist | Shoot bamboo, timber bamboo, cabbage, persimmon trees |
| Dry | Tea bushes, Sichuan pepper |

* Dry-ground plants are luxuries and ingredients, never staple calories.
* Tea and pepper die if their roots get wet, and say so. A dry-stone wall keeps moisture out of a tea slope.

### Bamboo, as two ordinary plants

Revision 3 put food and building material on one plant. In practice the woodcutter would cut every stalk
before it bore a shoot, and one drought would end food and construction together. So:

* **Shoot bamboo is a field crop.** The Farmstead plants and harvests it like carrots. It is edible raw, ready
  in about three days, and is the starter crop. A vanilla player's first reflex — farmhouse and the first
  crop on the list — is exactly right.
* **Timber bamboo is a fast tree.** The forester plants it and woodcutters cut it for **poles**.
* **Poles are the Inkpaws' planks: no mill, no power.** Poles are light, so builders carry more per trip.
* Both shrug off a short drought and die in a long one. Cabbage is a second raw staple, so the colony never
  rests on one plant.
* Bamboo mushrooms grow in standing timber groves and are foraged.

## Pillar 3 — The afternoon bell

* **One bell divides the day.** It is the vanilla working-hours slider. A new game starts where vanilla does.
* **Rested pandas are quick pandas.** The shorter the working day, the faster Inkpaws work *and walk*: at
  twelve hours they get as much done as beavers do in sixteen. The bonus is shown on the slider. Long days are
  allowed and simply remove it. There is no punishment and no hidden need.
* **The game suggests it once the village is settled**: "Inkpaws work a short day and work it well."
* **Afternoons have rituals**, so off-duty pandas are doing something:

| Ritual | Building | How often |
|---|---|---|
| Tea | Teahouse | Daily |
| A nap in the sun | Hammock, Nap Platform | Daily |
| Play | Slide and Swing | Every few days |
| Watching the cubs | Panda Kindergarten | Every few days |
| A soak | Hot Spring Bath | Every few days |
| Ink painting | Ink Studio | Weekly |

* **Decorate the workplace.** Decorations reach pandas at work. Each kind of decoration is its own small need,
  as in vanilla.
* **Cooking is the ladder.** Each dish is a recognisable Sichuan food and a step up in wellbeing. Tea also
  quenches thirst, three cups from one measure of water.
* **Cubs are a joy.** Adults gain wellbeing from the Kindergarten.

## Pillar 4 — Two peoples, one village

### The one rule

**Inkpaws work from dawn to the bell. Ringtails work from the bell to dawn.**

One slider, one clock. Twelve and twelve is the natural balance: both peoples are at their best.

### How it is learned

1. The game opens with Inkpaws only.
2. A **Moon Loft** — a snug home raised on stilts above a path, with a lantern in its window — is an old
   invitation. Building the first one brings a Ringtail family and unlocks their first workplace.
3. Every Ringtail building sits in one toolbar group marked with a moon. Nothing needs configuring.
4. A player who never builds a Moon Loft has a complete colony. Nothing else depends on Ringtails.

### What the Ringtails are

The village's **Night Watch**, its stargazers and its artists. Not helpers.

| Building | What it does |
|---|---|
| Night Builders' Post | Sites are stocked and raised overnight. The first Ringtail workplace, because it is the one a player sees |
| Night Courier Post | Hauling through the evening and night |
| Night Forager's Post | Gathers bamboo mushrooms and wild food |
| Star Tower | Science from the night sky |
| Opera Stage | Face-changing opera for whoever is off duty |

### How they differ

| | Inkpaws | Ringtails |
|---|---|---|
| Hours | Dawn to the bell | The bell to dawn |
| Strength | Lift more | Run with their loads: no slowing when carrying |
| Young | Cubs, born in homes as beavers are | Kits, raised in the Moon Loft while there is work for them |

Everything else — food, wellbeing, lifespan, homes — is the same, so there is one set of numbers to learn.
Each people takes its leisure while the other works: Ringtails fill the teahouse in the morning.

### What the interface shows

* A sun or a moon on every workplace, in the toolbar and on the panel.
* A moon arc on the working-hours clock.
* The population panel in two rows: Inkpaws and Ringtails, each with idle workers.
* "Closed for the day. Ringtails start at the afternoon bell" in place of the vanilla no-workers alert.

### The gate

A prototype must show Ringtails holding their jobs, keeping these hours, sleeping, surviving save and reload,
and leaving other factions untouched, and then pass a multi-day soak. If it fails or proves fragile, the
faction ships with one people and Ringtail coats as variety. If a game update ever breaks the Ringtail code,
existing Ringtails load as Inkpaws rather than vanishing.

**Passed, 2026-11-14** (`docs/tech/two-peoples.md` section 17): three days and a reload with no Ringtail in an
Inkpaw job or the reverse, no critical need, every colonist back from the save with its kind, job and home, no
Harmony, and a Folktails game unchanged. The faction ships with two peoples. What the prototype settled:

* **Hours.** A Ringtail coming off the night sleeps about three hours after dawn, then has the rest of the
  morning for food and leisure until its shift starts. The start of that shift is the bell (the working-hours
  slider), never earlier than four hours after dawn so there is time to sleep, and never later than nightfall,
  so Ringtails always hold the night even if the Inkpaws are worked around the clock.
* **Homes.** Moon Lofts belong to Ringtails: an Inkpaw who lands in one is swapped out within the hour. A
  Ringtail without a loft may sleep in any home.
* **Appetite.** The prototype also proved a lighter Ringtail appetite. It is not used: one set of food numbers
  is easier to learn, the balance was set with equal appetites, and the trick leans on an unwritten detail of
  how the game applies need effects.
* **Numbers.** The vanilla population panel does not count Ringtail crews, so the two-row panel is required,
  not optional.

## Pillar 5 — A third rhythm

### Lantern Festival

* **Small Festival**, reachable in the second cycle: paper lanterns and any three cooked dishes.
* **Grand Festival**: adds fireworks. Two tiers only; bamboo-seed cakes simply count as a dish.
* The player calls it from the Festival Square, at most once per cycle, or lets it call itself when stocked.
* Everyone takes a day and a night off: dancing, rising lanterns, fireworks. The cost is a day's work.
* Rewards: festive spirit that lasts most of a cycle, and one step of **Tradition**, which unlocks decorations.

### The Great Flowering

* Never before a set cycle, never in a drought or badtide, and announced a full cycle ahead with visible buds.
* One of the two bamboos flowers, drops its seed and dies across the map. Shoot bamboo means a food season to
  bridge; timber bamboo means building material to have stocked.
* The fallen **bamboo seed** is a large one-time harvest and makes the best food in the mod. It is a windfall
  to prepare for, not only a loss.
* A setting offers off, rare or normal.

## Pillar 6 — Late game

* **Wooden Oxen** are the faction's bots: tireless, strong and slow.
* **Kite windmills** and **bamboo water wheels** replace fuel engines.
* **Bamboo scaffolding and rope bridges** make tall building cheap and light.
* **The Great Sitting Panda**, a freestanding cliff carving with water at its feet and both peoples on it, is
  the top monument.
* **The wonder** is a colossal sky lantern that carries seeds over the wasteland.

## The first two hours (Normal difficulty)

| When | What the player does | The new idea |
|---|---|---|
| First minutes | Water pump, forager, woodcutter, Farmstead with shoot bamboo | None: the vanilla reflexes work |
| Day 1–2 | Forester with timber bamboo; dens from logs | Poles come from bamboo and need no mill |
| Days 3–5 | First shoots and poles. Steamer cooks shoots. Hammock and Teahouse | Dishes; afternoon rituals |
| Around day 5 | The game suggests a shorter day | The afternoon bell |
| Days 5–8 | A scoop wheel and a short flume water a second grove | Leading water |
| First drought | Bamboo browns and survives; cisterns carry the village | Droughts are survivable |
| End of cycle 1 | First Moon Loft: the Ringtails arrive, and building continues overnight | The one rule |
| Cycle 2 | Paddy spout and rice; pickles; lanterns; the Small Festival | Flooded fields; the festival |
| Cycle 3 | Tea on dry ground; trip-hammer mill; sweet rice balls | Dry land; water as power |
| Later | Hot pot, Star Tower, Opera, Flowering forecast, Oxen, the cliff carving, the sky lantern | The long game |

Seven new ideas in two hours, never two at once.

## Art direction

* **Buildings:** dark timber frames with white lime-plaster infill, grey clay roof tiles, fresh and cured
  bamboo, woven bamboo panels, rammed earth and river stone.
* **Red is an accent:** lanterns, small trim, festival goods.
* **Lattice windows** that glow at night. Lanterns light in a wave at the bell.
* **Outfits:** conical hats on paddy farmers only; cloth head-wraps; back-baskets for couriers.
* **Characters:** the Reskin's proportions and coats for Inkpaws. Ringtails start as a smaller red-coated body
  and get a true red panda body when the character pipeline allows.
* **Sound:** panda bleats, a red panda's twitter, a bamboo "tok" as a flume fills, different bells for the two
  shifts, the watchman's clapper.
* **Names:** colonists get real doubled names with their meaning shown, such as "Le Le (Joy)"; Ringtails get
  star, fruit and spice names.

## What sinks faction mods (design against these)

1. Breaking on game updates.
2. Dependency chains: none required.
3. Id clashes: everything prefixed.
4. Brutal or opaque starts.
5. Reusing a vanilla faction's look, emblem or text.
6. Side effects outside the faction.

## Build order

Every step ends in a mod that could be released.

| Step | Contents |
|---|---|
| A. Foundation | Frozen ids; catalogue and generator; validator against the game's own definitions; code skeleton with safe feature loading; in-game checks of the mechanisms everything rests on |
| B. Playable core | The whole catalogue in data on re-themed and stand-in models; water tools; the afternoon bell; first two hours tuned with the colony model |
| C. Its own look | Materials, the building kit, identity models, plants, icons, portraits, outfits |
| D. Ringtails | If the gate passes: Moon Loft, the night posts, Star Tower, panels |
| E. Events and depth | Festival, Kindergarten extras, Flowering, Oxen, monuments, wonder, tutorial |
| F. Release | Balance on every difficulty, soak tests, compatibility, Mac, store pages |

## Quality bar for every step

* The automated test starts a new Inkpaws game on each difficulty, runs it for days, and finds no errors.
* Folktails and Iron Teeth games with the mod enabled are unchanged.
* Works with the Reskin installed and without it, and with no other mods at all.
* Save and reload works, and saves from the previous build still load.
* With any optional feature switched off, the game still loads and plays.

## Change log

| Date | Change | Why |
|---|---|---|
| 2026-11-13 | Two factions cut to one | Depth sells a faction mod; two doubles art and upkeep |
| 2026-11-14 | Three-way workplace toggle, restricted jobs and extreme stats cut | Owner: two species must not be a steep learning curve |
| 2026-11-14 | "Day makes, night moves" split dropped | Owner caught it: workshops supply themselves all day |
| 2026-11-14 | Two crews sharing a workplace dropped; Ringtails get their own buildings | A workplace holds one kind of worker |
| 2026-11-14 | Pipeline became an open flume | The water system already has one-way, watertight-sided cells |
| 2026-11-14 | Bamboo split into a crop and a tree | On one plant the woodcutter destroys the food, and one drought ends food and building together |
| 2026-11-14 | Bamboo survives short droughts instead of dying first | The first drought was the likeliest place for a new player to quit; Hard was unplayable |
| 2026-11-14 | Twelve-hour default day and the Rest need replaced by a rested bonus shown on the slider | A twelve-hour first day leaves pandas thirsty and idle at noon; a Rest need cannot be tuned and means walls of hammocks |
| 2026-11-14 | The bonus covers walking as well as working | Building, hauling and foraging are mostly walking |
| 2026-11-14 | Daily rituals added to the afternoon | One leisure visit lasts a week, so off-duty pandas only wandered |
| 2026-11-14 | Ringtail hours became "from the bell to dawn" | The earlier overlapping schedule was eleven things to learn, and made Ringtails work half as long again as Inkpaws |
| 2026-11-14 | Night builders are the first Ringtail job; treadwheel power is not a Ringtail job | Haulers never supply sites; power wheels turn only while staffed, at the wrong hours |
| 2026-11-14 | Ringtails keep full speed when loaded instead of walking fast and lifting little | Load size and carrying speed are what make a courier |
| 2026-11-14 | Ringtails reframed as Night Watch, stargazers and artists; same lifespan and homes; back-baskets | As written they read as a servant caste |
| 2026-11-14 | Kits are raised in the Moon Loft while there is work for them | Homes cannot be restricted by kind; unseen idle Ringtails would pile up |
| 2026-11-14 | Nothing a one-people colony needs is a Ringtail job | Lanterns, explosives and water lifting had drifted behind the Ringtail gate |
| 2026-11-14 | Flume gate shuts itself on badwater; flumes report why they are dry | A flume would have poisoned every terrace in the first badtide; four failures were silent |
| 2026-11-14 | Trip-hammer mill and cistern tap added | Leading water should power things, and should still matter in a drought |
| 2026-11-14 | Festival tiered and moved to the second cycle; it costs a day's work | It was gated behind the deepest chains and changed nothing for Inkpaws |
| 2026-11-14 | Flowering announced a cycle ahead, never in bad weather | Three days cannot answer "grow something else" |
| 2026-11-14 | The Long Nap cut | All custom code, and the worst framing in the design |
| 2026-11-14 | A third of the identity catalogue cut: lacquer chain, tofu and soy, ox upkeep, lotus, persimmon cakes, two monuments | So the rest can be made well |
| 2026-11-14 | Vanilla functions keep vanilla names; noria became Scoop Wheel | A player should never relearn a levee |
| 2026-11-14 | Poles are the vanilla plank under a new name, if the game allows a faction-only rename | Hundreds fewer cost edits, and other mods' buildings keep working |
| 2026-11-14 | Art direction moved from lacquer red to Sichuan timber, plaster and grey tile; no writing on textures | Red and gold reads as Chinatown; generated characters are gibberish |
| 2026-11-14 | Charcoal filter, crop rotation, raw-shoot penalty, lantern speed bonus dropped | Low value, a chore, extra walking, and nothing to remove |
| 2026-11-14 | The rested bonus multiplies speed instead of adding to it | The colony model: game bonuses add together, so a flat bonus loses 8–17% against a long day once wellbeing is high |
| 2026-11-14 | Inkpaws lift 18, Ringtails 14; Ringtails keep full speed when loaded | The model: this makes a night builder exactly as good as a day builder at twelve and twelve; equal lift would make Ringtails half as good again |
| 2026-11-14 | Births, lifespan and childhood stay as vanilla | The model: slow breeding took 46 days to reach fifty colonists against 24, which is an hour of watching thirteen pandas |
| 2026-11-14 | "Fast building in the first hour" withdrawn as a claim | The model: the first week is limited by logs, not builders. The smoother start is food: shoots on day 4.5 against carrots on day 5.9 |
| 2026-11-14 | Dry-day tolerance set: shoot bamboo 5, cabbage 7, timber bamboo 7 | The model: shoots survive every first drought on Normal; on Hard cabbage is the staple |
| 2026-11-14 | Rule: if a mechanic cannot be explained in one sentence, simplify the mechanic. Festival cut to two tiers; the rested bonus is stated as one rule and its walking-speed limit is handled in code, not explained to the player | The writer could not fit the rested bonus, the festival tiers, kit-raising or the Flowering into a tooltip |
| 2026-11-14 | Needs renamed "Watching the young", "Ink painting", "Opera"; "Kindergarten" without "Panda"; "Night Gatherers' Post"; the farmhouse keeps its vanilla name | The writer's review: one word per job, and both peoples share the kindergarten |
| 2026-11-14 | The Ringtail gate passed: two peoples ship. Ringtail shift starts at the bell, clamped between four hours after dawn and nightfall; lofts are Ringtail homes by a swap rule; the lighter Ringtail appetite the prototype tried is left out | The prototype ran three days and a reload with no failures. The game's own sleep logic gives a three-hour sleep and a free morning, which is the teahouse beat the design wanted |
| 2026-11-14 | The faction's look is a re-theme of the vanilla materials done in code, plus its own models for identity buildings | A data-only re-theme crashed with two popular mods; the code form passed with thirty-five mods and falls back to the Folktails look if anything is missing |
| 2026-11-14 | Tea quenches a fifth of a thirst per cup; dew collectors crowd each other out | The model: at a third, tea becomes mandatory; any useful dew yield repays a pump worker within three weeks unless collectors share a catchment |
