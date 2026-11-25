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
| Flume | An open bamboo aqueduct one tile wide. Water runs one way, along the arrow, level or downhill. It never climbs and never spills, and the ground beside it stays moist six tiles to each side |
| Flume Corner, Drop, Bridge | Turn, step down, and cross above the ground |
| Flume Gate | The intake. Sets the flow, and **shuts itself when the water turns bad** |
| Paddy Spout | Keeps the field in front of it flooded to a shallow set depth |
| Scoop Wheel | Sits in a current and lifts a steady trickle with no workers. Still water does not turn it |
| Treadwheel Lift | Lifts water where there is no current, turned by a worker |
| Trip-Hammer Mill | A mill driven straight from a flume or stream, with no shafts |
| Dew Collector | A little drinking water with no worker, less in drought |
| Cistern and Cistern Tap | Store water; pour it into a flume to keep one strip alive in a drought |

Rules that keep it pleasant:

* **A flume never fails silently.** A dry intake, a missing corner and a starved run each say so on the piece.
* **A flume is an irrigation line.** Measured in game: a ground flume keeps a strip thirteen tiles wide moist,
  and loses almost nothing over sixty tiles. So the first payoff, in the first hour, is a bamboo grove along
  a flume, with no digging.
* **A spout makes a paddy.** The pool at the end of a flume is for rice; spouts cascade down a staircase of
  terraces, each feeding the next.
* **Wheels and mills show the current they have**, not horsepower, and say "needs a current" when becalmed.
* **Pieces are sealed.** A backed-up line never overtops its gate, corner or spout, and a raised piece stands
  on solid legs, so a flume cannot flood the field it serves.
* **Drought has its own moment.** Sources stop and scoop wheels fall still; a cistern tap keeps the best strip
  alive; when the water returns it races back down every flume.

## Pillar 2 — Every kind of land has a use

| Zone | Plants |
|---|---|
| Flooded | Rice |
| Moist | Shoot bamboo, timber bamboo, cabbage, persimmon trees |
| Dry | Tea bushes, Sichuan pepper |

* Dry-ground plants are luxuries and ingredients, never staple calories.
* Tea and pepper grow on **brown ground**: the dry land every other faction leaves empty. The rule a player
  needs is the one the map already paints: green ground for bamboo and cabbage, brown ground for tea.
  Water reaches far through soil (six tiles from a flume, sixteen from a paddy, and up a terrace step), so
  a tea garden goes out past the green, not beside the paddies. A dry-stone wall stops moisture creeping
  sideways through the soil where the player wants tea closer in; it costs logs and poles only.
* Dry-ground plants need no water at all, so they are the one harvest a drought cannot touch.
* Wet roots are a warning, not a sentence: a tea or pepper bush stops growing and says so, and dies only
  after about three wet days.
* **Tea and pepper are bushes, handled like vanilla berries**: the Forester plants them and gatherers pick
  them. They never appear in the Farmhouse's crop list, so nobody plants tea in a wet field by reflex.
* Foresters replant dead trees by default, so a grove that dies in a long drought comes back by itself.

### Bamboo, as two ordinary plants

Revision 3 put food and building material on one plant. In practice the woodcutter would cut every stalk
before it bore a shoot, and one drought would end food and construction together. So:

* **Shoot bamboo is a field crop.** The Farmhouse plants and harvests it like carrots. It is edible raw, ready
  in about three days, and is the starter crop. A vanilla player's first reflex — farmhouse and the first
  crop on the list — is exactly right.
* **Timber bamboo is a fast tree** (six days). The forester plants it and woodcutters cut it for **poles**.
* **Poles are the Inkpaws' planks.** Cut bamboo is already a pole: no mill, no power. Poles are light, so
  builders carry more per trip.
* **A Pole Mill splits logs into poles**, as a lumber mill makes planks (a worker and power). It supplies the
  first days, before any bamboo has grown, and it is the fallback when a long drought kills the groves.
  Bamboo is the better source, never the only one.
