# Balance: the colony model and the first-pass numbers

Status: first pass, 2026-11-14, against design revision 4 (`docs/DESIGN.md`, `docs/CONTENT.md`). Every number here
comes from the colony model in [`tools/sim/`](../../tools/sim/README.md), which follows
[`game-mechanics.md`](game-mechanics.md). Full scenario output is in `tools/sim/out/*.md`; rerun with
`tools/sim/run.py all`. The proposed stat sheet is at the end of this page and, machine-readable, in
`tools/sim/out/statsheet.json` (one entry per catalogue item, generated from `tools/sim/pandasim/stats.py`).

Nothing here was measured in a running game. "Model" means the model's arithmetic on the reference's rules.

## Summary

* **Calibration is good.** The model reproduces the reference's vanilla ratios to within a few percent (haulers,
  construction trips, land per beaver, pumps per beaver, the Normal thirst deadline). It disagrees with the
  reference's hand arithmetic on self-supplied workshops, for a reason worth knowing (below).
* **The opening is log-bound, not builder-bound.** Two woodcutters make about 30 logs a day; two builders can place
  60 (Folktails) or 86 (Inkpaws with lift 18). A stronger carrier does not speed the first week on pine. What makes
  the Inkpaw opening smoother is food: shoots arrive on day 4.5 against carrots on day 5.9, and the lowest food
  stock is 66 against 21.
* **The rested bonus works only if it multiplies, and must cover walking.** As proposed (+33% at 12 hours, linear
  to 0 at 16, on working and walking speed, scaling the whole multiplier) twelve hours does exactly what sixteen
  does in every job. As a flat bonus delta it loses 8–17% at mid-game wellbeing. On working speed alone it gives
  the veteran review's 77% for builders.
* **Rituals make the bell matter.** All eight leisure needs fit in a 14-hour day; at 16 hours only two do, which
  costs a settled colony about 10 wellbeing and 17% of its output. With Ringtails, 12/12 is the peak.
* **Ringtails should lift 14, not 18.** Full-speed carrying already makes a Ringtail at 14 equal to an Inkpaw
  builder on the 12/12 day; at 18 they would be 1.4–1.5 times better. The best mix is 20–40% Ringtails, and the
  curve is flat there.
* **Plants that pause in a drought prevent the death spiral.** In a 9-day drought with 2 days of food stored, a
  colony of 60 loses 17 and recovers in 2 days if its crops pause; it collapses to 3–6 if they die. The review's
  290–340 stored shoots is right for dying bamboo; with the proposed tolerances 144 cover a 3-day first drought.
* **Poles cost half a plank's labour** (no mill). With costs a straight Plank → Pole rename, ordinary Inkpaw
  construction is 25–40% cheaper. Monuments and the wonder are re-costed so the late game is the same stretch.

## Calibration on vanilla Folktails

| Item | Reference | Model |
|---|---|---|
| Hauler, food / water / logs a day at 20 tiles | 386 / 193 / 55 | 387 / 194 / 55 |
| Bakery: builder trips, walking h, building h (20 tiles) | 15, ~17, 2 | 15, 17.4, 2 |
| Uptime without haulers: lumber mill, bakery, smelter | 59%, 73%, < 45% | 52%, 58%, 36% |
| Carrot tiles per beaver; wheat tiles per beaver as bread | 3.6; 1.8 | 3.6; 1.8 |
| Wheat tiles one farmer keeps | ~90 | 84 |
| Beavers per pump worker, tank next door | ~20 | 21 |
| Normal start, no pump: first critical thirst | day 1.43 | day 1.42 |
| Normal start, no farm, gatherer + 30 wild bushes: first hunger | 3.7 d of berries alone | day 6.9 |
| Normal opening: first carrots; lowest food stock | tight | day 5.9; 21 items |
| First Bakery (440 science) with 1 / 2 inventors | mid cycle 1 to cycle 2 | day 30 / day 17, + 10 d of wheat |
| Folktails working day, mid game | 16 is about right | 16 h: 31.4; 17 h: 33.4; 18 h: 28.3 (leisure needs lapse) |

The workshop rows differ because the vanilla order empties output before it fetches input (§4.2): a lone worker
carries out two planks on a full round trip each time its two logs run out. The reference assumed half a delivery
trip per fetch. The model follows the order, so its self-supplied uptimes are 7–15 points lower. Everything that
depends on haulers and couriers uses the model's figures. This is the first thing worth measuring in game.

## Q1. The opening

Hour-by-hour opening, Normal, 9 adults and 4 children, 30 wild berry bushes, two woodcutters on pine, the same
order of reflexes for both factions (`openings.py`). "Built" is material units placed by that day.

| Case | First crop (day) | Lowest food | Hungry colonist-hours | Built d5 | d7 | d10 | d14 |
|---|---|---|---|---|---|---|---|
| Folktails Normal (carrots) | 5.9 | 21 | 0 | 139 | 166 | 285 | 431 |
| Inkpaws Normal (shoots, cabbage, steamer) | 4.5 | 66 | 0 | 124 | 190 | 307 | 413 |
| Folktails Hard | 5.9 | 0 | 0 | 139 | 166 | 285 | 431 |
| Inkpaws Hard | 4.5 | 26 | 0 | 124 | 190 | 307 | 413 |
| Inkpaws, lift 14 | 4.9 | 66 | 0 | 124 | 178 | 307 | 388 |

**Shoot bamboo.** Growth 3 days, 2 shoots a harvest: first shoots on day 4.5 counting from the first minute
(planting starts when the Farmstead is up, about day 1.4). Growth 2 days would bring day 3.4 and twice the stock
(too generous: it never lets the berries matter); growth 4 matches carrots and removes the head start. Per raw shoot
a farmer works 0.68 h against 0.51 h for a carrot, and a shoot field needs 1.5 tile-days per shoot against 1.33:
shoots are fast but costly, so cabbage, the Steamer (×2) and rice stay worth taking. Berries are still eaten: 154 in
the first two weeks (Folktails 230).

**Carrier strength.** Where builders are the limit (16-hour day, against a Folktails builder):

| Lift | Logs a trip | Poles a trip (weight 3) | Log-only buildings | Mid-game mix | Mix with poles of weight 2 | Oak woodcutter |
|---|---|---|---|---|---|---|
| 14 | 2 | 4 | 1.00 | 1.00 | 1.14 | 1.00 |
| 16 | 2 | 5 | 1.00 | 1.08 | 1.19 | 1.00 |
| **18** | **3** | **6** | **1.43** | **1.41** | 1.55 | 1.28 |
| 20 | 3 | 6 | 1.43 | 1.41 | 1.58 | 1.28 |
| 24 | 4 | 8 | 1.83 | 1.78 | 1.94 | 1.59 |

Lift 18 is the smallest that moves a third log, so it gives +40% to building and hauling without approaching
twice. Lighter poles add only 10% more and would need a global data change; keep poles at the plank weight 3, which
also keeps the "a pole is the vanilla plank renamed" option open. On pine, logs come one tree per trip whatever the
lift, so the first week is set by woodcutters. In an oak forest the Inkpaws place 22% more by day 5 (298 against
245).

