# The Inkpaws: a player's guide

For after the first hour. It assumes you know Timberborn: levees, districts, well-being, droughts.

**How this page is kept true.** The prose states rules. Every cost, rate and count sits in a table that
`tools/docs/guide_tables.py` writes from the mod's own data (`catalogue/`), so the numbers are the build's. A
building whose part of the mod is switched off is left out of the tables, as it is left out of the toolbar. Distances and
flows quoted in the prose were measured in runs of the game (`docs/tech/`). Balance is still being tuned: trust the
game's own panels over any number here.

**Which parts depend on a switch.** Each part of the mod that has code can be off, in a build or after a game
update. A section that needs one is marked like this: **[Water]**. In an Inkpaws game, open the notification log:
one entry starts "Pandaborn - Factions:" and lists every part of the mod and whether it is on.

<!-- gen:switches -->
| Mark | Part of the mod | In the catalogue as this page was generated |
|---|---|---|
| **[Bell]** | The afternoon bell and the rested bonus | on |
| **[Ringtails]** | The Moon Loft, the Ringtails and the night posts | on |
| **[Water]** | Flumes, spouts, the scoop wheel, the cistern tap, dew, the trip-hammer mill | on |
| **[Festival]** | The Lantern Festival and Tradition | on |
| **[Flowering]** | The Great Flowering | on |
<!-- /gen:switches -->

Water, Festival and Flowering are switched on in the catalogue and proven on test copies of the build. They had
not yet passed the install gate when this page was written (2026-11-25), so the last installed build was without
them. See [RELEASE.md](RELEASE.md).

## Contents