* Both shrug off a short drought and die in a long one (timber bamboo lasts ten dry days). Cabbage is a second raw staple, so the colony never
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
| Tea | Teahouse, which serves roasted tea and water from its own stock | Daily |
| A nap in the sun | Hammock (one napper), Nap Platform (several; on the ground or on a roof) | Daily |
| Play | Slide and Swing | Every few days |
| Watching the young | Kindergarten | Every few days |
| A soak | Hot Spring Bath | Every few days |
| Ink painting | Ink Studio | Weekly |

* **Decorate the workplace.** Decorations reach pandas at work. Each kind of decoration is its own small need,
  as in vanilla.
* **Cooking is the ladder.** Each dish is a recognisable Sichuan food and a step up in wellbeing.
* **Tea is drunk at the Teahouse, nowhere else.** There is one need called Tea and one place to meet it.
  Roasted tea is a dry good and stores in a warehouse; haulers or night couriers keep the Teahouse stocked.
* **Cubs are a joy.** Adults gain wellbeing from the Kindergarten.

## Pillar 4 — Two peoples, one village

### The one rule

**Inkpaws work from dawn to the bell. Ringtails work from the bell to dawn.**

One slider, one clock. Twelve and twelve is the natural balance: both peoples are at their best. Ringtails are rested by the
length of their own night shift, exactly as Inkpaws are by the length of their day.

### How it is learned

1. The game opens with Inkpaws only.
2. A **Moon Loft** — a snug home raised on stilts above a path, with a lantern in its window — is an old
   invitation. Building the first one brings a Ringtail family (two adults and a kit, at its door), one
   message that states the rule, and the night posts, unlocked free. Before that the posts sit behind a
   science cost and nothing about Ringtails is on screen.
3. Every Ringtail building sits in one toolbar group marked with a moon. Nothing needs configuring.
4. A player who never builds a Moon Loft has a complete colony. Only the Star Tower depends on Ringtails,
   and it adds science the inventors would also make, more slowly.
5. Ringtails cannot be lost for good: when a district with a Moon Loft has no living Ringtail, a new family
   answers the lantern after a few days.

### What the Ringtails are

The village's **Night Watch**, its stargazers and its artists. Not helpers.

| Building | What it does |
|---|---|
| Night Builders' Post | Sites are stocked and raised overnight. The first Ringtail workplace, because it is the one a player sees |
| Night Courier Post | Restocks every workshop and clears every flag overnight, so Inkpaws spend the day working instead of carrying. Inkpaw workplaces hold about three working days of goods to make that possible; without couriers, workers fetch their own as in vanilla |
| Night Gatherers' Post | Gathers bamboo mushrooms and wild food |
| Star Tower | Science from the night sky. It keeps its own science cost |

The **Opera Stage** (face-changing opera) is an ordinary attraction for whoever is off duty, not a Ringtail post.

### How they differ

| | Inkpaws | Ringtails |
|---|---|---|
| Hours | Dawn to the bell | The bell to dawn |
| Strength | Lift more | Run with their loads: no slowing when carrying |
| Young | Cubs, born in homes as beavers are | Kits, raised in the Moon Loft while there is work for them |

Everything else — food, wellbeing, lifespan, homes — is the same, so there is one set of numbers to learn.
Each people takes its leisure while the other works: Ringtails fill the teahouse in the morning.

### What the interface shows

* A sun or a moon on every workplace's panel (not in the toolbar: the Night Watch group's moon does that job).
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
* The player calls it from the Festival Square, at most once per cycle, or lets it call itself when stocked
  (it only calls itself in fair weather). The square's panel shows what the district has in its ordinary
  storage and exactly what is still missing; the goods are taken from storage when the festival is called.
* The festival runs from the next dawn to the dawn after. Everyone takes the day and the night off: dancing,
  rising lanterns at dusk, fireworks at a Grand Festival. Pump and lift crews stay at their posts, so a
  festival never costs the village its water. The cost is a day's work.