### First droughts

Proposed tolerances (`DaysToDieDry`): shoot bamboo 5, cabbage 7, timber bamboo 7. While dry, a plant pauses and
keeps its progress; the timer resets when water returns (§7.2). Share of droughts an unirrigated plant survives:

| | Drought 1 | 2 | 3 | 5 |
|---|---|---|---|---|
| Normal: shoot bamboo (5) | 100% | 99% | 74% | 18% |
| Normal: cabbage, timber bamboo (7) | 100% | 100% | 100% | 75% |
| Normal: Folktails carrot (2) | 20% | 0% | 0% | 0% |
| Hard: shoot bamboo (5) | 66% | 24% | 4% | 0% |
| Hard: cabbage, timber bamboo (7) | 100% | 75% | 40% | 3% |

Hourly opening with a drought (the scripted player does not stock up for the forecast, so these are worst cases):

| Case | Folktails | Inkpaws, proposed | Inkpaws, bamboo dies at once |
|---|---|---|---|
| Normal, day 14, 3 days | 144 hungry hours, no deaths | none | none |
| Normal, day 14, 5 days | 2 deaths | no hunger; thirsty hours (cisterns too small) | no hunger |
| Hard, day 6, 3 days | 7 of 13 die | 1 dies | 9 die |
| Hard, day 6, 4 days | all 13 die | 5 die | all die |
| Hard, day 6, 6 days | all die | all die | all die |

Stored food for 18 colonists: with pausing plants, consumption × drought days (3 days: 144; 5 days: 240). With
dying plants, add replanting and three days of growth: 312, which is the review's 290–340. **The Hard start is at
least as playable as vanilla Hard**: the scripted Folktails colony dies in a 4-day day-6 drought, the Inkpaws lose
5; both need a player who stocks food. Cabbage, not shoots, is the Hard staple.

## Q2. The afternoon bell

Output per worker against a Folktails worker on a 16-hour day at the same wellbeing (lift 14 throughout, so only the
bonus differs):

| Wellbeing | Variant | Hours | Workshop + haulers | Self-supplied workshop | Farmer | Gatherer | Woodcutter | Builder | Hauler |
|---|---|---|---|---|---|---|---|---|---|
| 0–50 | **Proposed (work and walk, multiplicative)** | 12 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| 0–50 | Proposed | 14 | 1.02 | 1.00–1.04 | 1.02 | 1.02 | 1.02 | 1.02 | 1.02 |
| 20 | Same curve as a flat bonus delta | 12 | 0.89 | 0.90 | 0.92 | 0.93 | 0.93 | 0.96 | 0.97 |
| 50 | Same curve as a flat bonus delta | 12 | 0.83 | 0.84 | 0.87 | 0.88 | 0.88 | 0.91 | 0.92 |
| 0–80 | Revision 3: working speed only | 12 | 0.99–1.00 | 0.84–0.92 | 0.87–0.91 | 0.83–0.87 | 0.82–0.86 | **0.76–0.77** | 0.75 |
| 80 | Proposed | 12 | 1.00 | 0.92 | 0.94 | 0.92 | 0.92 | 0.89 | 0.88 |

* **The veteran review's 77% is confirmed** for a working-speed-only bonus.
* **Bonuses add in the game** (`1 + Σ deltas`). A constant +0.33 is worth +33% at wellbeing 0 but only +11% at
  wellbeing 50, so the code must re-add `bonus × (current multiplier without it)` whenever wellbeing changes.
* **MovementSpeed is clamped at 2.0** (BonusTypes). Above wellbeing ~60 the walking half of the bonus is cut off, so
  a twelve-hour day loses up to 12% on walking jobs; a 13–14 hour bell is then best. Acceptable; say it in the
  tooltip.
* The draft linear taper bulges about 2% above flat at 13–14 hours. An exactly flat curve is `16 / hours − 1`
  (13 h +23%, 14 h +14%, 15 h +7%); the difference does not matter, and "+33% at 12, nothing at 16" is easier to
  read.

### Rituals and leisure time

One representative Inkpaw with all eight leisure needs built (Nap daily; Teahouse, Play, Cub-watching, Soak every
3–4 days; Contemplation and Performance weekly; Campfire). Tea is drunk on ordinary drinking trips and costs no
leisure time.

| Bell | Leisure hours | Used | Needs held | Leisure wellbeing (of 20) | Nap hours |
|---|---|---|---|---|---|
| 10 | 8.7 | 6.6 | 8/8 | 20 | 1.3 |
| 12 | 6.7 | 6.6 | 8/8 | 20 | 1.3 |
| 14 | 4.5 | 4.3 | 8/8 | 20 | 1.0 |
| 15 | 3.4 | 3.1 | some lapse | 19 | 1.0 |
| 16 | 2.3 | 2.3 | 2/8 | 10 | 1.0 |
| 18 | 0.3 | 0 | 0/8 | 0 | 0 |

Buildings per 100 colonists on a 12-hour bell (second figure: 30% Ringtails share them in their morning): Nap
Platform 3.5 (1.9), Hot Spring 1.0 (0.6), Slide and Swing 1.0 (0.6), Kindergarten 0.7 (0.4), Teahouse 0.7 (0.4),
Ink Studio with 4 seats 2.1 (1.1), Opera 0.4 (0.2), Campfire 1.7 (0.9). About ten leisure buildings per hundred,
against a Folktails colony's six or seven: reasonable, and no hammock walls.

### Is 12/12 the balance point?

Colony output per colonist in "beaver 16-hour days at wellbeing 35", leisure re-simulated at each bell:

| Ringtails | Bell 10 | 12 | 13 | 14 | 16 | 18 |
|---|---|---|---|---|---|---|
| 0% | 0.83 | 1.00 | 1.02 | 1.02 | 0.83 | 0.75 |
| 25% | 0.88 | **1.00** | 0.99 | 0.97 | 0.79 | 0.69 |
| 40% | 0.91 | **1.00** | 0.98 | 0.95 | 0.77 | 0.65 |

Without Ringtails, 12–14 hours are flat. With Ringtails, 12 is the peak because every hour of Inkpaw day is an hour
less of Ringtail night. Sixteen hours is about 17% worse for a settled colony, through lost rituals, not through
the bonus.

## Q3. Food ladder

Per unit, wellbeing 20, 16-hour day. Land in tile-days per unit; labour in worker-hours per unit (farm, gather,
cook, fuel). "Per wb per 100" = worker-hours a day that keep +1 wellbeing for 100 colonists (25 units a day hold a
dish need).