1. [What is different from beavers](#1-what-is-different-from-beavers)
2. [The afternoon bell](#2-the-afternoon-bell)
3. [The first ten days](#3-the-first-ten-days), and [the first drought](#the-first-drought)
4. [Plants and the three kinds of land](#4-plants-and-the-three-kinds-of-land)
5. [Flumes and paddies, step by step](#5-flumes-and-paddies-step-by-step)
6. [Dry-ground crops: tea and pepper](#6-dry-ground-crops-tea-and-pepper)
7. [Food and the afternoon](#7-food-and-the-afternoon)
8. [The Ringtails](#8-the-ringtails)
9. [The Lantern Festival](#9-the-lantern-festival)
10. [The Great Flowering](#10-the-great-flowering)
11. [Late game: oxen, monuments, the Sky Lantern](#11-late-game-oxen-monuments-the-sky-lantern)
12. [When something looks wrong](#12-when-something-looks-wrong)

## 1. What is different from beavers

| | Folktails | Inkpaws |
|---|---|---|
| Building material | Planks from a lumber mill | Poles. Cut timber bamboo is already a pole. A Pole Mill also splits logs into poles |
| Late material | Treated planks | Cured poles from a Smoke Kiln: log smoke, no power |
| First crop | Carrots | Shoot bamboo, edible raw |
| Working day | A longer day is simply more work | From twelve to sixteen hours the work done is the same. A shorter day buys a free afternoon |
| Dry ground | Empty | Tea and Sichuan pepper |
| Night | Everyone sleeps | The Ringtails work |
| Fuel engines | Yes | None. Water wheels, kite windmills, power wheels |
| Bots | Bots | Wooden Oxen |

<!-- gen:lifts -->
A beaver lifts 14. An Inkpaw lifts 18.
<!-- /gen:lifts -->

Births, lifespan, childhood, hunger and thirst are the game's own. Levee, Dam, Floodgate, pumps, warehouses,
platforms, stairs and all the automation buildings are there under their usual names.

## 2. The afternoon bell

**[Bell]**

The afternoon bell is the game's working-hours control. It starts where any new game starts.

**The rule: rested pandas are quick pandas.** The shorter the working day, the faster Inkpaws work and walk. From
twelve to sixteen hours the bonus exactly makes up for the hours, so the village gets the same work done at any
length in that range. What you choose is how much afternoon the Inkpaws have, and how long the Ringtails' night is.

<!-- gen:bell -->
| Working day | Rested bonus | Work done in the day, against a plain 16-hour day |
|---|---|---|
| 10 hours | +33% | 83% |
| 11 hours | +33% | 91% |
| 12 hours | +33% | 100% |
| 13 hours | +22.8% | 100% |
| 14 hours | +14% | 100% |
| 15 hours | +6.4% | 100% |
| 16 hours | none | 100% |
| 18 hours | none | 112% |
<!-- /gen:bell -->

Things worth knowing:

* **The day's length is fixed at dawn.** Change the hours at noon and the panel shows today's bonus and
  tomorrow's. The change takes effect the next morning. You cannot work a long day and slide the bell back at dusk.
* **It covers walking.** Builders, haulers and gatherers mostly walk. A bonus on working speed alone would cost
  them a quarter of their day. This one does not.
* **It multiplies.** The bonus sits on top of whatever well-being already gives, in proportion. The game normally
  stops walking speed at twice normal; for Inkpaws that limit is raised, so happy pandas keep the full bonus.
* **Below twelve hours gains nothing more.** A shorter day than that is simply less work.
* **Long days are allowed.** Past sixteen hours there is no bonus and no penalty. What goes is the afternoon:
  naps, tea and the rest need off-duty hours, and a village with no time for them loses the well-being they give.
* **Where it shows:** a line under the working-hours panel, a line on each Inkpaw's panel, and inside the
  well-being bonus totals.

**The suggestion.** Once the village is settled the game says, once: "Your village is settled. Inkpaws work a short
day and work it well: shorten the working hours until the Rested bonus stops rising, and the afternoon is theirs."
Settled means your first Hammock or Teahouse is finished, or a few
days have passed, whichever comes first. It waits out a drought or a badtide.

**The sound.** One bell at the end of the working day and a lighter one at dawn, heard everywhere, once a Village
Hall stands.

**Advice.** Leave the day long until the village has water, food and beds. Shorten it once a Hammock is up and
there is somewhere to spend the afternoon. With Ringtails in the village, twelve and twelve is the natural
balance: every hour added to the Inkpaws' day is an hour off the Ringtails' night.

## 3. The first ten days

The order the design and the tutorial lead you through, on Normal. It is a sound start, not a tested optimum.

| When | Do | Why |
|---|---|---|
| First minutes | Lumberjack Flags first, more of them than you think, with trees marked. Then Water Pump and Gatherer Flag | A village starts with no logs, and nothing else can be built without them. The first week is short of logs, not of builders |
| Day 1 | Farmhouse with shoot bamboo on green ground near water. Inventor | Shoot bamboo is first on the crop list and the fastest food |
| Day 1–2 | Dens. A Hammock | Beds first. The Hammock is the cheapest afternoon place, and it counts as "settled" |
| Day 2–3 | Power Wheel and Pole Mill. Forester with timber bamboo on green ground | The mill gives the first poles from logs. Bamboo needs days to grow, so plant it now |
| Day 3–5 | Steamer. A Small Cistern | Steamed shoots are the first dish and feed more than raw ones. Cisterns carry the village through the first drought |
| Around day 5 | Shorten the day | See the bell |
| Day 6–10 | The first bamboo is cut: poles with no mill. A second crop: cabbage | Cabbage lasts longer without water than shoot bamboo |
| Day 6–10 **[Water]** | A Scoop Wheel in a current, a Flume Gate and a short flume to a second grove | The ground stays moist to each side of a flume, with no digging |
| Before the first drought | A Medium Cistern. Food in store | Bamboo and cabbage brown in a short drought and recover. Water for drinking is the thing to store |
| End of cycle 1 **[Ringtails]** | A Moon Loft, then a Night Builders' Post | Building goes on overnight |
| Cycle 2 | Rice in a paddy; pickles; tea bushes on brown ground and the first Teahouse; paper lanterns | Tea cannot exist in the first week: the bushes need time. Do not wait for it |

What those cost today:

<!-- gen:first_days -->
| Building | Cost | Science to unlock | Holds |
|---|---|---|---|
| Water Pump | 12 logs | none |  |
| Gatherer Flag | free | none |  |
| Lumberjack Flag | free | none |  |
| Farmhouse | 25 logs | none |  |
| Inventor | 12 logs | none |  |
| Den | 12 logs | none |  |
| Hammock | 4 logs | none |  |
| Power Wheel | 20 logs | none |  |
| Pole Mill | as in the game | as in the game |  |
| Forester | 12 logs | none |  |
| Steamer | 20 logs, 5 poles | 40 |  |
| Small Cistern | 15 logs | none | 40 water |
| Medium Cistern | 20 logs, 30 poles | 100 | 300 water |
| Scoop Wheel | 20 logs, 30 poles | 60 |  |
| Flume Gate | 6 logs, 6 poles | 40 |  |
| Flume | 2 poles | none |  |
| Moon Loft | 10 logs, 10 poles | 200 |  |
| Night Builders' Post | 15 logs, 10 poles | 50 |  |
<!-- /gen:first_days -->

On Hard, plant cabbage early: it is the hardier staple.

### The first drought

The first drought is the likeliest place to lose a new village, and it is lost on drinking water, not on food.

**Store water early.** A pump is not a store: it holds a little and stops. What carries the village is cisterns,
filled before the river stops. Build the first one in the first days and a bigger one before the warning.

<!-- gen:drought -->
* A Water Pump holds about 16 hours of its own pumping and then stops. It is not a store.
* Cisterns are the store: Small Cistern 40 water (15 logs; no science); Medium Cistern 300 water (20 logs, 30 poles; 100 science); Large Cistern 1,200 water (80 poles, 40 gears, 20 metal blocks; 500 science).
* Dry days a plant survives: shoot bamboo 5, cabbage 7, timber bamboo 10, persimmon tree 10. Tea and pepper need no water at all.
<!-- /gen:drought -->

What a drought does, in order:

1. **The river stops and the pumps with it.** From then on the village drinks from its cisterns.
2. **A Scoop Wheel stops**, because it needs a current, and says so. Water already standing in a flume line
   stays there and keeps the ground beside it wet for days.
3. **Crops stop growing and turn brown** when their ground dries. They are not dead. Each plant has a count of
   dry days it survives, and the count starts over the moment its ground is wet again. A first drought on Normal
   is shorter than any of them.
4. **The harvest pauses**, so the village eats from store. Steam shoots ahead of time: steaming makes more food
   out of the same field.
5. **Tea and pepper carry on.** They are the one harvest a drought cannot touch.

What to have before it: a full cistern or two, a few days of food, and the Farmhouse's fields close to water so
they recover fast. What you do not need yet: a Cistern Tap. The first drought does not ask for one. In longer
droughts, later, the tap pours stored water into a flume and keeps one strip of fields alive.

When the water comes back it runs down every flume again, and brown fields turn green without replanting.

**Workshops hold a lot.**

<!-- gen:shelves -->
A workshop that turns ingredients into goods holds inputs and outputs for 48 hours of work at full staffing. A pump holds what it would in the plain game.
<!-- /gen:shelves -->

That is so night couriers have something to carry, and so the day crew starts with full inputs. Early on it means
a new workshop draws a large first order of logs or poles. If poles are short, pause the workshop you need least.

## 4. Plants and the three kinds of land

The map already paints the rule. **Green ground** is moist: bamboo, cabbage, persimmons. **Brown ground** is dry:
tea and pepper. **Flooded fields** are for rice.

<!-- gen:plants -->
| Plant | Land | Planted by | Grows in | Yield | Survives |
|---|---|---|---|---|---|
| Shoot Bamboo | Moist | Farmhouse | 3 days | 2 bamboo shoots when harvested | 5 dry days |
| Cabbage | Moist | Farmhouse | 5 days | 3 cabbages when harvested | 7 dry days |
| Timber Bamboo | Moist | Forester | 5 days | 2 poles when cut; 2 bamboo mushrooms every 3 days while it stands | 10 dry days |
| Rice | Flooded, shallow | Paddy House | 8 days | 3 rice when harvested | 1 dry day |
| Tea Bush | Dry | Forester | 6 days | 3 tea leaves every 3 days while it stands | about 3 days with wet roots |
| Sichuan Pepper | Dry | Forester | 5 days | 2 Sichuan pepper every 3 days while it stands | about 3 days with wet roots |
| Persimmon Tree | Moist | Forester | 14 days | 3 logs when cut; 3 persimmons every 6 days while it stands | 10 dry days |
<!-- /gen:plants -->

Birch, pine, oak, blueberries and dandelions are still there. Fruit, mushrooms, tea leaves and pepper are picked
by the Gatherer Flag; trees and timber bamboo are cut by the Lumberjack Flag.

* A plant in trouble stops growing and turns brown. When its ground is right again the countdown starts over from
  nothing, and it carries on growing. Only a plant that runs out its whole countdown dies.
* Dead crops are cleared and replanted by the farmers. Inkpaw foresters replant dead trees by default.
* Mushrooms come from standing timber bamboo. A grove you cut flat gives poles and no mushrooms. Keep one grove
  for the Gatherer Flag.

## 5. Flumes and paddies, step by step

**[Water]**

A flume carries water one way along its arrow, level or downhill. It does not leak from its sides and water
does not run back up it. It never climbs.

<!-- gen:water -->
| Piece | What it does | Cost | Science to unlock |
|---|---|---|---|
| Flume Gate | The intake of a line. Sets how much water enters and shuts itself when the water turns bad | 6 logs, 6 poles | 40 |
| Flume | One tile of aqueduct on the ground | 2 poles | none |
| Flume Corner | A turn. Flumes do not bend on their own | 3 poles | none |
| Flume Drop | Steps the line down one level | 3 poles | none |
| Flume Bridge | Carries the line above the ground on a trestle | 4 poles, 1 log | 120 |
| Flume Bridge Span | A bridge piece that stands over another flume, so two lines can cross | 4 poles, 1 log | 120 |
| Paddy Spout | Keeps the field in front of it flooded to a shallow set depth | 6 poles | 150 |
| Scoop Wheel | Lifts water out of a current. No workers | 20 logs, 30 poles | 60 |
| Treadwheel Lift | Lifts water where there is no current. Turned by a worker, so only during the working day | 30 poles, 10 gears | 300 |
| Cistern Tap | A worker pours stored water into a flume or a basin | 8 logs, 8 poles | 250 |
| Dew Collector | A little drinking water with no workers, less in a drought | 15 poles, 4 paper | 300 |
| Trip-Hammer Mill | Pounds rice into rice flour. Its wheel stands in a flume or a stream; no power shafts | 30 logs, 20 poles, 10 gears | 200 |
| Dry-Stone Wall | Stops moisture spreading sideways through the soil, to keep a tea slope dry | 4 logs, 2 poles | 120 |

* **Flume Gate:** lets through 0.3 m³/s to start, adjustable up to 1. It shuts itself when the water behind it is 5% badwater or more, and reopens when it is clean.
* **Paddy Spout:** holds its field 0.3 deep unless you change it.
* **Scoop Wheel:** starts turning in a current of 0.15. Its panel shows the current it has and the current it wants.
* **Dew Collector:** 3.2 water a day in fair weather, 1.1 in a drought.
* **Cisterns:** Small Cistern holds 40 water (15 logs; no science); Medium Cistern holds 300 water (20 logs, 30 poles; 100 science); Large Cistern holds 1,200 water (80 poles, 40 gears, 20 metal blocks; 500 science).
<!-- /gen:water -->

### A first line

1. **Find the intake.** Either a pond or stream that stands level with or above where the flume starts, or a
   Scoop Wheel. The wheel needs a current. In still water it does nothing and says so.
2. **Place a Flume Gate** where the water comes in. Its arrow points down the line.
3. **Lay Flumes** along the arrow. Level is fine: in a test, sixty level tiles still delivered 92% of the flow.
   Use a Flume Drop to step down a level, a Corner to turn, a Bridge to cross a dip, a Bridge Span to cross
   another flume.
4. **Read the line if it stays dry.** Each piece says what is wrong: blocked, pointing the wrong way, intake dry,
   end dry, or closed by badwater.
5. **Plant beside it.** A flume on the ground keeps the soil moist six tiles to each side. That strip, thirteen
   tiles wide, is your bamboo grove and your cabbage field. This is the first payoff, and it needs no digging.

### A paddy

1. Pick level ground at the end of the line and give it edges one block high, so the water stays in. Levees or
   natural banks both work.
2. Put a **Paddy Spout** at the end of the flume, facing the field. It holds the field at a shallow depth and tops
   it up as water evaporates. One spout is enough for a whole level field.
3. Build a **Paddy House** and mark rice in the water.
4. If the field sits a block below the path, add stairs. In one test the farmers stood at the top with "Nothing to
   do in range" for the whole run.
5. For terraces, put one spout on each step, at the lower edge of the paddy above. Each field feeds the next.

Rice wants shallow water. In water deeper than one block it dies.

**A paddy wets a lot of ground.** Soil stays moist sixteen tiles around a paddy, and one level up beside it. Good
for bamboo. Bad for tea: see the next section.

### In a drought

* The Scoop Wheel stops when the current stops, and says why.
* A line that has backed up behind a full paddy is a reservoir of its own. In a test, eighteen flume tiles held
  about 19 m³ and kept a paddy and the ground beside the flume wet for six days with no help.
* After that, a **Cistern Tap** at the gate pours stored water into the line. It needs a worker, and water hauled
  to it. Its panel gives a rule of thumb for how much farmland a given store keeps alive.
* You do not need to pour all the time. A plant's countdown starts over whenever its soil is wet again, so one
  fill of the line every few days keeps a grove alive.
* In a badtide the gate shuts itself. Leave its switch on.

### If the water toolkit is switched off

Every flume piece becomes a solid block that holds no water and floods nothing. The spout is a plain fill valve.
Gate settings wait in the save and come back with it.

### Still being tested

The Trip-Hammer Mill and the Treadwheel Lift have been placed and finished in test runs, but not yet run with a
worker in a game. The Dry-Stone Wall's effect on moisture has not been measured in a run.

## 6. Dry-ground crops: tea and pepper

Tea bushes and Sichuan pepper grow on brown ground and need no water at all. A drought cannot touch them.

* **The Forester plants them and the Gatherer Flag picks them**, like berries. They are not in the Farmhouse's
  crop list.
* **Wet roots are a warning.** On moist ground a bush stops growing and shows the dying status. If the ground
  dries in time, it recovers and grows on. If not, it dies.
* **Keep them away from your water.** Moisture reaches six tiles from a flume and sixteen from a paddy. Plant
  tea out past the green. If you are not sure, look at the ground colour: brown is safe.
* **A Dry-Stone Wall** stops moisture spreading sideways through the soil, for when you want tea closer in.

Tea is a second-cycle goal. The bushes need time, and the Teahouse needs poles.

<!-- gen:tea -->
| Step | Where | Numbers |
|---|---|---|
| Grow | Forester, on dry ground | 6 days to grow, then 3 tea leaves every 3 days |
| Pick | Gatherer Flag |  |
| Roast | Tea Roastery (15 logs, 20 poles; 250 science) | 1 tea leaves → 2 tea, 0.75 h |
| Serve | Teahouse (25 logs, 25 poles; 150 science) | Uses 1 tea and 0.5 water for each hour it is serving. Closed when it has none |
<!-- /gen:tea -->

Tea is a dry good and keeps in any warehouse. Nobody drinks it from storage: the Tea need is met at the
Teahouse and nowhere else. Haulers, or night couriers, keep the Teahouse stocked.

Pepper has one use: hot pot.

## 7. Food and the afternoon

Every food fills the same hunger. What a dish adds is its own small need, worth well-being while it is met. A
bite every few days keeps it met, so variety is cheap.

<!-- gen:dishes -->
| Food | From | Recipe | Well-being while the need is met |
|---|---|---|---|
| Bamboo shoots | Farmhouse | raw | none |
| Cabbages | Farmhouse | raw | +1 |
| Persimmons | Gatherer Flag | raw | +1 |
| Bamboo mushrooms | Gatherer Flag | raw | +1 |
| Steamed shoots | Steamer | 1 bamboo shoot → 2 steamed shoots, 0.5 h, log fuel | +2 |
| Pickles | Pickle Yard | 2 cabbages → 5 pickles, 1.7 h | +2 |
| Steamed rice | Steamer | 1 rice → 4 steamed rice, 1 h, log fuel | +2 |
| Hot pot | Hot Pot Hall | 1 cabbage, 1 Sichuan pepper, 1 bamboo mushroom → 8 hot pot, 1.5 h, log fuel | +4 |
| Sweet rice balls | Kitchen | 1 rice flour, 1 persimmon → 5 sweet rice balls, 1 h, log fuel | +3 |
| Bamboo seed cakes | Kitchen | 1 bamboo seed, 1 rice flour → 6 bamboo seed cakes, 1.5 h, log fuel | +3 |

Where they are cooked:

| Building | Cost | Science to unlock |
|---|---|---|
| Steamer | 20 logs, 5 poles | 40 |
| Pickle Yard | 20 logs, 15 poles | 120 |
| Hot Pot Hall | 40 logs, 40 poles, 20 gears | 800 |
| Kitchen | 15 logs, 15 poles, 10 gears | 300 |
| Trip-Hammer Mill | 30 logs, 20 poles, 10 gears | 200 |

Rice flour: 1 rice → 1 rice flour, 0.5 h, at the Trip-Hammer Mill.
<!-- /gen:dishes -->

Pickles stretch land, not time. Food does not spoil in this game.

### The rice chain

Rice is the food of the second cycle onward, and everything after it hangs on it. One crop, three uses:

<!-- gen:rice -->
| Step | Where | Numbers |
|---|---|---|
| Grow | Paddy House (30 logs, 10 poles; 150 science), in a flooded field | 8 days to grow, 3 rice a plant |
| Steam | Steamer | 1 rice → 4 steamed rice, 1 h, log fuel |
| Mill | Trip-Hammer Mill (30 logs, 20 poles, 10 gears; 200 science), in a flume or a stream | 1 rice → 1 rice flour, 0.5 h |
| Cook | Kitchen (15 logs, 15 poles, 10 gears; 300 science) | 1 rice flour, 1 persimmon → 5 sweet rice balls, 1 h, log fuel |
| Cook | Kitchen (15 logs, 15 poles, 10 gears; 300 science) | 1 bamboo seed, 1 rice flour → 6 bamboo seed cakes, 1.5 h, log fuel |
<!-- /gen:rice -->

1. **A paddy first.** Rice grows only in shallow standing water: a walled field with a Paddy Spout **[Water]**, or
   any basin you can keep shallow with levees and a floodgate.
2. **Steamed rice** needs nothing new. The Steamer you built for shoots cooks it.
3. **Rice flour** needs a Trip-Hammer Mill **[Water]** standing in moving water. Flour is an ingredient, never
   eaten.
4. **The Kitchen** turns flour into sweet rice balls, with persimmons from an orchard that takes a long time to
   bear. Plant the persimmon trees when you dig the paddy, not when you build the Kitchen.
5. The same flour makes the most of **bamboo seed** after a Great Flowering.

Rice dies fast out of water. In a drought the paddy is the field to keep wet.

**The afternoon.** Off-duty pandas need somewhere to be. Each of these is its own need.

<!-- gen:afternoon -->
| Place | Need | Well-being | Fades from full | Cost | Notes |
|---|---|---|---|---|---|
| Hammock | Nap | +3 | in about 2 days | 4 logs; no science | One napper |
| Nap Platform | Nap | +3 | in about 2 days | 10 logs, 15 poles; 100 science | Several nappers; on the ground or on a roof |
| Teahouse | Tea | +4 | in about 3 days | 25 logs, 25 poles; 150 science | Needs tea and water in stock |
| Slide and Swing | Play | +2 | in about 5 days | 25 logs, 20 poles; 250 science |  |
| Kindergarten | Watching the young | +3 | in about 5 days | 60 logs, 40 poles; 400 science |  |
| Ink Studio | Ink painting | +2 | in about 8 days | 10 logs, 10 paper; 200 science |  |
| Hot Spring Bath | Soak | +3 | in about 5 days | 80 logs, 30 cured poles; 1,500 science | Uses water; wets the fur |
| Opera Stage | Opera | +5 | in about 8 days | 100 logs, 40 cured poles, 20 metal blocks; 1,200 science |  |
<!-- /gen:afternoon -->

Ringtails use the same places in their morning, so one Teahouse serves both peoples at different hours.

Decorations work as they do for beavers: each kind is its own small need, and they reach pandas at work.

## 8. The Ringtails

**[Ringtails]**

**The one rule: Inkpaws work from dawn to the bell. Ringtails work from the bell to dawn.**

### Inviting them

Build a **Moon Loft**. It is in the Night Watch group of the toolbar. When the first one is finished:

* Two Ringtail adults and a kit appear at its door and move in.
* One message states the rule.
* The night posts unlock for free. Before that they sit behind a science cost. The Star Tower is the exception:
  it keeps a science cost of its own.
* A second row appears under the population panel: Ringtails, working, idle.

The family comes once. A second loft is a second home, not a second family.

*Decided on 2026-11-25 and not yet in a build: if a district with a Moon Loft loses its last Ringtail, a new family
answers the lantern after a few days. Until that is in, do not let the Ringtails die out.*

### The night posts

<!-- gen:night_posts -->
Moon Loft: 10 logs, 10 poles; 200 science.

| Post | What it does | Cost | Workers |
|---|---|---|---|
| Night Builders' Post | Ringtail builders stock and raise construction sites through the night | 15 logs, 10 poles | up to 4 |
| Night Courier Post | Ringtail couriers refill workshops and clear their outputs and the flags overnight | 20 logs, 10 poles | up to 6 |
| Night Gatherers' Post | Ringtail gatherers gather at night: whatever a Gatherer Flag would pick in its range | 10 poles | up to 2 |
| Star Tower | Ringtail stargazers make science from the night sky | 60 poles, 30 gears, 10 paper | up to 4 |
<!-- /gen:night_posts -->

A post shows "Closed for the day. Ringtails start at the afternoon bell." by day. That is normal.

Night couriers are why Inkpaw workshops hold so much: in a two-day test with full-sized shelves the couriers
moved more than four times as many goods as with day-sized ones, and the workshops ran half as long again.

### How Ringtails differ

<!-- gen:peoples -->
|  | Inkpaw | Ringtail |
|---|---|---|
| Hours | Dawn to the bell | The bell to dawn |
| Lifts | 18 | 14 |
| Walking with a load | Slower, as in the game | Full speed |
| Rested bonus | From the length of the day | From the length of the night shift |
| Young | Cubs, born in homes | Kits, raised in Moon Lofts |
| Food, water, well-being, lifespan | The same | The same |
<!-- /gen:peoples -->

Running with a full basket is what makes a Ringtail a courier. Ringtails are rested by the length of their own
night shift, as Inkpaws are by the length of their day, so at twelve and twelve a night builder is meant to be as
good as a day builder. *That bonus is new code of 2026-11-25 and has not been run in a game yet.*

### Their day

A Ringtail comes off shift at dawn, sleeps a few hours, then has the rest of the morning for food and the
Teahouse. Its shift starts at the bell. Two limits protect it: the shift never starts so early that there is no
time to sleep, and never later than nightfall, so Ringtails hold the night even if you work the Inkpaws around
the clock. When Ringtails are in the village a wooden clapper answers the bell, and a pale arc on the clock shows
the night shift.

### Kits and numbers

Ringtail numbers follow **vacancies at night posts, not beds.**

* Each dawn, each Moon Loft may raise one kit, if the district has more night-post places than it has Ringtails
  and kits, nobody in the district is critically hungry or thirsty, and the loft has room.
* The loft's panel says where it stands: one kit each dawn while a night post has a vacancy; none for now,
  because no night post has a vacancy; no room for a kit; or none while anyone in the district is hungry or
  thirsty.
* Kits grow up into Ringtail adults and take the open places.
* **To get more Ringtails, build or enlarge a night post.** Ten lofts with no vacancy raise nobody.

### Homes

Moon Lofts belong to Ringtails. An Inkpaw may sleep in a spare loft bed and gives it up when a Ringtail or a kit
needs it. A Ringtail without a loft sleeps in any home.

### If you never build a Moon Loft

Nothing a village needs is missing. Only the Star Tower depends on Ringtails, and the science it makes is science
your inventors would also make, more slowly.

### If the Ringtails are switched off

Ringtails in a save load as Inkpaws with the same names, homes and needs. Night posts become ordinary Inkpaw
workplaces. Lofts are plain homes.

## 9. The Lantern Festival

**[Festival]**

Once a cycle, the whole village takes a day and a night off. Afterwards everyone is festive for most of a cycle
and Tradition rises by one.

Build a Festival Square and connect it by path. Its panel counts what the district has in its ordinary storage
and shows exactly what is still missing. Nothing has to be carried to the square: the goods stay in your
warehouses and are taken when you call.

<!-- gen:festival -->
Festival Square: 30 logs, 30 poles, 10 paper; 200 science.

| For | In the district's storage |
|---|---|
| A Small Festival | 40 paper lanterns, and 20 or more of each of 3 different cooked dishes |
| A Grand Festival | The same, and 20 fireworks |

Cooked dishes that count: steamed shoots, pickles, steamed rice, sweet rice balls, hot pot, bamboo seed cakes. Raw food does not.

Paper lanterns: 2 paper, 1 pole → 2 paper lanterns, 1.5 h, at the Lantern Workshop (10 logs, 20 poles; 100 science).

Paper: 1 pole → 2 paper, 1.56 h, at the Paper Mill.

The day:

| Hours after dawn | What happens |
|---|---|
| 0 | It begins. Nobody works except the crews of pumps and lifts, so the village keeps its water |
| Through the day | Pandas eat, drink, nap and drift to the square to dance. Ringtails sleep through the morning as usual, then come |
| 15.5 | Everyone gathers at the square. Lanterns rise, 24 of them |
| 19 | Fireworks, at a Grand Festival |
| 22 | The gathering ends |
| Next dawn | Work starts again. Tradition rises by one |

Festive spirit: +4 well-being for everyone, fading over about 25 days. A Grand Festival adds +1.

What Tradition unlocks, at no science cost:

| Tradition | Decorations |
|---|---|
| 1 | Goldfish Bowl, String Lanterns |
| 2 | Hanging Lantern |
| 3 | Garden Moon Gate |
<!-- /gen:festival -->

### Calling it

Press **Call the festival**, or switch on **Call it automatically when ready**. Called at any hour, it begins at the
next dawn and runs to the dawn after.

* Automatically, it is only called in fair weather, and never on the day before a drought or a badtide.
* By hand you may call it in any weather.
* At most one festival in each cycle.
* Everyone ends festive, whether or not they reached the square.
* With several districts, the texts now being prepared give the festival to the district whose square calls it,
  with one festival a cycle for the whole village. *Not in a build yet when this was written.*
* The cost is one day's work. A fed village can afford that. Critical needs still come first on the day.

Lanterns take a while to make. Start a cycle ahead.

**Known gap.** The lanterns that rise at dusk are drawn with the game's own firework trails for now. Their own
lantern art is being finished.

## 10. The Great Flowering

**[Flowering]**

Bamboo flowers once in a long while, all at once, and dies. It really does, and it really starves pandas. In the
game you get a full cycle of warning and a harvest from it.

<!-- gen:flowering -->
| When | What happens |
|---|---|
| Never before cycle 6 | Nothing |
| Start of the cycle before | The forecast: a notice, a line under the top bar, a line on every bamboo's panel |
| Start of the flowering cycle | Every grown plant of that bamboo, planted or wild, flowers. Young plants die |
| The first 3 days | Flowering plants bear bamboo seed. Farmers or lumberjacks take it as their ordinary harvest |
| Until day 9 | That bamboo rests. Planting marks stay and fields are replanted, but seedlings do not grow |
| 5 to 7 cycles later | The next Flowering, of the other bamboo |

The first Flowering is the shoot bamboo's. The two take turns.

| Bamboo | Seed | Time without its ordinary harvest |
|---|---|---|
| Shoot Bamboo | 3 bamboo seed from each grown plant | about 12 days: 9 of rest and 3 to grow |
| Timber Bamboo | 3 bamboo seed from each grown plant | about 14 days: 9 of rest and 5 to grow |

The setting, per save: normal, rare or off. Rare means the first one comes 3 cycles later and they are 9 to 11 cycles apart.

Bamboo seed cakes: 1 bamboo seed, 1 rice flour → 6 bamboo seed cakes, 1.5 h, log fuel, at the Kitchen.
<!-- /gen:flowering -->

It is always the first day of a cycle, so never in a drought or a badtide.

### Preparing

The forecast's tooltip tells you how much to store for each panda. In short:

* **Shoot bamboo:** food to cover the gap. Or lean on cabbage, rice and pickles.
* **Timber bamboo:** poles to cover the gap. The Pole Mill splits logs meanwhile. Mushrooms stop too.
* Keep farmers free for the seed days. Seed left on a dead crop is gone.
* For timber bamboo, mark the flowering groves for cutting. Dead flowering trees keep their seed until cut.
* Leave room in a warehouse for the seed.

A village that follows the forecast is not at risk. Switching the setting to off cancels a Flowering that has
been announced. The setting is opened from the line under the top bar or from any bamboo's panel.

### What the seed is for

Bamboo seed is not eaten as it is and it is not for planting. Bamboo replants itself from the planting marks. The
seed is cooked into **bamboo seed cakes**, a dish of its own with its own well-being, and one that counts toward
a festival. A Flowering leaves a great deal of seed at once, and seed does not spoil, so it becomes many days of
cakes.

What cooks it in this build:

<!-- gen:seed -->
* 1 bamboo seed, 1 rice flour → 6 bamboo seed cakes, 1.5 h, log fuel, at the Kitchen.
* 1 bamboo seed → 2 bamboo seed cakes, 1 h, log fuel, at the Steamer.
<!-- /gen:seed -->

The Kitchen's recipe with rice flour gets the most out of each seed, and it needs the rice chain: a paddy, a
Trip-Hammer Mill and a Kitchen. The Flowering never comes early in a game, which is time enough to have them. Seed
you cannot cook yet waits in a warehouse.

So the Flowering takes one harvest away for a while and gives another back. A village that stored food for the
gap and has a Kitchen comes out of it better fed than it went in.

## 11. Late game: oxen, monuments, the Sky Lantern

*In testing. Everything here is in the data and on its own model, and has been placed and finished in test runs.
No test has reached it by playing a village that far.*

### The numbers

<!-- gen:late -->
**Wooden Oxen.** The Ox Workshop (100 poles, 50 gears, 40 metal blocks; 1,000 science) builds one from 20 cured poles, 20 gears, 4 metal blocks in 96 hours of work. An ox lifts 30 against an Inkpaw's 18 and wears out after 90 days.

**Cured poles.** 1 pole → 1 cured pole, 3 h, log fuel, at the Smoke Kiln (20 logs, 40 poles, 20 gears; 600 science). No power.

| Monument | Cost | Science to unlock | Well-being |
|---|---|---|---|
| Memorial Arch | 250 logs, 800 poles | 3,000 | +6 |
| Great Sitting Panda | 1,400 poles, 700 cured poles, 650 metal blocks | 15,000 | +14 |
| Sky Lantern | 2,400 gears, 2,400 cured poles, 1,800 metal blocks, 500 paper | 20,000 | +10 |

The Sky Lantern is launched with 400 paper lanterns and 300 extract.

Lantern decorations are built from paper lanterns: Standing Lantern 1, Hanging Lantern 1, String Lanterns 3.
<!-- /gen:late -->

### Wooden Oxen

Wooden Oxen are the Inkpaws' bots. An ox needs no food, no water, no sleep and no home, and it works through the
day and the night. It carries far more than a panda. It wears out after a fixed number of days and is then gone,
so an ox is something you keep building, not something you own.

* **Where they pay:** long hauls, big construction sites, anything that is mostly carrying.
* **What they cost:** cured poles, gears and metal, and many hours at the Ox Workshop. That means a Smoke Kiln and
  a metal supply first. They are a late-game answer, not a way out of an early labour shortage.
* **What they do not change:** well-being. Oxen have none and add none.
* **Where they do not work:** night posts belong to the Ringtails.

### Power

Power is bamboo water wheels, kite windmills and power wheels. There are no fuel engines.

### After the wonder

Launching the Sky Lantern is the last goal the faction sets. There is nothing after it: no further tier, no
second wonder. From there the game is a sandbox, as it is for Folktails and Iron Teeth. Build the valley you want.

Paper lanterns never stop being useful: decorations are built from them, each festival uses them, and the wonder
takes hundreds.

## 12. When something looks wrong

| You see | It means |
|---|---|
| "... is switched off in the file PandabornFactions.txt" | You, or someone, switched that part off. The README says how the file works |
| "... is switched off until the mod is updated for this game version" | A part of the mod did not load after a game update. The game still plays; its buildings behave like plain ones until the mod is updated. The notification log entry "Pandaborn - Factions:" lists every part |
| A notice that the mod is enabled twice | A local copy and a Workshop copy are both on. Switch one off |
| A flume that stays dry | Select it. The piece names the problem |
| "No current at the wheel" on a Scoop Wheel | Still water. Move it into a channel where the river runs |
| A night post "Closed for the day" | It is day. Ringtails start at the bell |
| A Moon Loft with "Kits: none for now. No night post has a vacancy: build another." | Build or enlarge a night post |
| A tea bush with the dying status | Its roots are wet. Look for a flume or paddy within range |
| A Teahouse that is closed | It has no tea or no water |
| Coats change after loading a save | The game picks a coat again on every load, for every faction |

Removing the mod breaks Inkpaws saves. Folktails and Iron Teeth saves are not affected.