* In a village of several districts the festival belongs to the district of the square that called it: its
  pandas take the day off and end festive, its squares light. There is still one festival a cycle and one
  Tradition for the whole village, and the turn passes to another district's square next time.
* At dusk the sky fills with rising paper lanterns for the whole evening, with one dense release; fireworks
  beside them are for a Grand Festival.
* Rewards: everyone ends festive for about twenty days (a Grand Festival a little more), and one step of
  **Tradition**, which unlocks decorations at no science cost.

### The Great Flowering

* Never before cycle 6, always on the first day of a cycle (so never in a drought or badtide), and announced
  a full cycle ahead: a notice, a line in the top bar with advice, and buds on the plants. Forecasts name
  the cycle, not a number of days.
* One of the two bamboos flowers across the map. Every grown plant becomes a flowering plant whose harvest is
  **bamboo seed**, gathered by the same farmers or woodcutters over three days before it dies. Young plants
  die at once, and that bamboo rests for nine days before it grows again; planting marks stay, so fields
  replant themselves. Wild bamboo left standing reseeds its own tile when it dies; wild bamboo cut for its
  seed is gone, like any wild tree that is cut. Shoot bamboo means a food gap of about twelve days to bridge; timber bamboo means
  building material to have stocked (the Pole Mill covers it).
* Bamboo seed is a large one-time harvest and makes a food of its own (seed cakes: steamed, or better from a Kitchen). It is a windfall to prepare
  for, not only a loss.
* A setting offers off, rare or normal.

## Pillar 6 — Late game

* **Wooden Oxen** are the faction's bots: tireless and strong. An ox lifts 30 (an Inkpaw lifts 18) and
  lasts ninety days.
* **Kite windmills** and **bamboo water wheels** replace fuel engines.
* **Bamboo scaffolding and rope bridges** are the Inkpaws' platforms and suspension bridges, at vanilla cost.
* **The Great Sitting Panda**, a freestanding cliff carving with water at its feet and both peoples on it, is
  the top monument.
* **The wonder** is a colossal sky lantern that carries seeds over the wasteland. It is launched with the
  village's own paper lanterns, and the awe it leaves lasts as long as any vanilla wonder's.
* **Paper lanterns always have a use**: lantern decorations are built from them, the festival burns them, and
  the wonder needs hundreds.

## The first two hours (Normal difficulty)

| When | What the player does | The new idea |
|---|---|---|
| First minutes | Woodcutter, water pump, forager, Farmhouse with shoot bamboo; then a cistern before the first drought | None: the vanilla reflexes work |
| Day 1–2 | Pole Mill on a power wheel; forester with timber bamboo; dens from logs | None yet: the mill is a lumber mill |
| Days 3–5 | First shoots. Steamer cooks shoots. A Hammock for the afternoon nap | Dishes; afternoon rituals |
| Around day 5 | The game suggests a shorter day | The afternoon bell |
| Days 6–10 | The first bamboo is cut: poles with no mill. A scoop wheel (logs and poles, no gears) and a short flume water a second grove | Bamboo poles; leading water |
| First drought | Bamboo browns and survives; cisterns carry the village | Droughts are survivable |
| End of cycle 1 | First Moon Loft: the Ringtails arrive, and building continues overnight | The one rule |
| Cycle 2 | Paddy spout and rice; pickles; tea bushes on brown ground and the first Teahouse; lanterns; the Small Festival | Flooded fields; tea; the festival |
| Cycle 3 | Sichuan pepper; trip-hammer mill; sweet rice balls | Water as power |
| Later | Hot pot, Star Tower, Opera, Flowering forecast, Oxen, the cliff carving, the sky lantern | The long game |

Seven new ideas in two hours, never two at once.

## Art direction