| Food | Dish wb | Land | Labour | As staple: labour a colonist-day | Per wb per 100 | Buildings |
|---|---|---|---|---|---|---|
| Berries (wild) | 0 | 4.00 | 0.35 | 0.93 | – | Gatherer Flag |
| Bamboo shoots | 0 | 1.50 | 0.50 | 1.33 | – | Farmstead |
| Cabbage | 1 | 1.67 | 0.37 | 0.98 | 9.2 | Farmstead |
| Persimmons | 1 | 2.00 | 0.35 | 0.94 | 8.8 | Forester, Gatherer |
| Bamboo mushrooms | 1 | 1.50 | 0.44 | 1.18 | 11.0 | timber grove, Gatherer |
| Steamed shoots | 1 | 0.75 | 0.48 | 1.29 | 12.1 | Steamer |
| Pickles | 2 | 0.56 | 0.37 | 0.99 | 4.6 | Pickle Yard |
| Steamed rice | 2 | 0.67 | 0.31 | 0.83 | 3.9 | Paddy House, Steamer |
| Sweet rice balls | 2 | 0.93 | 0.39 | 1.05 | 4.9 | Trip-Hammer Mill, Kitchen |
| Hot pot | 3 | 0.71 | 0.32 | 0.86 | 2.7 | Hot Pot Hall |
| Tea (a cup) | 2 | 0.33 | 0.27 | – | 3.3 | Tea Roastery |
| *FT carrot* | 1 | 1.33 | 0.37 | 0.98 | 9.2 | |
| *FT grilled potato* | 2 | 1.50 | 0.40 | 1.06 | 5.0 | |
| *FT bread* | 2 | 0.67 | 0.32 | 0.84 | 3.9 | |

* Each step is worth taking: cost per wellbeing point falls from 9–12 (raw foods, steamed shoots) to 4–5 (pickles,
  rice, rice balls) to 2.7 (hot pot). Steamed rice matches bread; cabbage matches the carrot.
* Unlock order and science (two inventors at wellbeing 0, 32 science a day): shoots and cabbage (0), steamed shoots
  (40, day 1), persimmons (0), pickles (120, day 5), steamed rice (150, day 10), tea (250, day 18), sweet rice balls
  (500, day 33), mushrooms (0, needs standing timber), hot pot (800, day 58), seed cakes (a Flowering). Something
  new every 4–10 days early, every 15–25 later.
* **Dry land cannot become a free staple.** Pepper has no Hunger effect; it only multiplies cabbage in hot pot.
  Tea needs one water per three cups, and its own need is non-wastable, so a colonist drinks about two cups a day.
* Pickles stretch land, not time: food never spoils in Timberborn, so every dish keeps equally well.

## Q4. Water

Drinking: 2.12 water a colonist a day on Normal and Hard (0.85 on Easy), 0.42 m³ of map water.

Drought stores, 95th-percentile length:

| Mode | Drought no. | Days | Water a colonist | Medium cisterns (300) for 50 | With tea |
|---|---|---|---|---|---|
| Normal | 1 | 3 | 6 | 1.1 | 0.8 |
| Normal | 2 | 4 | 8 | 1.4 | 1.0 |
| Normal | 3 | 6 | 13 | 2.1 | 1.5 |
| Normal | 5 | 8 | 17 | 2.8 | 2.0 |
| Normal | 8+ | 9 | 19 | 3.2 | 2.3 |
| Hard | 1 | 6 | 13 | 2.1 | 1.5 |
| Hard | 3 | 10 | 21 | 3.5 | 2.5 |
| Hard | 5 | 14 | 30 | 4.9 | 3.6 |
| Hard | 8 | 20 | 42 | 7.1 | 5.1 |
| Hard | 13+ | 29 | 62 | 10.3 | 7.4 |

**Tea.** The Tea need (+0.3 a cup, −0.6 a day, non-wastable) means two cups a day. The thirst per cup decides
everything:

| Thirst per cup | Water a colonist-day | Saving |
|---|---|---|
| **0.20** | 1.58 | **26%** |
| 0.25 | 1.27 | 40% |
| 0.33 | 0.79 | 63% (tea becomes mandatory) |
| 0.25 with a wastable need | 0.93 | 56% |

0.2 makes water go a quarter further: useful in a long drought, never required.

**Dew collector.** At 2 water a day (0.67 in drought), 10 collectors cover 6% of a 50-colony's drinking in a
drought: a lifeline for a handful. Without a limit, 53 collectors (800 poles) would replace the pumps of 50
colonists and repay a pump worker in about three weeks, so data alone cannot stop spamming. Add a crowding rule to
the prototype's `DewLimiter`: efficiency divided by the number of collectors within 6 tiles.

**Paddies.** Rice 3 per 8 days, steamed ×4: 1.8 paddy tiles per colonist (bread: 1.8 wheat tiles). Standing water
loses about 0.28 water a tile a day, so a paddy colonist costs about 0.5 water a day on top of drinking.

**Cistern tap.** A one-tile flume loses about 1.5 water a tile a day (evaporation factor 6.5). A tap pouring 1 water
an hour keeps about 16 tiles of ground flume wet, whose 1–2-tile strip holds 20–30 bamboo tiles; a 6-day drought
costs 144 water, half a Medium Cistern. Worth it to keep a long drought from killing timber (7 days).

## Q5. Ringtails

Per worker per shift, wellbeing 20, Ringtail lift 14 and no slowing when loaded:

| Bell | Ringtail shift | Ringtail builder | Inkpaw builder | FT builder (16 h) | Ringtail courier (water) | Inkpaw porter | Ringtail forager | Inkpaw forager | Star Tower science |
|---|---|---|---|---|---|---|---|---|---|
| 12 | 12 | 77 | 77 | 54 | 329 | 282 | 25 | 19 | 85 |
| 14 | 10 | 64 | 79 | 54 | 273 | 288 | 21 | 20 | 71 |
| 16 | 8 | 51 | 77 | 54 | 217 | 282 | 16 | 19 | 56 |

Ringtail lift against an Inkpaw on 12/12: lift 12 → builders 1.00, couriers 1.00; **14 → 1.00, 1.17**; 16 → 1.08,
1.33; 18 → 1.40, 1.50. At 14 the Ringtail's speciality (full speed loaded) matches the Inkpaw's (lifts more).

**Night Courier Post.** An Inkpaw workshop on a 12-hour day that supplies itself, with couriers filling every input
and emptying the output overnight (15 tiles):

| Workshop | Alone | With night couriers | With day porters | Courier hours a night | Inkpaw hours gained |
|---|---|---|---|---|---|
| Lumber-mill-like (1 log → 1) | 57% | 73% | 95% | 1.1 | 1.7 |
| Bakery-like (Kitchen, Steamer) | 61% | 100% | 95% | 3.3 | 4.7 |
| Smelter | 33% | 92% | 95% | 6.0 | 6.9 |
| Gear Workshop | 87% | 99% | 95% | 0.9 | 1.2 |
| Gristmill-like (Trip-Hammer) | 70% | 67% | 95% | 0.4 | – |

A courier-hour buys 1.1–1.6 Inkpaw hours wherever the input buffer holds more than a shift (kitchen 38 h, smelter
26 h). Short buffers (the mill's 10 h) gain nothing. One courier keeps 2 (smelters) to 13 (gear workshops) going.

**Night Builders' Post** is worth exactly an Inkpaw builder per Ringtail on 12/12, working while the day crew
sleeps: construction continues around the clock. **Night Forager's Post** picks 25 mushrooms a shift (enough for
hot pot for 200 colonists). **Star Tower** gives 85 science a Ringtail a shift, 5 times an inventor.

**Best mix** (colony output in Inkpaw-worker equivalents; Ringtail jobs limited to building, hauling, gathering
and science, up to 1.5× their share of a day colony's labour): 0% → 1.00, 10% → 1.04, 20% → 1.08, 30% → 1.10,
40% → 1.10, 50% → 1.01 (Ringtails idle). Flat from 20 to 40%; the Moon Loft rule (kits only while jobs are open)
keeps a colony from passing the edge.

## Q6. Population

Median of 12 runs, homes built as needed (1 + 0.12 beds per adult a day), wellbeing rising from 4 to 25:

| Case | Days to 50 | Days to 100 |
|---|---|---|
| Folktails | 24 | 36 |
| Inkpaws, vanilla births (revision 4) | 24 | 36 |
| Inkpaws + Ringtails (first Moon Loft day 18) | 22 | 34 |
| Revision 3 slow breeding (0.06 a home entry, life 70, childhood 8) | 46 | 66 |

The slow breeding of revision 3 would have doubled the time to 100; dropping it was right. Keep vanilla life (50
days) and childhood (6).

**Death spiral** (60 colonists, a 9-day drought at day 60):

| Crops in drought | Food stored | Lowest population | Starved | Days to recover |
|---|---|---|---|---|
| Pause (proposed) | 2 days | 43 | 17 | 2 |
| Pause | 6 days | 60 | 0 | – |
| Die after 4 days, 4 days to regrow | 2 days | 6 | 61 | 26 |
| Die at once | 2 days | 3 | 62 | 32 |
| Either | 6 days | 59–60 | 0 | – |

Pausing crops turn a colony-ending drought into a bad week. A pantry of six days does the same.

## Q7. Great Flowering and the Festival

| Colonists | Food from shoots | Reserve if replanting is allowed at once | Reserve if blocked for the season | Poles to stock (season) | Bamboo seed | Seed-cake days for everyone |
|---|---|---|---|---|---|---|
| 40 | 35% | 149 | 560 | 210 | 168 | 67 |
| 80 | 20% | 171 | 640 | 420 | 192 | 38 |
| 150 | 20% | 380 | 1200 | 788 | 360 | 38 |

If farmers may replant at once, a Flowering is a four-day blip. For "a food season to bridge", the flowered bamboo
must not be replantable until the next temperate season (a planting check in code). Then the reserve is about 14
food a colonist (8 above 60 colonists, when shoots matter less) and 5 poles a colonist, and the seed (3 a plant,
4 cakes a seed) keeps the best dish need for everyone for 5–10 weeks. First at cycle 6, then every 5–7 cycles,
alternating: 4–5 Flowerings in a 30-cycle game.

**Small Festival in cycle 2.** Steamer, Pickle Yard, Paddy House (three cooked dishes), Paper Mill, Lantern
Workshop and Festival Square cost 1,060 science: about day 28 with two inventors, the start of cycle 2. Forty
lanterns are 40 paper and 20 poles. Payoff at wellbeing ~20 against a day's lost work: festive +3 for 17 days
returns 1.1 days; **+4 for 20 days (decay 0.05) returns 1.8**: worth calling, not compulsory.

## Q8. Late game

Worker-days per unit made and delivered (wellbeing 30; one worker-day is 16 h for Folktails and 12 h for Inkpaws,
the same output):

| Material | Folktails | Inkpaws | |
|---|---|---|---|
| Log | 0.085 | 0.072 | |
| Plank / Pole | 0.112 | 0.055 | no mill |
| Gear | 0.202 | 0.145 | from a pole |
| Treated plank / Cured pole | 0.236 | 0.162 | no resin |
| Metal block | 0.387 | 0.377 | |

Monuments re-costed to equal Folktails labour: Memorial Arch (Awe +6) = Farmer Monument + Brazier of Bonding,
62 worker-days → Log 250, Pole 800. Great Sitting Panda (Awe +12) = Fountain of Joy + Hall of Abundance, 435 →
Pole 1,400, Cured Pole 700, Metal Block 650. Sky Lantern = Earth Recultivator, 1,882 → Gear 2,400, Cured Pole
2,400, Metal Block 1,800, Paper 500, plus the vanilla 15,000 build hours.

**Wooden Ox against a Folktails bot**, per day: hauling 448 planks (supplied bot 465), building 160 units (176),
kitchen 180 bread (295); no upkeep (the bot's supplies cost about 3 worker-hours a day), life 90 days (70), cost
7.4 worker-days (9.3). Strong and slow, a little weaker in workshops, cheaper to keep: a fair trade.

## Design claims the model contradicts or weakens

| # | Claim | Finding | Change |
|---|---|---|---|
| 1 | "Poles are light, so builders carry more per trip"; fast building is felt in the first hour | The first week is log-bound: two woodcutters feed 30 logs a day, two builders could place 60–86. Lift changes nothing on pine before day 7 | Keep lift 18 and pole weight 3; tell the player early that three or four lumberjack flags pay; the "faster building" feeling arrives in the first cycle, not the first hour |
| 2 | "At twelve hours they get as much done as beavers in sixteen" | True only if the bonus multiplies the whole multiplier and covers walking; a flat delta loses 8–17% at wellbeing 20–50; the 2.0 walking clamp costs up to 12% above wellbeing 60 | Code re-adds `bonus × multiplier` on every wellbeing change; tooltip notes that very happy pandas gain little from a shorter day |
| 3 | "Long days simply remove the bonus. No punishment" | With rituals built, 16 hours keeps 2 of 8 leisure needs: −10 wellbeing, −17% output | Say it on the slider ("long days leave no time for tea and naps"); or shorten rituals so 15 hours keeps 6 of 8 |
| 4 | "Twelve and twelve is the natural balance" | Confirmed with 20%+ Ringtails; without them 12–14 are flat | None |
| 5 | Ringtails "otherwise share Inkpaw stats" (lift 18) | Full-speed carrying plus lift 18 makes them 1.4–1.5× better builders and couriers | Ringtail lift 14 (matches DESIGN's "Inkpaws lift more") |
| 6 | Bamboo "ready in about three days" | Three days from planting is day 4.5 from the first minute | Fine; the tutorial should not promise day 3 |
| 7 | The review's 290–340 stored shoots for the first drought | Right only if bamboo dies; with pausing plants, 144 for a 3-day drought | Proposed tolerances (5 / 7 / 7) |
| 8 | "Both bamboos shrug off a short drought and die in a long one" | Holds on Normal. On Hard shoot bamboo survives only 66% of first droughts | Cabbage (7) is the Hard staple; say so in the Hard tips |
| 9 | "Pickles: the way to stretch a harvest" (draft 1: "pantry food") | Food never spoils; pickles stretch land (0.56 tile-days against 1.67), not time | Keep as land-stretcher; drop any pantry wording |
| 10 | Tea "three cups from one water" | Fine as a recipe; the thirst per cup decides whether tea is optional (0.2: −26%) or mandatory (0.33: −63%) | Thirst 0.2 per cup, Tea need non-wastable |
| 11 | Dew collector "weak, weaker in drought" stops spamming | At any useful yield, 50+ collectors repay a pump worker in weeks | Crowding rule in `DewLimiter` (÷ collectors within 6 tiles) |
| 12 | Flowering "a food season to bridge" | With immediate replanting it is a four-day blip | Block replanting of the flowered bamboo until the next temperate season |
| 13 | Festival "costs a day's work" and pays | +3 for 16 days only breaks even | Festive +4, decay 0.05 (20 days) |
| 14 | Poles replace planks with costs unchanged; mid game "comparable" | Poles cost half a plank's labour: ordinary construction is 25–40% cheaper | Accept as the faction's easier building (its other costs: rituals, short days); if play tests find the mid game too easy, timber bamboo gives 1 pole a cut |
| 15 | Night couriers "keep shelves full" | Only where an input buffer holds more than a shift (kitchens, smelter, gears); nothing for mills | None; the courier post's tooltip should name the buildings it helps |

## The five numbers least certain, and how to measure them

| Number | Why uncertain | Measure in game |
|---|---|---|
| Self-supplied workshop uptime (lumber mill 52%, bakery 58%) | Rests on "empty output before fill input" read from the module order; the reference assumed otherwise | Dev harness: a lumber mill, one worker, no haulers, log pile 20 tiles away; count planks over 3 days (model 6.7 a day, reference 7.5) |
| Off-duty time: ~4 h sleep block and ~1.9 h of food trips, which set how many rituals fit (12 h: 6.7 h leisure; 16 h: 2.3 h) | The bedtime rule and food-visit lengths are inferred | Log one colonist's behaviour every tick for 5 days at 12 and 16 working hours; sum hours by behaviour |
| Shoot bamboo and cabbage `DaysToDieDry` 5 and 7 | Assumes ripe crops can still be harvested while dying and that dying crops resume fully | WaterLab drought: a ripe and a growing field; check harvest during the drought and growth after 3 and 6 dry days |
| Cistern Tap 1 water/h for 16 flume tiles (evaporation 1.5 water a flume tile a day) | Evaporation units and the thin-film rate come from constants, not a run | WaterLab: tap into a 16-tile ground flume in drought; read depth at the last tile after 2 days |
| Rested bonus and the 2.0 walking clamp | The multiplicative form is our code; the clamp's effect is inferred | Spawn Inkpaws at wellbeing 20 and 80 with bells 12 and 16; log `MovementSpeed` and `WorkingSpeed` multipliers and planks a builder places per day |

<!-- Generated by tools/sim/run.py sheet (tools/sim/out/sheet.md). Edit tools/sim/pandasim/stats.py, not this section. -->

## Proposed stat sheet (first pass)

Basis: **M** derived from the model (question in brackets), **V** copied from the vanilla analogue in `basis_template`, **G** a guess to tune in play. Re-themed buildings not listed keep their Folktails analogue with Plank -> PandabornPole and TreatedPlank -> PandabornCuredPole.

### Colonists

| stat | spec | Inkpaw | Ringtail | Folktail | basis |
|---|---|---|---|---|---|
| BaseWalkingSpeed (tiles/s) | WalkerSpeedManagerSpec | 2.7 | 2.7 | 2.7 | V |
| BaseSlowedSpeed (tiles/s) | WalkerSpeedManagerSpec | 1.35 | 2.7 | 1.35 | V (Inkpaw) · design (Ringtail: no slowing when loaded) |
| BaseLiftingCapacity | GoodCarrierSpec | 18 | 14 | 14 | M (q1: 3 logs and 6 poles a trip; q5: a Ringtail at 14 equals an Inkpaw builder at 12/12) |
| Rested bonus, WorkingSpeed and MovementSpeed | code (decorator) | +33% at <=12 h, linear to 0 at 16 h, by the bell | same curve, by the Ringtail shift (24 - bell) | - | M (q2) |
| Working hours | new-game slider | dawn to the bell; starts at 16 | bell to dawn | 16 | design · M (q2, q5) |
| Life (days at wellbeing < 7) | LifeService (global) | 50 | 50 | 50 | V · M (q6: no change needed) |
| Childhood (days at wellbeing < 5) | LifeService (global) | 6 | 6 | 6 | V |
| Hunger, Thirst, Sleep | Need.Beaver.* | vanilla | vanilla | vanilla | V |
| Births | ProcreationHouseSpec / nursery | 0.1875 per den entry (vanilla) | Moon Loft: 0.1875 per entry while Ringtail jobs > Ringtail adults + kits | 0.1875 | V · M (q6) |

Rested bonus: +33% at 12 working hours or fewer, falling linearly to 0 at 16; applies to WorkingSpeed, MovementSpeed; multiplies the colonist's whole multiplier (code: delta = bonus x current multiplier).

### Plants

| id | kind | basis | planter | zone | plant h | grow d | harvest | harvest h | dry d | water | spread | basis of numbers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PandabornShootBamboo | crop | Carrot | Farmstead (Farmhouse group) | moist | 0.2 | 3 | PandabornBambooShoots x2 | 1.0 | 5 | 0/0, DaysToDie 2 | 0 | GrowthTimeInDays: M q1; Yield: M q1; DaysToDieDry: M q1/q4; PlantTimeInHours: V; RemovalTimeInHours: G; Water: V |
| PandabornCabbage | crop | Carrot | Farmstead | moist | 0.2 | 5 | PandabornCabbage x3 | 1.2 | 7 | 0/0, DaysToDie 2 | 0 | GrowthTimeInDays: M q3; Yield: M q3; DaysToDieDry: M q1; PlantTimeInHours: V; RemovalTimeInHours: V |
| PandabornTimberBamboo | tree | Birch | Forester | moist | 0.5 | 5 | cut: PandabornPole x2 (CuttableSpec, RemoveOnCut false like trees); gather: PandabornBambooMushrooms x2 every 3 d (pick 0.5 h) | 1.5 | 7 | 0/0, DaysToDie 8 | 0.03 | GrowthTimeInDays: M q1; Yield: M q1/q8; DaysToDieDry: M q1; PlantTimeInHours: V; RemovalTimeInHours: M q8; Mushrooms: G; ReproductionChance: V |
| PandabornRice | crop | Cattail | Paddy House (aquatic group) | flooded | 0.2 | 8 | PandabornRice x3 | 1.2 | 1 | 1/1, DaysToDie 1.5 | 0 | GrowthTimeInDays: V (Cattail); Yield: V; Water: M q4 |
| PandabornTeaBush | bush (arid) | Blueberry | Farmstead (dry ground) | dry | 0.4 | 6 | gather: PandabornTeaLeaves x3 every 3 d | 0.6 | - | arid: dies 2 d after its soil turns moist | 0 | Yield: M q4; GrowthTimeInDays: G; PlantTimeInHours: V; Water: design |
| PandabornSichuanPepper | crop (arid) | Sunflower | Farmstead (dry ground) | dry | 0.2 | 5 | PandabornSichuanPepper x2 | 1.2 | - | arid: dies 2 d after its soil turns moist | 0 | Yield: M q3; GrowthTimeInDays: V (Sunflower) |
| PandabornPersimmonTree | tree | ChestnutTree | Forester | moist | 0.75 | 14 | gather: PandabornPersimmons x3 every 6 d (pick 1.0 h); cut: Log x3 | 1.2 | 10 | 0/0, DaysToDie 10 | 0.01 | all: V (Chestnut) with growth M q3 |

### Goods

| id | type | weight | consumption effects | dish wellbeing | basis |
|---|---|---|---|---|---|
| PandabornBambooShoots | Box | 1 | Hunger 0.3 | 0 | V (Berries): the raw staple carries no dish need |
| PandabornCabbage | Box | 1 | Hunger 0.3, PandabornCabbage 0.2 | 1 | V (Carrot) |
| PandabornPersimmons | Box | 1 | Hunger 0.3, PandabornPersimmons 0.2 | 1 | V (Carrot) |
| PandabornBambooMushrooms | Box | 1 | Hunger 0.3, PandabornBambooMushrooms 0.2 | 1 | V |
| PandabornSteamedShoots | Box | 1 | Hunger 0.3, PandabornSteamedShoots 0.2 | 1 | M q3 |
| PandabornPickles | Box | 1 | Hunger 0.3, PandabornPickles 0.2 | 2 | V (Grilled Potato) |
| PandabornSteamedRice | Box | 1 | Hunger 0.3, PandabornSteamedRice 0.2 | 2 | V (Bread) |
| PandabornSweetRiceBalls | Box | 1 | Hunger 0.3, PandabornSweetRiceBalls 0.2 | 2 | V (Cattail Cracker) |
| PandabornHotPot | Box | 1 | Hunger 0.3, PandabornHotPot 0.2 | 3 | V (Maple Pastry) |
| PandabornBambooSeedCakes | Box | 1 | Hunger 0.3, PandabornBambooSeedCakes 0.2 | 3 | M q7 |
| PandabornTea | Liquid | 2 | Thirst 0.2, PandabornTea 0.3 | 2 | M q4 (Tea need non-wastable: about 2 cups a day) |
| PandabornRice | Box | 1 | - | 0 | V (Wheat) |
| PandabornRiceFlour | Box | 2 | - | 0 | V (Wheat Flour) |
| PandabornSichuanPepper | Box | 1 | - | 0 | M q3: never edible |
| PandabornTeaLeaves | Box | 1 | - | 0 | V |
| PandabornBambooSeed | Box | 1 | - | 0 | M q7 |
| PandabornPole | Pileable | 3 | - | 0 | V (Plank): keeps the rename option open; lift 18 makes it light |
| PandabornCuredPole | Pileable | 4 | - | 0 | V (Treated Plank) |
| PandabornPaperLantern | Box | 1 | - | 0 | G |

### Recipes

| id | building | cycle h | ingredients | products | cycles capacity | fuel | power | basis |
|---|---|---|---|---|---|---|---|---|
| PandabornSteamedShoots | Steamer | 0.5 | PandabornBambooShoots 1 | PandabornSteamedShoots 2 | 30 | Log, 1 per 10 cycles | 0 | M q1/q3 (ratio) · V (Grill: fuel, buffer) |
| PandabornSteamedRice | Steamer | 1.0 | PandabornRice 1 | PandabornSteamedRice 4 | 30 | Log, 1 per 10 cycles | 0 | M q3 · V (Bread) |
| PandabornPickles | Pickle Yard | 1.0 | PandabornCabbage 1 | PandabornPickles 3 | 20 |  | 0 | M q3 (one cabbage makes several) |
| PandabornRiceFlour | Trip-Hammer Mill | 0.5 | PandabornRice 1 | PandabornRiceFlour 1 | 20 |  | flowing water (own wheel) | V (Gristmill) |
| PandabornSweetRiceBalls | Kitchen | 1.0 | PandabornRiceFlour 1, PandabornPersimmons 1 | PandabornSweetRiceBalls 5 | 20 | Log, 1 per 10 cycles | 0 | V (Maple Pastry shape) · M q3 |
| PandabornBambooSeedCakes | Kitchen | 1.5 | PandabornBambooSeed 1, PandabornRiceFlour 1 | PandabornBambooSeedCakes 4 | 20 | Log, 1 per 10 cycles | 0 | M q7 |
| PandabornHotPot | Hot Pot Hall | 1.5 | PandabornCabbage 1, PandabornSichuanPepper 1, PandabornBambooMushrooms 1 | PandabornHotPot 8 | 15 | Log, 1 per 10 cycles | 0 | M q3 |
| PandabornTea | Tea Roastery | 0.75 | PandabornTeaLeaves 1, Water 1 | PandabornTea 3 | 20 |  | 0 | design (3 cups per water) · M q4 |
| Paper (from poles) | Paper Mill | 1.56 | PandabornPole 1 | Paper 2 | 10 |  | 80 | V (Paper, pole for log) |
| PandabornPaperLantern | Lantern Workshop | 1.5 | Paper 2, PandabornPole 1 | PandabornPaperLantern 2 | 10 |  | 0 | M q7 (Small Festival in cycle 2) |
| PandabornCuredPole | Smoke Kiln | 3.0 | PandabornPole 1 | PandabornCuredPole 1 | 10 | Log, 1 per 4 cycles | 0 | V (Treated Plank: 3 h) · M q8 (log smoke instead of resin and 250 hp) |
| Gear | Gear Workshop | 3.0 | PandabornPole 1 | Gear 1 | 10 |  | 120 | V |
| Water | Water Pump | 0.33 | free | Water 1 | 15 |  | 0 | V |
| PandabornDewWater | Dew Collector | 12.0 | free | Water 1 | 4 |  | 0 | M q4: 2 a day; DewLimiter DroughtEfficiency 0.33, and efficiency / (collectors within 6 tiles) |
| PandabornCisternTap | Cistern Tap | 1.0 | Water 1 | 0.2 m3 into the flume 1 | 5 |  | 0 | V (Discharge: 3 Water/h) · M q4 (1 Water/h keeps a 10-tile strip) |
| PandabornWoodenOx | Ox Workshop | 72.0 | PandabornCuredPole 10, Gear 15, MetalBlock 2 | Wooden Ox 1 | 1 |  | 250 | M q8 (vanilla bot parts, one building) |
| SciencePointsStarTower | Star Tower | 4.0 | free | Science 12 | 1 |  | 0 | V (Observatory, 4 workers, no power) · M q5 |

### Needs (new)

| id | group | daily | wellbeing | importance | wastable | satisfied by | rhythm | basis |
|---|---|---|---|---|---|---|---|---|
| PandabornNap | Fun | -0.6 | 2 | 1.2 | False | Hammock (1 seat), Nap Platform (6 seats): +0.6/h | daily: one 1-hour visit | M q2 |
| PandabornTea | Nutrition | -0.6 | 2 | 1.0 | False | PandabornTea +0.3 a cup (about 2 a day) | daily, on ordinary drinking trips | M q4 |
| PandabornTeahouse | SocialLife | -0.15 | 2 | 1.0 | False | Teahouse +0.6/h, 12 seats | every 3-4 days | V (Domed Garden) · M q2 capacity |
| PandabornPlay | Fun | -0.2 | 2 | 1.0 | False | Slide and Swing +0.6/h, 8 seats | every 3 days | V (Lido) · M |
| PandabornCubWatching | SocialLife | -0.2 | 3 | 1.0 | False | Panda Kindergarten +0.6/h, 12 seats | every 3 days | V (Agora) · M |
| PandabornSoak | Fun | -0.2 | 3 | 1.0 | False | Hot Spring Bath +0.6/h, 8 seats (+WetFur) | every 3 days | V (Mud Pit) · M |
| PandabornContemplation | Fun | -0.12 | 2 | 1.0 | False | Ink Studio +0.6/h, 4 seats | weekly | V (Contemplation Spot) |
| PandabornPerformance | Fun | -0.12 | 5 | 1.0 | False | Opera Stage +0.6/h, 20 seats, while performers work | weekly | V (Dance Hall) |
| Pandaborn<Dish> (nine) | Nutrition | -0.05 | see goods | 1.0 | True | +0.2 a unit | a bite every 4 days | V (Need.Beaver.Bread) |
| PandabornFestive | Boosts | -0.05 | 4 | 1.0 | True | A Lantern Festival sets it to 1 (Grand: and +1 wb) | 20 days, most of a cycle | M q7 |
| PandabornMemorialArch / GreatSittingPanda / SkyLantern | Awe | -0.3 | 6 / 12 / 10 | 1.0 | True | ranged 0.1/h (wonder 10/h) | 3 h a day in range | V (Awe) · M q8 |

Wellbeing ceiling by group: Inkpaws: Basic 5, Nutrition 18, Social 6, Fun 14, Aesthetics 10, Awe 28, Boosts 4 = 85; Folktails: Basic 5, Nutrition 15, Social 13, Fun 12, Aesthetics 9, Awe 30, Boosts 0 = 84


### Buildings

| id | basis | who | cost | science | workers max (default) | recipes | capacity / notes | basis of numbers |
|---|---|---|---|---|---|---|---|---|
| PandabornVillageHall | DistrictCenter.Folktails | I | free | 0 | 4 (2) | - | builders; 20 storage | V |
| BuildersHut | BuildersHut.Folktails | I | Log 20, PandabornPole 10 | 100 | 4 (4) | - |  | V |
| HaulingPost | HaulingPost.Folktails | I | Log 20, PandabornPole 10 | 0 | 10 (5) | - | CarryingCapacity +1 | V |
| DistrictCrossing | DistrictCrossing.Folktails | I | Log 30, PandabornPole 15 | 600 | 10 (4) | - |  | V |
| PandabornFestivalSquare | new | - | Log 30, PandabornPole 30, Paper 10 | 300 | 0 | - | holds 40 lanterns, 60 dishes, 20 fireworks | M q7 (reachable in cycle 2) |
| PandabornDen | Lodge.Folktails | - | Log 12 | 0 | - | - | 3 (2 adults, 1 child) | V |
| PandabornCourtyardHouse | DoubleLodge.Folktails | - | Log 20 | 150 | - | - | 6 (4, 2) | V |
| PandabornTerraceHouse | TripleLodge.Folktails | - | Log 25, PandabornPole 10 | 250 | - | - | 9 (6, 3), stackable | V · M (poles for the stackable frame) |
| PandabornMoonLoft | new (Lodge) | - | Log 10, PandabornPole 10 | 200 | - | - | 4 (3 adults, 1 kit slot); a kit is born only while open Ringtail jobs > Ringtail adults + kits; the first loft brings 3 adults + 1 kit | M q5/q6 |
| GathererFlag | GathererFlag.Folktails | I | free | 0 | 1 | - | 20; berries, persimmons, mushrooms | V |
| PandabornFarmstead | EfficientFarmHouse.Folktails | I | Log 25 | 0 | 3 | - | 50; shoot bamboo, cabbage; tea and pepper on dry ground | V |
| PandabornSteamer | Grill.Folktails | I | Log 20, PandabornPole 5 | 40 | 1 | PandabornSteamedShoots, PandabornSteamedRice |  | M q1/q3 |
| PandabornPickleYard | new | I | Log 20, PandabornPole 15 | 120 | 1 | PandabornPickles |  | M q3 |
| PandabornPaddyHouse | AquaticFarmhouse.Folktails | I | Log 30, PandabornPole 10 | 150 | 2 | - | 50; rice | V |
| PandabornTeaRoastery | new | I | Log 15, PandabornPole 20 | 250 | 1 | PandabornTea |  | M q4 |
| PandabornTripHammerMill | Gristmill.Folktails | I | Log 30, PandabornPole 20, Gear 10 | 200 | 1 | PandabornRiceFlour | runs on flowing water at its wheel, no shafts | V · G (cheaper: no power plant) |
| PandabornKitchen | Bakery.Folktails | I | Log 15, PandabornPole 15, Gear 10 | 300 | 1 | PandabornSweetRiceBalls, PandabornBambooSeedCakes |  | V |
| PandabornHotPotHall | new | I | Log 40, PandabornPole 40, Gear 20 | 800 | 1 | PandabornHotPot |  | M q3 |
| LumberjackFlag | LumberjackFlag.Folktails | I | free | 0 | 1 | - |  | V |
| Forester | Forester.Folktails | I | Log 12 | 0 | 1 | - |  | M q1 (log-only: built before the first pole) |
| GearWorkshop | GearWorkshop.Folktails | I | Log 15, PandabornPole 25 | 100 | 1 | Gear |  | V |
| PaperMill | PaperMill.Folktails | I | Log 40, PandabornPole 40, Gear 15 | 250 | 1 | Paper (from poles) |  | V |
| PandabornLanternWorkshop | new | I | Log 10, PandabornPole 20 | 200 | 1 | PandabornPaperLantern |  | M q7 |
| PandabornSmokeKiln | WoodWorkshop.Folktails | I | Log 20, PandabornPole 40, Gear 20 | 600 | 1 | PandabornCuredPole |  | M q8 (no power, so cheaper than the Wood Workshop) |
| ExplosivesFactory | ExplosivesFactory.Folktails | I | PandabornPole 30, Gear 30, MetalBlock 30 | 400 | 1 | - |  | V |
| ScavengerFlag | ScavengerFlag.Folktails | I | free | 250 | 1 | - |  | V |
| Smelter | Smelter.Folktails | I | PandabornPole 50, Gear 20, ScrapMetal 30 | 300 | 1 | - |  | V |
| Mine | Mine.Folktails | I | Log 250, Gear 350, PandabornCuredPole 200 | 4000 | 10 | - |  | V |
| WaterPump | WaterPump.Folktails | I | Log 12 | 0 | 1 | Water |  | V |
| PandabornCisternSmall | SmallTank.Folktails | - | Log 15 | 0 | - | - | 40 | M q4 |
| PandabornCisternMedium | MediumTank.Folktails | - | Log 20, PandabornPole 30 | 100 | - | - | 300 | M q4 (no gears: reachable before the first drought) |
| PandabornCisternLarge | LargeTank.Folktails | - | PandabornPole 80, Gear 40, MetalBlock 20 | 500 | - | - | 1200 | V · M |
| PandabornFlume | new (ThrottlingValve cell) | - | PandabornPole 2 | 60 | - | - | per tile | G |
| PandabornFlumeCorner | new | - | PandabornPole 3 | 60 | - | - |  | G |
| PandabornFlumeDrop | new | - | PandabornPole 3 | 60 | - | - |  | G |
| PandabornFlumeBridge | new | - | PandabornPole 4, Log 1 | 120 | - | - | per tile | G |
| PandabornFlumeGate | FillValve.Folktails | - | Log 6, PandabornPole 6 | 80 | - | - | sets flow; shuts at contamination >= 0.05 | G · design |
| PandabornScoopWheel | new | - | Log 20, PandabornPole 30, Gear 5 | 250 | - | - | lifts 1 block; needs flow >= 0.15 | G (prototype measures) |
| PandabornPaddySpout | FillValve.Folktails | - | PandabornPole 6 | 150 | - | - | holds 0.3 deep | G |
| PandabornCisternTap | Discharge.Folktails | - | Log 8, PandabornPole 8 | 250 | - | PandabornCisternTap | 1 Water an hour into a flume; no workers | M q4 |
| PandabornDewCollector | new | - | PandabornPole 15, Paper 4 | 300 | - | PandabornDewWater | buffer 4; footprint 2x2; 2 Water a day, 2/3 in drought, shared with collectors within 6 tiles | M q4 |
| PandabornTreadwheelLift | new | I | PandabornPole 30, Gear 10 | 300 | 1 | - | lifts 1 block | G |
| PandabornDryStoneWall | Levee.Folktails | - | Log 4, Dirt 2 | 120 | - | - | blocks moisture like an impermeable floor, sideways | G |
| PandabornBambooWaterWheel | WaterWheel.Folktails | - | Log 30, PandabornPole 15 | 0 | - | - | 270 hp x flow | V |
| PowerWheel | PowerWheel.Folktails | I | Log 20 | 0 | 1 | - | 50 hp | V |
| PandabornKiteWindmill | WindTurbine.Folktails | - | Log 20, PandabornPole 20 | 120 | - | - | 150 hp | V |
| PandabornLargeKiteWindmill | LargeWindTurbine.Folktails | - | PandabornPole 40, Gear 20, Paper 30 | 1400 | - | - | 300 hp | V |
| Inventor | Inventor.Folktails | I | Log 12 | 0 | 1 | SciencePoints |  | V |
| PandabornStarTower | Observatory.Folktails | R | PandabornPole 60, Gear 30, Paper 10 | 1000 | 4 | SciencePointsStarTower | no power (stars, not machines) | V · M q5 |
| PandabornOxWorkshop | BotAssembler.Folktails | I | PandabornPole 100, Gear 50, MetalBlock 40 | 1000 | 2 | PandabornWoodenOx | 250 hp; all parts in one building | M q8 |
| PandabornNightBuildersPost | BuildersHut.Folktails | R | Log 15, PandabornPole 10 | 0 | 4 (4) | - | unlocked by the first Moon Loft | M q5 |
| PandabornNightCourierPost | HaulingPost.Folktails | R | Log 20, PandabornPole 10 | 150 | 6 (3) | - | CarryingCapacity +1 | M q5 |
| PandabornNightForagersPost | GathererFlag.Folktails | R | PandabornPole 10 | 100 | 2 (2) | - | 30; mushrooms first | M q5 |
| PandabornOperaStage | DanceHall.Folktails | R | Log 100, PandabornCuredPole 40, MetalBlock 20 | 1200 | 2 (2) | - | 20 seats; open while performers work | V · M q5 |
| Campfire | Campfire.Folktails | - | Log 15 | 0 | - | - | 5 seats | V |
| PandabornHammock | Hammock.Folktails | - | Log 4 | 0 | - | - | 1 seat, Nap +0.6/h | M q2 (log-only: buildable on day 1) |
| PandabornNapPlatform | RooftopTerrace.Folktails | - | Log 10, PandabornPole 15 | 100 | - | - | 6 seats, Nap +0.6/h, stackable | M q2 |
| PandabornTeahouse | DomedGarden.Folktails | - | Log 25, PandabornPole 25 | 150 | - | - | 12 seats; stocks 30 Tea | M q2/q4 |
| PandabornSlideAndSwing | Lido.Folktails | - | Log 25, PandabornPole 20 | 250 | - | - | 8 seats | V |
| PandabornKindergarten | Agora.Folktails | - | Log 60, PandabornPole 40 | 400 | - | - | 12 adult seats + cubs' play | V · M |
| PandabornInkStudio | ContemplationSpot.Folktails | - | Log 10, Paper 10 | 200 | - | - | 4 seats | V |
| PandabornHotSpringBath | MudPit.Folktails | - | Log 60, PandabornCuredPole 30, Dirt 20 | 1500 | - | - | 8 seats | V |
| TeethGrindstone / MedicalBed / Herbalist / Shower | vanilla | - | vanilla | vanilla | vanilla | - |  | V |
| PandabornMemorialArch | BrazierOfBonding.Folktails | - | Log 250, PandabornPole 800 | 3000 | - | - | Awe +6, radius 10 | M q8 (labour of Farmer Monument + Brazier) |
| PandabornGreatSittingPanda | HallOfAbundance.Folktails | - | PandabornPole 1400, PandabornCuredPole 700, MetalBlock 650 | 15000 | - | - | Awe +12, radius 30 | M q8 (labour of Fountain + Hall) |
| PandabornSkyLantern | EarthRecultivator.Folktails | - | Gear 2400, PandabornCuredPole 2400, MetalBlock 1800, Paper 500 | 20000 | 10 (crew) | - | build 15000 h, 40 builders; fill 500 Paper Lanterns + 500 Tea | V · M q8 |

### Events and oxen

**Great Flowering.** first_cycle: 6; every_cycles: 5-7 (alternating shoot, timber; first is shoot bamboo); announce: at the start of the cycle before: buds show, about 15-20 days; never_in: drought, badtide; when: the first day of a temperate season; plants die over 2 days; seed: each flowering plant drops 3 PandabornBambooSeed when cleared (gathered or cut); replant: that bamboo cannot be replanted until the next temperate season (code: planting check); reserve: shoot year: ~14 food per colonist (40 colonists: 560); timber year: ~5 poles per colonist; setting: off / rare (every 9-11 cycles) / normal; basis: M q7

**Lantern Festival.** small: 40 Paper Lanterns + 20 each of three cooked dishes; grand: adds 20 Fireworks; cost: everyone off duty from dawn to the next dawn; festive: PandabornFestive (+4) set to 1, decay 0.05: 20 days; Grand adds 1 more wellbeing while it lasts; once_per_cycle: True; basis: M q7

**Wooden Ox.** walk_tiles_s: 1.8; lift: 40; life_days: 90; hours: 24; needs: none (bot tier 0: work x1.65, walk x1.3); cost: 10 Cured Pole + 15 Gear + 2 Metal Block, 72 h at the Ox Workshop; basis: M q8