* **Buildings:** dark timber frames with white lime-plaster infill, grey clay roof tiles, fresh and cured
  bamboo, woven bamboo panels, rammed earth and river stone.
* **Red is an accent:** lanterns, small trim, festival goods.
* **Lattice windows** that glow at night, and lanterns lit at dusk.
* **Outfits:** conical hats on farmers (field and paddy share one outfit); cloth head-wraps; back-baskets for couriers.
* **Characters:** the Reskin's proportions and coats for Inkpaws. Ringtails start as a smaller red-coated body
  and get a true red panda body when the character pipeline allows.
* **Sound:** panda bleats and a red panda's twitter (built; off until the owner has listened), a bamboo "tok" as a flume fills, different bells for the two
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

* **Nothing in the toolbar lies.** A building appears only when it does what its text says. A building that
  waits for a code module is left out of the faction's lists until that module and its data ship, and comes
  back by itself when they do. The same goes for a need nothing can satisfy and a good nothing uses.

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
| 2026-11-14 | The day's length is fixed at dawn: moving the bell shows "Rested +33%; tomorrow +0%" and takes effect next morning | Otherwise a player could work a long day and slide the bell back at dusk to keep the bonus |
| 2026-11-14 | Inkpaws' top walking speed is raised (the game stops everyone at twice normal) | In game, the rested bonus stopped helping walkers above wellbeing 52; with the limit raised a twelve-hour day matches a sixteen-hour one at every wellbeing level |
| 2026-11-14 | In an Inkpaws game the interface says "Inkpaw", "cub" and "panda" where vanilla says "beaver" and "kit", by code that only acts while an Inkpaws game is loaded | A panda faction whose every tooltip says "beavers" feels like a reskin; a text override file would have renamed beavers in Folktails games too |
| 2026-11-14 | A flume waters the ground beside it; "flume, spout, pool" is no longer the taught unit | The water prototype measured six moist tiles to each side of a one-wide flume. The pool is for rice only |
| 2026-11-14 | Tea and pepper survive about three wet days; they belong on brown ground, out past the irrigated land (first written as "the top bench of a terrace"; a later run showed tea dying one level up and four to eight tiles from a paddy) | In the prototype a dry-ground crop died within a day anywhere near water, and moisture reaches sixteen tiles from a paddy |
| 2026-11-14 | Inkpaw foresters replant dead trees by default | The vanilla default leaves a dead grove dead, which would end pole supply after one long drought |
| 2026-11-14 | Night couriers restock workshops for the coming day; Inkpaw workplaces hold about a day's inputs and outputs | In the prototype the couriers made no hauls at all: builders, not haulers, supply sites, and nothing was left to carry at night. A day-sized shelf gives the night real work and takes carrying off the day crew, and changes nothing for a village without Ringtails |
| 2026-11-14 | Ringtails walk at Inkpaw speed and keep it when loaded, by data alone | The game has a separate "carrying" speed per character; setting it equal to the walking speed is the whole feature |
| 2026-11-14 | Tea quenches a fifth of a thirst per cup; dew collectors crowd each other out | The model: at a third, tea becomes mandatory; any useful dew yield repays a pump worker within three weeks unless collectors share a catchment |
| 2026-11-14 | Buildings that wait for code are hidden until the code's data ships; a release build fails if one is visible without it | The independent review found twenty-three buildings whose text promised one thing while a vanilla stand-in did another (a flume that was a banner pole, a scoop wheel that asked for power) |
| 2026-11-14 | A Pole Mill splits logs into poles; timber bamboo lasts ten dry days instead of seven | The review: bamboo was the only source of poles, the first poles came on day seven, and one long drought ended poles, gears, paper and building together |
| 2026-11-14 | Tea and pepper are planted by the Forester and picked by gatherers, like berries | They were offered in the farm's crop list, died in the wet field within days, and were harvested by a different building than the one that planted them |
| 2026-11-14 | One Tea need, met at the Teahouse, which uses up roasted tea and water. Tea is no longer drunk from storage, and is a dry good | Two rows named "Tea" and "Teahouse", and a teahouse with no tea in it. Pandas gathered over tea is also the picture the faction wants |
| 2026-11-14 | The Nap Platform stands on the ground or on a roof and takes several nappers | It could only be placed on a roof, and a daily nap for fifty colonists meant a wall of single hammocks |
| 2026-11-14 | The Hot Spring Bath uses water, not dirt; the Dry-Stone Wall blocks moisture sideways and costs logs and poles | Both were copies of vanilla buildings that need a late-game dirt excavator, and the wall's copied setting did not stop moisture at all |
| 2026-11-14 | The wonder is launched with paper lanterns and its awe lasts as a vanilla wonder's does; lantern decorations cost paper lanterns | Its reward faded in three days, and paper lanterns had no use anywhere |
| 2026-11-14 | Scoop Wheel costs logs and poles, no gears | The "days 5-8" flume beat was not reachable before day thirteen |
| 2026-11-14 | Wellbeing total at least matches the Folktails': the Nap Platform keeps the rooftop effect, and the goldfish bowl, moon gate and string lanterns are each their own small need | Reachable wellbeing was about nine below the Folktails', with rows that could never fill |
| 2026-11-14 | Wooden Ox lifts 30 and lasts ninety days; the faction uses its own tail and banner decals | "Strong" oxen lifted about what a panda does, and beaver tails showed on panda banners |
| 2026-11-14 | Inkpaw workplaces hold three working days of inputs and outputs (was "about a day"), set by one number | Measured: day-sized shelves gave the couriers 24 goods to move in two nights; three-day shelves gave 107 and 46% more produced, and without Ringtails they changed nothing for the worse. To be re-checked for workshops hoarding scarce logs and poles early |
| 2026-11-14 | The first Moon Loft brings two adults and a kit to its door and unlocks the night posts free; a loft says in its panel why it is or is not raising a kit | The Ringtail module passed a five-day soak with a reload. If the module is switched off or a game update breaks it, the same colonists load as Inkpaws and the posts become ordinary workplaces |
| 2026-11-14 | Festival goods stay in ordinary storage and are taken at the call; the festival starts at the next dawn; pump and lift crews keep working; everyone ends festive | The events prototype: colonists eat from any storage a building holds, a festival must never strand the water supply, and a reward only for those who reached the square punishes big villages |
| 2026-11-14 | The Flowering's seed is the dying plant's own harvest, and the bamboo rests nine days (was "until the next temperate season") | Dropped goods rot and are slow to collect; the colony model had 19 to 40 of 60 starving after a fifteen-day gap and none after twelve |
| 2026-11-14 | A Flume Bridge Span lets one flume line cross over another; a stopped wheel or a dry gate says that a Cistern Tap can pour stored water into the line; a flume is heard only where water runs | The water module's runs: without a span no two lines could ever cross; in the first drought the wheel stops and explains why, a backed-up line holds about nineteen cubic metres by itself, but nothing told the player the tap exists |
| 2026-11-14 | With the water module switched off the flume pieces are solid blocks and nothing floods; gate settings and water in the flumes survive save and reload | Proven on a save made with the module on and loaded with it off |
| 2026-11-25 | Ringtails get the rested bonus from the length of their own night shift | The balance model on the built data: without it a Ringtail builder did 0.75 of an Inkpaw's work at twelve and twelve, where the design promises parity |
| 2026-11-25 | The rested bonus tapers hour by hour from twelve to sixteen hours, so output is the same at any day length in that range | The model found a 2% bulge at thirteen to fifteen hours; a flat line makes the choice about free time and the night shift, not arithmetic |
| 2026-11-25 | Water pumps and taps keep vanilla-sized shelves (workshops with ingredients keep three days) | The shelf rule had turned the first water pump into a 146-water tank: a careless Inkpaws colony lost nobody in the first drought where the same script lost ten of thirty-nine Folktails |
| 2026-11-25 | Flumes cost no science, the gate 40 and the scoop wheel 60; tea and the Teahouse move to the second cycle in the first-hours plan | With two inventors the water beat landed on day fifteen instead of days five to eight, and no tea can exist before day twelve |
| 2026-11-25 | Wellbeing trimmed (play, ink painting, watching the young, tea one point each; Memorial Arch 6, Great Sitting Panda 14; rice balls above steamed rice), the Wooden Ox costs more, pickles match bread | The model: a ceiling of 94 against the Folktails' 84 and a mid-game lead of 7 to 14; an ox that out-hauled a fully boosted bot with no upkeep |
| 2026-11-25 | The Star Tower ships as a Ringtail night post that makes science; the Opera Stage ships as an ordinary attraction with no claim about who runs it | Both were hidden behind venue code nobody had planned, which left the last 38,000 science to inventors alone |
| 2026-11-25 | The tutorial teaches the woodcutter first, then water and food, poles, dens, a cistern, the inventor, the Steamer, the bell, flumes, and tea last | Second audit: a colony starts with no logs, so a newcomer who followed the old order placed a pump that was never built; the Steamer step showed a locked button; nothing taught storing water; tea stood in front of flumes |
| 2026-11-25 | The Star Tower keeps its own science cost (the Moon Loft does not unlock it) and is the one thing that depends on Ringtails; inventors alone still research everything | Unlocked free by a 200-science loft, four Ringtails would out-research every inventor from the second cycle |
| 2026-11-25 | When a district with a Moon Loft has no living Ringtail, a new family answers the lantern after a few days | Second audit: the family arrived once per save, so Ringtails could die out for good |
| 2026-11-25 | Timber bamboo grows in six days, not five | Poles from bamboo cost a third of poles from birch and a mill per tile and day; nearer half is the intent: the better source, never a free one. Seven days was ruled first and withdrawn: the first bamboo poles would land after day ten, outside the first-hours plan |
| 2026-11-25 | Bamboo seed can be steamed into seed cakes with no mill (two per seed); the Kitchen recipe with rice flour stays the better one | Without a Kitchen and a Trip-Hammer Mill the Great Flowering's seed had no use, so the event only took |
| 2026-11-25 | The design is brought to what the build does: "Farmhouse" (the vanilla name, already translated), farmers of both kinds wear the conical hat, the dew has no dawn, the ox is not slow, scaffolding and rope bridges cost as vanilla, no sun or moon in the toolbar, no lantern wave at the bell | The docs review of 2026-11-25 listed nine places where this document promised what no lane had built; none is worth new code before release |
| 2026-11-25 | Second wellbeing trim: Opera 3, Soak 2, Moon Gate 1, Great Sitting Panda 12, Sky Lantern 8 | The model after the first trim: the Opera Stage put back more than the trims took, leaving a ceiling of 95 against the Folktails' 84; the target is within about three points |
| 2026-11-25 | A festival belongs to the district of its square (one festival a cycle and one Tradition for the whole village); the lantern sky lasts the whole evening and comets are kept for a Grand Festival | The events review: a village-wide day off from one square made no sense across districts, and the first lantern show was two points of light |
| 2026-11-25 | Wild bamboo left standing through a Great Flowering reseeds its own tile; cut for seed, it is gone | The events review: only marked tiles were replanted, so every wild grove flowered once and vanished from the map |
| 2026-11-25 | A Dew Collector is tuned so four keep a landlocked outpost of about six in water outside droughts; pine resin stays (Inkpaws have no tapper and no building costs it, and removing the good would break other mods' buildings in an Inkpaws game); the Potted Pine is priced in poles; the Goldfish Bowl and Moon Gate are priced like other decorations of their worth | Second audit: a collector made 2 water a day against a pump worker's 48; a gathered good with no recipe; +2 wellbeing for twelve logs |
