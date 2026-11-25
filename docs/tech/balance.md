# Balance

Status: second pass, 2026-11-25, against the build generated that day (catalogue at `804fff1`). Lane: balance.
This page proposes; the coordinator decides; the catalogue lane applies. Nothing here has been changed in
`catalogue/`.

The second pass is the part above the line "First pass". It reads the numbers the game reads
([`tools/balance`](../../tools/balance/README.md): vanilla blueprints plus the generated Inkpaws build) and is
calibrated against the scripted playtests. The first pass (2026-11-14, `tools/sim`) is kept below, because other
pages cite its question numbers; where the two disagree, the second pass is right and
[Corrections to the first pass](#corrections-to-the-first-pass) says why.

No game was run for this pass. Every table is in `tools/balance/out/*.md` and is rebuilt by
`E:\PandabornDev\tools\venv\Scripts\python.exe -I tools\balance\run.py all`.

## Summary

1. **On Normal, cycles 1 to 3 cannot go wrong for an Inkpaws village, and one cause is an accident.** The same
   scripted "careless" colony (no water storage, one crop, three homes) lost 10 of 39 Folktails to thirst and hunger
   over three runs and no Inkpaw over two. The accident is the shelf rule: it turns the Water Pump into a
   146-water tank (vanilla 15), five days of drinking for the starting thirteen, for 12 logs. The rest is design
   (crops that sit out a short drought) and is fine.
2. **The bell is fair but 12 hours is not its sweet spot.** Work is flat from 12 to 16 hours with a 2% bulge at 13
   to 15, at every wellbeing level; the walking cap is never reached. All rituals fit in any day of 15 hours or less;
   a 16-hour day loses only the nap. Twelve hours becomes the best day only when Ringtails are there to use the
   night. A flat curve removes the bulge.
3. **Ringtails are not the equals the design says they are.** They get no rested bonus, so at twelve and twelve a
   Ringtail builder does 0.75 of an Inkpaw's work and a courier 0.75 to 0.87, while eating the same. The first pass
   assumed they shared the bonus. This needs a decision (three options below).
4. **Shelves do not starve construction.** A worker without haulers fetches one load at a time whatever the shelf
   size (game code), so nothing is hoarded before a Hauling Post or Courier Post exists; after that the one-time
   extra is about 37 logs early and 80 logs and 55 poles in a full mid-game town. Keep 48 hours for workshops; take
   pumps and taps out of the rule.
5. **The first-two-hours table has two beats the numbers do not allow.** A scoop wheel and flume by day 5 to 8
   needs 290 science and lands on day 14 to 15 with two inventors; tea at the Teahouse by day 3 to 5 is impossible
   before day 12 (bushes) and realistically day 19 (science), and the Teahouse is stocked only by haulers.
6. **Mid game, Inkpaws hold 7 to 14 more wellbeing than Folktails at equal science** (45 against 32 at 4,000
   science), and the ceiling is 94 against 84. Four one-point trims bring that to 3 to 10 and 90.
7. **Late science is three times as dear in labour**: the Star Tower is hidden until its module exists, so the last
   38,000 science is 826 inventor-days against 275 Folktails Observatory worker-days.
8. **The festival pays until about wellbeing 50** (return 2.0 at wellbeing 10, 1.0 at 50, 0.45 at 60) and its first
   three calls unlock +5 wellbeing of decorations. After that it is a pleasure that costs most of a working day a
   cycle.
9. **The Wooden Ox outclasses a fully boosted Folktails bot** at hauling (517 poles a day against 465) with no
   upkeep and a cheaper build. Its recipe should cost about twice what it does.
10. **Hard breaks where vanilla Hard breaks: water in the first week.** Both scripted Hard colonies died of thirst,
    the Inkpaws one drought later. Nothing Inkpaw-specific fails on Hard that the design does not already name.

## How far to trust this

| Mark | Meaning |
|---|---|
| **measured** | Read from a finished game run (run named) |
| **data** | Arithmetic on blueprint values, no behaviour assumed |
| **model** | Arithmetic that also assumes behaviour (distances, time off duty, a player's choices) |
| **thin** | A judgement with little behind it; a run is named that would settle it |

### What the runs can and cannot tell us

The playtest lane was stopped before it reported. Its runs are in `E:\PandabornDev\build\test\pt-*`.

| Runs | Verdict | Good for | Not good for |
|---|---|---|---|
| `pt-ft-base-m2`, `-m3`, `-m4`; `pt-ink-std-m1`, `-m3` (Meander, Normal, 41 days) | Trustworthy as far as they go | The first six days hour by hour; consumption; pump, inventor and lumberjack rates; first-crop days; stores before a drought; wellbeing of a small village; whether a drought hurts | Growth, the mid game, building pace after day 6: the driver ran out of trees it could mark (logs fell from 33 a day to 0 to 8), homes stalled, nobody was born. "13 to 18 colonists in 41 days" is the driver, not the faction |
| `pt-ft-care-m1..3`, `pt-ink-care-m1`, `-m3` (careless, 31 days) | Trustworthy for the question they ask | Does a careless start survive the first drought | Anything after it |
| `pt-ft-hard-m1`, `pt-ink-hard-m1`, `-m2` (Hard) | Trustworthy as worst cases | Where an unprepared Hard start dies and of what; plant deaths in a five-day drought | Whether a prepared player survives (the plan does not stock up) |
| `pt-ft-base-m1` | Discard | | Three colonists died homeless; the mill step never ran |
| `pt-ft-base-1`, `-2`, `pt-ftb-dev1..5` (Plains) | Discard | | 0 adults by day 8 to 11: driver development |
| `pt-ft-base-m5`, `pt-ink-std-1`, `-m2`, `-m4`, `pt-ink-care-m2` | Discard | | No telemetry |
| `rt2-shelvesA/B/C`, `rt2-soak`, `rt3_breed3` | Trustworthy, small | Couriers and shelf size, Ringtail loads (2 logs a trip), the kit valve | Any rate per 100 colonists: one small layout each |
| `water-*` | Trustworthy, measured by the water lane | Flow, moisture reach, tap and wheel rates (docs/tech/water.md) | A drought with a colony drinking |
| `events-*` | Mechanism only | That the festival and Flowering run | Their balance: no colony economy in them |

Two more limits on the faction-against-faction runs. The driver cannot lay power shafts, so the Folktails colonies
never made a plank and built nothing that needs one, while the Inkpaws cut poles from bamboo (244 piled up unused
by day 35, with logs at zero): the comparison is fair for water, food and the first drought, and unfair for
anything built after the first week. And every colony stayed on a 16-hour day, so the bell was never exercised.
The playtest lane's own charts of the careless and Hard pairs are in `docs/tech/playtest/`.

No run had a Teahouse with tea in it, a 12-hour day with a real economy, a festival's effect on output, an ox, or
a colony above 20. Everything said about those is **model**.

## Calibration

| Quantity | Measured in game | Model |
|---|---|---|
| Logs a lumberjack a day (pine, wellbeing under 5) | 16.9 | 16.2 |
| Water a pump worker makes a day | 40.2 | 39.4 (the recipe says 46; pumps run at 85%) |
| Science an inventor makes a day | 16.3 | 15.3 |
| Food a colonist eats a day | 2.57 | 2.57 (set from this; the rule of thumb says 2.67) |
| Water a colonist drinks a day | 2.10 | 2.11 (set from this) |
| Shoot bamboo alive after a five-day drought | 45% (52 of 116 plants, two runs) | 50% |
| Crop tiles one farmer keeps harvested | 35 (three farmers saturated on 105 tiles) | 29.5 |
| First crop | Shoots day 5 to 6, carrots day 6 to 7 | One day apart (growth 3 against 4) |

A Folktails colony in the model reproduces the vanilla pace to within 6% on every rate we could measure. The model
was **not** calibrated on walking distances, on time off duty, or on anything in the mid game.

## Q1. Is the faction too easy in cycles 1 to 3?

**Yes on Normal, and the size of it is measured.** Same script, same map:

| Scenario | Colonists | Water at the first drought | Food at the first drought | Thirsty colonist-days | Died of thirst or hunger |
|---|---|---|---|---|---|
| Folktails standard (3 runs) | 13 to 11-12 | 41 to 51 | 99 to 106 | 4 to 29 | 0 |
| Inkpaws standard (2 runs) | 13 to 7-18 | 191 to 193 | 159 to 160 | 0 | 0 |
| Folktails careless (3 runs) | 13 to 0-9 | 0 | 38 to 92 | 37 to 102 | 9, 1, 0 |
| Inkpaws careless (2 runs) | 13 to 8-9 | 114 to 120 | 106 | 0 | 0 |

Four causes, largest first.

**1. The pump is a tank (data, measured).** `rules.toml [shelves] workshop_hours = 48` sizes a recipe's store as 48
hours of work. The Water recipe has no input, so the rule only inflates its output: 146 water in one pump (vanilla
15), 720 in a Large Water Pump (vanilla 60). In `pt-ink-std-m3` the pump held 108 of the village's 148 water. A
Small Cistern (40 water, 15 logs) is pointless beside it, and the first drought's lesson, "build a cistern", is
never taught. In vanilla the 15-unit pump is also the careless player's trap: the Folktails careless colonies were
thirsty from day 5 in fair weather, because thirteen beavers drink 27 in an evening. A one-day store (49) keeps
Inkpaws out of that trap and still leaves a three-day drought to prepare for.

**2. Staples that sit out a drought, at high yield, with no infrastructure (data).**

| Food | Dish wellbeing | Food per tile-day | Work hours per food | Science | Needs | Dry days |
|---|---|---|---|---|---|---|
| Folktails carrot | 1 | 0.75 | 0.58 | 0 | - | 2 |
| Folktails grilled potato | 2 | 0.67 | 0.57 | 0 | fuel | 1 |
| Folktails bread | 2 | 1.50 | 0.42 | 340 | fuel, power | 0.5 |
| Bamboo shoots | 0 | 0.67 | 0.77 | 0 | - | 5 |
| Cabbage | 1 | 0.60 | 0.58 | 0 | - | 7 |
| Steamed shoots | 2 | 1.33 | 0.64 | 40 | fuel | 5 |
| Pickles | 2 | 1.80 | 0.53 | 120 | - | 7 |
| Steamed rice | 3 | 1.50 | 0.40 | 190 | fuel | 1 |
| Sweet rice balls | 2 | 1.07 | 0.51 | 650 | fuel | 1 |
| Hot pot | 4 | 1.71 | 0.39 | 800 | fuel | 7 |

The review's figures hold: 1.33 and 1.8 against 0.75 and 1.5. But the edge is land, timing and drought, **not
labour**: an Inkpaw food costs 0.4 to 0.8 work hours, a Folktails one 0.4 to 0.6. Land was not the limit in any
run (60 shoot and 45 cabbage tiles filled every store; farmers, not tiles, were saturated). So cutting yields would
change little in cycles 1 to 3. Share of unwatered plants alive after the n-th drought (model, calibrated above):

| Mode | Drought | Days | Carrot (2) | Shoot bamboo (5) | Cabbage (7) | Timber bamboo (10) |
|---|---|---|---|---|---|---|
| Normal | 1 | 2-3 | 20% | 100% | 100% | 100% |
| Normal | 2 | 3-5 | 0% | 99% | 100% | 100% |
| Normal | 3 | 3-6 | 0% | 74% | 100% | 100% |
| Normal | 4 | 4-7 | 0% | 41% | 96% | 100% |
| Normal | 5 | 4-8 | 0% | 18% | 75% | 100% |
| Normal | 6+ | 5-9 | 0% | 6% | 50% | 100% |

Food stops being free in cycle 3 (shoots) and cycle 5 (cabbage). That is the design's choice ("the first drought
was the likeliest place for a new player to quit") and it tapers at a sensible pace. Leave the dry days alone:
cabbage at 6 would cost the Hard start more than it adds to Normal (Hard first drought 92% instead of 100%, second
50% instead of 75%). Timber bamboo never dies of drought on Normal, where no drought exceeds 9 days.

**3. Bigger harvest stores (data, measured).** A farmhouse holds 96 (vanilla 50), a flag 32 (20). Measured food at
the first drought: 106 to 160 against 38 to 106. This is `harvest_hours = 16`, the day's harvest the night couriers
clear, and it is what the rule is for. Leave it.

**4. Poles and lift (data, model).** A pole from bamboo costs 0.41 of a plank's labour and bamboo yields 0.4 poles
a tile-day against pine's 0.17 logs. With lift 18 an Inkpaw builder moves 1.40 times a Folktails builder's units.
Neither showed in the runs, which were log-bound from day 2 (33 logs a day from two flags, both factions). Logs
cost Inkpaws what they cost beavers; that is the brake, and it holds.

**Early wellbeing is not out of line.** At no science an Inkpaws village can hold 13 and a Folktails one 12; at
1,000 science 27 against 26. The 4-log Hammock (+3) is the cheapest wellbeing in the game and the measured villages
sat at 9 to 10 against 5 to 6 on day 30, but the working-speed step from that is one tier. Leave the nap at 3.

**Recommendation.** Fix the pump (must). Leave yields, growth, cook times and dry days. Optionally bring pickles
to bread's yield (2 cabbage to 5 pickles: 1.5 a tile-day), since pickles are today the best food in the game on
land, science, fuel and drought at once (thin: static sums only).

## Q2. The bell

**Work (data, verified in game by the Bell lane at wellbeing 80).** Against the same Inkpaw on a 16-hour day:

| Day | Rested | Work, building, carrying | With a flat curve |
|---|---|---|---|
| 8 h | +33% | 0.66 | 0.66 |
| 10 h | +33% | 0.83 | 0.83 |
| 12 h | +33% | 1.00 | 1.00 |
| 13 h | +25% | 1.01 | 1.00 |
| 14 h | +16% | 1.02 | 1.00 |
| 15 h | +8% | 1.02 | 1.00 |
| 16 h | 0 | 1.00 | 1.00 |

Identical at wellbeing 0, 20, 50 and 80: the bonus multiplies, and the fastest possible Inkpaw walks at 2.39
against a cap of 2.66. There is **no short-day optimum** (10 hours loses 17%) and no way to keep the bonus on a
long day (the day is locked at dawn).

**Rituals (model; the time off duty is assumed, see `tools/balance/day.py`).** A colonist has 24 minus the day
minus 3.9 hours reserved for bed minus about 1.2 hours of meals. The Inkpaws' full set of rituals needs 3.8 hours
a day (nap 60 minutes, tea 40, the rest 12 to 20 each, plus walking); the Folktails' full set needs 2.6.

| Day | Leisure hours | Inkpaw rituals kept (of 23 wellbeing) | Lapses | Folktails kept (of 22) |
|---|---|---|---|---|
| 12 h | 6.9 | 23 | - | 22 |
| 14 h | 4.9 | 23 | - | 22 |
| 15 h | 3.9 | 23 | - | 22 |
| 16 h | 2.9 | 20 | Nap | 22 |
| 17 h | 1.9 | 15 | Tea, Nap | 19 |
| 18 h | 0.9 | 9 | Play, Soak, Tea, Nap | 14 |

The measured villages kept the nap on a 16-hour day with nothing else to visit, so "16 hours loses the nap" is
true only once the other attractions are built. The first pass's "16 hours keeps 2 of 8 and costs 17% of output"
was too harsh: the same budget lets Folktails keep all eleven of their attractions at 16 hours, as they do in the
real game.

**So where is the sweet spot?** Colony work per colonist with every ritual built, against Folktails on 16 hours:
12 h 1.01, 13 h 1.03, 14 h 1.03 to 1.04, 15 h 1.03, 16 h 0.97 to 0.99. Without Ringtails the best day is 13 to 15
hours by a hair, and 12 leaves three hours a day with nothing to do. With Ringtails every hour the Inkpaws give up
costs them nothing and is an hour of night work: at 30% Ringtails 12 hours is the best day (44.9 against 44.6 at
13 and 40.2 at 16).

**Degenerate optimum.** One small one: 14 hours beats 12 by 2% and keeps every ritual, because the bonus falls in
a straight line while the hours grow. A curve of `16 / hours - 1` (points at 13, 14 and 15) is flat, so the
suggestion "work a short day" is never wrong by a number. Nothing else: 16 hours with rituals ignored equals 12
hours in work and is 8 wellbeing poorer (nap 3, tea 5).

**Recommendation.** Flat curve (would improve). Tell the truth in the suggestion text: a short day costs nothing
and leaves time for tea; do not promise it is faster.

## Q3. Nap and tea

Colonists one building serves (model: seats x awake off-duty hours x 0.75, the share measured on hammocks):

| Building | Seats | Wellbeing | Minutes a colonist-day | 12-hour day | 14 | 16 |
|---|---|---|---|---|---|---|
| Hammock | 1 | 3 | 60 | 6 | 5 | 3 |
| Nap Platform | 5 | 3 (+1 rooftop) | 60 | 30 | 23 | 15 |
| Teahouse | 5 | 5 | 40 | 46 | 34 | 23 |
| Slide and Swing | 7 | 3 | 20 | 128 | 96 | 65 |
| Kindergarten | 5 | 4 | 20 | 91 | 69 | 46 |
| Ink Studio | 1 | 3 | 12 | 30 | 23 | 15 |
| Hot Spring Bath | 8 | 3 | 20 | 146 | 110 | 74 |

* **Measured:** four hammocks kept the nap of 13 to 15 colonists (three or four of them cubs with the whole day
  free) on a 16-hour day: 3 to 4 colonists a hammock, as the table says.
* "One Teahouse serves about 25" is right on a 16-hour day and modest on a 12-hour one (46). Leave the five seats.
* The Nap Platform has five seats (its catalogue note said eight; the catalogue lane is correcting the note).
  Five is enough.
* The Ink Studio has one seat: a hundred colonists need four. That is a wall of studios for a +3; give it four
  seats if its model allows (thin: not measured).

**The tea chain for 100 colonists (model, 12-hour day).** A Teahouse uses 1 tea and 0.5 water for every hour it
has anyone inside, whatever the number of guests (game code: `GoodConsumingAttraction`). Three Teahouses, 22 to 34
tea and 11 to 17 water a day, 11 to 17 tea bushes, and half to three-quarters of a worker to pick, roast and
carry. The water is 5 to 8% of what the village drinks. Against that, +5 wellbeing is worth 11% more work at
wellbeing 20, 7% at 40, 3% at 60: seven to eleven workers' worth in a hundred through the mid game. Tea is worth
its wellbeing about ten times over, so its real costs are the wait and the logistics:

* a bush bears its first leaves 9 days after planting (grow 6, then 3), so no tea before day 12;
* Roastery and Teahouse are 400 science;
* **only haulers or night couriers stock a Teahouse** (it is a good-consuming building, like the vanilla Domed
  Garden). A village with neither has a closed Teahouse. The same goes for the Hot Spring Bath's water. The
  tutorial's tea stage should say so.

`DESIGN.md` says a cup "also takes the edge off thirst". The build does not do that (the Teahouse's only effect
is Tea), and it uses water. Either is fine for balance; the sentence should go.

## Q4. Ringtails

**One Ringtail against one Inkpaw, per shift (data plus distances; wellbeing 30):**

| Bell | Ringtail | Builder, logs | Builder, poles | Courier, logs | Courier, water or food | Builder against a Folktails builder |
|---|---|---|---|---|---|---|
| 12 | as shipped: lift 14, no rested bonus | 0.75 | 0.75 | 0.75 | 0.87 | 1.08 |
| 12 | lift 16 | 0.75 | 0.90 | 0.94 | 1.00 | 1.14 |
| 12 | lift 18 | 1.07 | 1.04 | 1.12 | 1.12 | 1.52 |
| 12 | lift 14 and the rested bonus by their own night | 1.00 | 1.00 | 1.00 | 1.17 | 1.44 |
| 14 | as shipped | 0.61 | 0.61 | 0.61 | 0.71 | 0.89 |
| 16 | as shipped | 0.49 | 0.49 | 0.49 | 0.58 | 0.71 |

`DESIGN.md` (change log, lift 18 and 14): "this makes a night builder exactly as good as a day builder at twelve
and twelve". That row is the fourth one. The first pass's stat sheet gave Ringtails "the same curve, by the
Ringtail shift"; the shipped Ringtail template carries no `PandabornBellSpec` (two-peoples.md 18.1: "the rested
bonus is an Inkpaw thing"). So today a Ringtail is a quarter weaker than an Inkpaw in the only jobs it may hold,
and eats the same. Measured support for the load side: night builders carried 36 goods in 18 trips (`rt2-soak`).

Three ways to make the design's sentence true:

| Option | Change | Result at 12/12 | Cost |
|---|---|---|---|
| A (recommended) | Ringtails get the rested bonus by the length of their night | 1.00 / 1.00 / 1.00 / 1.17 | Code: Bell and Ringtails lanes. One rule for both peoples: "a twelve-hour shift is a rested shift" |
| B | Data only: Ringtail `BaseWalkingSpeed` and `BaseSlowedSpeed` 2.7 to 3.6 | 1.00 in carrying jobs, 0.75 in the building work itself (a small share) | Reverses the 2026-11-14 decision that Ringtails walk at Inkpaw speed; animation scale to retune |
| C | Data only: Ringtail lift 14 to 16 | 0.75 on logs, 0.90 to 1.00 on the rest | "Inkpaws lift more" stays true, parity does not quite arrive |

**Is a 12/12 village with Ringtails clearly better, without being mandatory?**

* **Not mandatory:** yes. Nothing a one-people village needs is a Ringtail job, and day haulers do what couriers do.
* **Clearly better early:** yes, because of how fast they come, not how well they work. The first Moon Loft adds
  two adults at once to a village of ten or twelve, and each loft raises a kit a day while night jobs are open: a
  set of three posts (4 + 6 + 2 jobs) can be filled within about ten days, against Inkpaw births that need homes
  and luck. The valve works (`rt3_breed3`: never more Ringtails than night jobs, no kits while anyone is hungry).
* **Clearly better late:** no, as shipped. Per mouth an Inkpaw hauler beats a Ringtail courier by 15 to 33%.
  With option A the two are equal and the night is free working time, which is the design.

**What couriers buy (model, and it matches the one measurement):** a workshop worker alone is at its bench 62 to
90% of the day (smelter 35%); supplied, all of it. The measured pair was Paper Mill and Pickle Yard: model 83% for
both, so +20% when supplied; measured +18% producing hours with couriers (`rt2-shelvesB` against `C`). A courier
hour frees 1.1 to 1.6 Inkpaw hours except at the Hot Pot Hall (0.8: three inputs).

**How many.** A hundred Inkpaws with about forty workshop workers need 80 to 120 courier hours a night (7 to 10
couriers), 3 to 5 more for flags, farms and pumps, 4 to 8 builders, 2 foragers: **about 20 Ringtails per 100
Inkpaws (15 to 25)**, which is two Courier Posts, one or two Builders' Posts and a Foragers' Post. Past that they
idle; the valve stops there by itself. Thin: the per-night courier hours are model only.

Posts and loft: Moon Loft 200 science (10 logs, 10 poles), Builders' Post 50, Courier Post 150, Foragers' Post
100, all free once the family arrives. Fine as they are.

## Q5. Shelves

**Does a 48-hour shelf make workshops hoard logs and poles in the first days? No (game code).** A workshop worker
produces if it can, else carries output out, else fetches **one load** of its emptiest input
(`WorkshopsTemplateModuleProvider`: Produce, EmptyOutput, FillInput). It never tops up a shelf. Only haulers do
(`FillInputHaulBehaviorProvider`, weight = one minus the fill). So before a Hauling Post or Courier Post stands,
shelf size changes nothing; `rt2-shelvesC` measured the same thing ("without Ringtails the bigger shelves are
harmless").

Once haulers exist, what the shelves can hold back (data):

| Workshop | Cycles held | Vanilla | Held at 48 h |
|---|---|---|---|
| Pole Mill | 39 | 13 | 39 logs |
| Steamer (shoots) | 96 | 30 | 16 logs of fuel |
| Hot Pot Hall, Kitchen | 32, 48 | 15, 20 | 11 and 12 logs of fuel |
| Smelter | 24 | 13 | 24 logs of fuel, 48 scrap |
| Gear Workshop | 16 | 10 | 16 poles |
| Paper Mill | 31 | 10 | 31 poles |
| Lantern Workshop | 32 | 10 | 32 poles, 64 paper |
| Smoke Kiln | 16 | 10 | 16 poles |
| **Water Pump** | **146** | 15 | output only: 146 water |
| **Cistern Tap, Discharge** | **48** | 5 | **144 water** |

One of each, kept full: 134 logs and 95 poles, against 56 and 40 under the vanilla sizes. In the first cycle (Pole
Mill and Steamer) it is 55 logs against 18: **37 logs once**, a day of two lumberjacks or three dens delayed by a
day. Not a starvation.

And 48 hours is not as long as it sounds: it is hours of work at speed 1. At wellbeing 30 on a 12-hour day a
worker goes through a 48-hour shelf in 1.4 days, so 24 hours would leave the day crew fetching again by early
afternoon and undo the measured gain (46% more produced with three-day shelves than with one-day ones).

**Recommendation.** Keep `workshop_hours = 48` for every workshop with inputs, early buildings included. Take the
two kinds the rule was never meant for out of it:

* recipes with no input (pumps, the Badwater Pump, the excavator): one day, like flags and farms;
* water poured away (Cistern Tap, Discharge): the vanilla size. A tap with a 144-water input lets haulers move 144
  water (68 colonist-days of drinking) out of the cisterns into a store nobody can drink from, the moment it is
  built.

Optional: the Pole Mill at 24 hours (20 logs), since logs are the one early good everything waits for (thin).
Input and output cannot be split in data: one `CyclesCapacity` sizes both.

## Q6. Water

**Drinking water for a drought (data):**

| Colonists | Dry days | Water | Small (40) | Medium (300) | Large (1200) |
|---|---|---|---|---|---|
| 20 | 3 / 6 / 9 | 127 / 253 / 380 | 3.2 / 6.3 / 9.5 | 0.4 / 0.8 / 1.3 | 0.1 / 0.2 / 0.3 |
| 50 | 3 / 6 / 9 | 316 / 633 / 950 | 7.9 / 15.8 / 23.7 | 1.1 / 2.1 / 3.2 | 0.3 / 0.5 / 0.8 |
| 100 | 3 / 6 / 9 | 633 / 1266 / 1899 | 15.8 / 31.6 / 47.5 | 2.1 / 4.2 / 6.3 | 0.5 / 1.1 / 1.6 |

Cisterns cost less than vanilla tanks and come sooner: Medium 20 logs and 30 poles at 100 science (vanilla: 30
planks and 20 gears, 120); Large 80 poles, 40 gears, 20 metal at 500 (80, 60, 30 at 600). That is what "cisterns
carry the village" needs, and it is why the pump must stop being a better cistern than the cisterns.

**Irrigation (measured rates, docs/tech/water.md: 0.21 m3 a day per flume tile, a band 13 tiles wide, 0.2 m3 per
Water):**

| Source | m3 a day | Flume tiles kept wet | Farm tiles kept moist |
|---|---|---|---|
| Scoop Wheel at a current of 0.30 (0.10 m3/s) | 46 | 219 | 2,850 |
| Flume Gate at its default (0.36 m3/s) | 166 | 790 | 10,300 |
| Cistern Tap, one worker (3 Water an hour of work) | 9.6 | 46 | 594 |

* **The tap's rule of thumb is right:** 100 Water for six days keeps 206 farm tiles moist (the text says about
  200). A Medium Cistern through a tap keeps 620 tiles for six days or 410 for nine; a Large one keeps 495 tiles
  through a thirty-day Hard drought. Thin in one respect: the 0.21 was measured on one strip in fair weather.
* **One Scoop Wheel waters any village** (20 logs, 30 poles, 150 science, no workers, no power; a vanilla
  Mechanical Pump lifts 2.5 times as much for 2,000 science and 500 hp). It is the faction's first pillar and it
  only works in a current, so it stops when it would matter most. Leave its rate. Its science is in Q10.
* **An unpaused tap pours 36 to 48 Water a day in any weather**, the drinking of about twenty pandas. Its text
  says it keeps a strip alive in a drought; nothing stops it in the wet. A "pour only in a drought" switch would
  be worth the code. Not a number.
* **Dew Collector:** 2 Water a day, 0.7 in a drought, for 15 poles, 4 paper and 300 science. One colonist's water
  takes 1.1 collectors in fair weather and 3.0 in a drought. Weak enough that spam is not worth it against
  cisterns (a Large Cistern covers a thirty-day drought for eight times less material). **Its text says collectors
  close together share the dew; the code has no such rule** (`DewLimiter` reads the weather only). Drop the
  sentence or write the rule.

## Q7. The Great Flowering

**The reserve depends on how much of the food is shoots (data):**

| Shoots' share of the food | Food to store per panda for the 12 days | ...if the fields are re-marked with cabbage |
|---|---|---|
| 20% | 6 | 3 |
| 35% (what the tooltip assumes) | 11 | 5 |
| 50% | 15 | 7 |
| 75% | 23 | 11 |
| 100% | 31 | 14 |

"About 11 food per panda" is right for a varied village and a third of what a shoots-only village needs. The
announcement comes a full cycle ahead, so the fix is advice, not numbers: "store about 11 food each, more if you
live on shoots, or sow cabbage". With that it is not a death sentence on Normal: the rest ends on day 9 and
shoots are back on day 12, before the cycle's drought (day 14 to 18).

**The windfall (data).** Forty colonists with a third of their food from steamed shoots grow about 27 shoot tiles:
81 seed, 324 seed cakes, three days of everyone's food or a month of the +3 dish. The food lost in the gap is
about 430. So in food the Flowering is roughly even only for villages that eat shoots raw (twice the tiles, twice
the seed); what it really pays is +3 wellbeing for four to nine weeks, and only to a village that already has
rice flour and a Kitchen (750 science of chain). Worth preparing for; not much of a windfall. Six cakes a seed
instead of four would make it one (thin).

**Timber year:** 14 days without bamboo poles. One Pole Mill worker makes 27 poles a day from logs at wellbeing 30,
supplied, so "about 5 poles per panda" plus a mill is safe. Thin: no run measured how many poles a village uses.

**Hard:** the temperate season is 5 to 8 days, so the nine-day rest always ends inside the cycle's drought, and
the sixth Hard drought lasts 8 to 16 days. But unwatered shoot bamboo is dead in every Hard drought from the
third on anyway (5% alive), so on Hard the Flowering takes away a crop the weather already took. Irrigated shoots
lose the 12 days as on Normal. No change needed.

## Q8. The Lantern Festival

A Small Festival burns 40 lanterns (40 paper, 40 poles, 61 work hours at speed 1) and 60 dishes, and costs one
working day. Festive +4 lasts 20 days; a Normal cycle lasts 15 to 26 (model):

| Colony wellbeing | Work speed from +4 | Days of work gained | Days spent (40 colonists) | Return |
|---|---|---|---|---|
| 10 | +10.7% | 2.1 | 1.1 | 2.0 |
| 20 | +8.4% | 1.7 | 1.1 | 1.6 |
| 30 | +7.0% | 1.4 | 1.1 | 1.3 |
| 40 | +5.9% | 1.2 | 1.1 | 1.1 |
| 50 | +5.2% | 1.0 | 1.1 | 1.0 |
| 60 | +2.4% | 0.5 | 1.1 | 0.45 |
| 80 | +1.1% | 0.2 | 1.1 | 0.2 |

**Worth calling every cycle until the village is past wellbeing 50**, and the first three calls are worth it at
any wellbeing: Tradition 1 unlocks the Goldfish Bowl (+2) and String Lanterns (+1), Tradition 3 the Garden Moon
Gate (+2). After that it costs about half a working day a cycle net, because the game's wellbeing tiers flatten
above 60 and no wellbeing reward can change that. That is acceptable for a festival: it should be a pleasure by
then, not an order. Two small things:

* Festive lasts 20 days and a cycle up to 26, so a village that calls it every cycle is still without it for up
  to six days. A decay of 0.04 (25 days) closes the gap (would improve).
* A Grand Festival's extra +1 costs 20 fireworks, which need an Explosives Factory (400 science, 30 metal). Fine.

## Q9. Late game

**Materials (model; worker-days per unit at wellbeing 30, made and carried 12 tiles):**

| Material | Folktails | Inkpaws | Ratio |
|---|---|---|---|
| Log | 0.04 | 0.04 | 1.00 |
| Plank / pole | 0.11 | 0.04 | 0.41 |
| Gear | 0.21 | 0.14 | 0.66 |
| Paper | 0.06 | 0.05 | 0.83 |
| Treated plank / cured pole | 0.26 | 0.16 | 0.62 |
| Metal block | 0.32 | 0.32 | 1.00 |

**Monuments and the wonder:**

| Faction | Monument | Awe | Radius | Science | Worker-days of materials |
|---|---|---|---|---|---|
| Folktails | Farmer Monument | 2 | 7 | 1,000 | 7 |
| Folktails | Brazier of Bonding | 4 | 10 | 3,000 | 43 |
| Folktails | Fountain of Joy | 6 | 20 | 9,000 | 95 |
| Folktails | Hall of Abundance | 8 | 30 | 15,000 | 315 |
| Folktails | Earth Recultivator | 10 | 40 | 20,000 | 1,433 + 90 to fill |
| Inkpaws | Memorial Arch | 8 | 10 | 3,000 | 45 |
| Inkpaws | Great Sitting Panda | 12 | 30 | 15,000 | 385 |
| Inkpaws | Sky Lantern | 10 | 40 | 20,000 | 1,335 + 76 to fill |

* **The Sky Lantern is fair**: 7% less labour than the Earth Recultivator, same science, same 15,000 build hours.
  (Scrap, resin and extract are rough figures here; the comparison is not better than 15%.)
* **The Memorial Arch is a Brazier's price for a Hall's awe**: +8 for 3,000 science and 45 worker-days. Folktails
  pay 4,000 science and 51 worker-days for +6. The first pass costed the Arch as "+6 = Farmer Monument plus
  Brazier"; its awe was later raised to 8 to reach 30 with three monuments. Put the two points on the Great
  Sitting Panda instead (Arch 6, Panda 14): the total stays 30 and each step matches its vanilla pair.
* Awe 20 costs Inkpaws 18,000 science against 28,000. That is tolerable **only while the Star Tower is missing**
  (Q10). When it ships, the Panda should cost 20,000.

**Wooden Ox (data plus distances):**

| Worker | Lift | Poles hauled a day | Units built | Workshop hours at speed 1 |
|---|---|---|---|---|
| Wooden Ox | 30 | 517 | 176 | 38 |
| Folktails bot, fuel only | 20 | 336 | 117 | 38 |
| Folktails bot, both boosts | 20 | 465 | 165 | 62 |
| Inkpaw, wellbeing 50, 12 h | 18 | 238 | 95 | 46 |

An ox costs about 6 worker-days, lasts 90 days and needs nothing; a bot costs about 8, lasts 70, needs a second
factory, 1.9 biofuel a day, and two more chains to reach the third row. "Strong and slow" is true in workshops
and false on the road: the ox out-hauls the best bot and is worth 2.2 Inkpaws at a Hauling Post. Keep the lift and
the 90 days (they are the design's sentence) and double the price: 20 cured poles, 20 gears, 4 metal blocks, 96
hours. Thin: the value of a bot's upkeep is the first pass's estimate, never measured.

**Wellbeing a colonist can reach (data):**

| Faction | Basic | Nutrition | Social | Fun | Aesthetics | Awe | Boosts | Total |
|---|---|---|---|---|---|---|---|---|
| Folktails | 5 | 15 | 13 | 12 | 9 | 30 | 0 | 84 |
| Iron Teeth | 5 | 17 | 4 | 18 | 10 | 30 | 0 | 84 |
| Inkpaws | 5 | 19 | 11 | 12 | 12 | 30 | 5 | 94 |

The Inkpaws' 94 includes Festive 5 (needs a festival every cycle) and seed cakes 3 (a few weeks after a
Flowering): 86 standing, 91 with festivals, 94 briefly. The Opera Stage will add 5 when its module ships. The
2026-11-14 change that raised several needs by one "to at least match the Folktails'" counted a build in
which the needs behind the Water, Festival and Flowering modules were hidden; with them on it overshoots by ten. More telling is the road there:

| Science spent | Folktails | Iron Teeth | Inkpaws | Inkpaws, proposed trims |
|---|---|---|---|---|
| 0 | 12 | 11 | 13 | 13 |
| 400 | 18 | 15 | 21 | 21 |
| 1,000 | 26 | 17 | 27 | 26 |
| 1,500 | 28 | 17 | 31 | 29 |
| 2,500 | 31 | 17 | 38 | 35 |
| 4,000 | 32 | 22 | 45 | 41 |
| 6,000 | 34 | 22 | 48 | 44 |
| 10,000 | 39 | 42 | 51 | 47 |

(Model: the wellbeing a colony can hold if it buys the cheapest point first; monuments and festivals aside.)
Thirteen points at 4,000 science is 2.8 against 2.2 in working speed, a quarter more work per colonist through
cycles 4 to 8, from needs that cost poles and paper where the Folktails' cost metal and extract. The trims: Play
3 to 2, Ink painting 3 to 2, Watching the young 4 to 3, Tea 5 to 4. Ceiling 90 (82 standing, 87 with festivals).
Thin: a player does not buy in this order, and Inkpaws earn science more slowly late (Q10).

**The dish ladder has one step out of order (data):** steamed rice (190 science, 1.5 food a tile-day) gives 3 and
sweet rice balls (650 science, 1.07 a tile-day, a mill, a kitchen and a persimmon orchard) give 2. Swap them.

## Q10. Science

**The first two hours, in the design's order, on inventors alone (model; 15.3 science an inventor-day, the first
staffed about day 4.5):**

| Beat | The design says | Science | Running total | Day, 2 inventors | Day, 4 inventors at wellbeing 10 |
|---|---|---|---|---|---|
| Steamer | days 3-5 | 40 | 40 | 5.8 | 5.0 |
| Teahouse with tea in it | days 3-5 | 400 | 440 | 18.9 | 9.6 (and not before day 12: bushes) |
| Scoop wheel, gate and a flume | days 5-8 | 290 | 730 | 28.4 | 13.0 |
| Medium Cistern | first drought | 100 | 830 | 31.6 | 14.2 |
| First Moon Loft | end of cycle 1 | 200 | 1,030 | 38.2 | 16.5 |
| Paddy spout, rice, pickles | cycle 2 | 420 | 1,450 | 51.9 | 21.4 |
| Lanterns and the Small Festival | cycle 2 | 850 | 2,300 | 79.7 | 31.3 |
| Trip-hammer mill, sweet rice balls | cycle 3 | 500 | 2,800 | 96.0 | 37.2 |

A vanilla opening has one or two inventors. With two:

* **Unreachable: "days 5 to 8, a scoop wheel and a short flume".** Even bought straight after the Steamer it is
  330 science: day 15. The 2026-11-14 fix took the gears out of the wheel's cost; the science was the other half.
  With Flume, Corner and Drop at 0, the Gate at 40 and the Scoop Wheel at 60 the beat costs 100 and lands on day
  9 (day 8 with a third inventor).
* **Unreachable: "days 3 to 5, Hammock and Teahouse".** The Hammock, yes. The Teahouse belongs in cycle 2: bushes
  first bear on day 12, the chain is 400 science, and it wants haulers. Move it in the table (DESIGN.md is the
  coordinator's).
* **Reachable if the water beat is cut as above:** Steamer 40, water 100, Medium Cistern 100, Moon Loft 200 = 440
  by day 19, the end of cycle 1.
* **Cycle 2 is tight but fair**: tea 400, pickles 120, paddy 300, lanterns and the square 850 is 1,670; three
  inventors at wellbeing 10 to 20 make that by day 40. The festival's own chain is the heavy part (Gear Workshop
  100, Paper Mill 250, Lantern Workshop 200, Square 300). Lantern Workshop 100 and Square 200 would put the first
  festival in cycle 2 for a two-inventor village too (thin).

**The whole tree (data):** Folktails 136,470, Iron Teeth 138,890, Inkpaws 122,910. But Folktails earn the back
half at an Observatory (12 science per four-hour cycle from four workers: 138 a worker-day at wellbeing 50) and
Inkpaws at Inventors (46 a day). The Star Tower waits for the RingtailVenues module and is hidden, rightly. Until
it ships, the Memorial Arch, Great Sitting Panda and Sky Lantern (38,000 science) take 826 inventor-days against
275: nine extra full-time workers for a hundred days. Either ship a plain day-staffed science building in the
meantime, or accept it and say so, or take 40% off those three costs until the tower exists. This is a decision
for the coordinator; the number is solid.

**Pointless next to an alternative:**

* Small Cistern (40 water, 15 logs) next to a pump that holds 146 for 12 logs. Fixed by the pump.
* Sweet rice balls next to steamed rice. Fixed by the swap.
* Dew Collector: 2 water a day for 300 science. Flavour; harmless.
* Nothing else. The Pole Mill is a bridge by design (poles from bamboo cost 0.41 of milled ones after day 8) and
  earns its place in a timber Flowering and in Hard droughts.

## Q11. Hard, long droughts and badtides

**Measured (worst cases: the scripted colony does not stock up).** Folktails Hard: 26 water at the first drought
(day 8, five days), all thirteen dead by day 18. Inkpaws Hard, twice: 56 to 57 water at the first drought, nobody
dead in it, about half the shoot bamboo dead while the cabbage and timber bamboo came through; then all dead or dying
of thirst in the second drought (day 18, six to eight days), which they entered with no water at all because the
village drank everything the single pump made while recovering. **Water, not food, killed all three.** A pump
makes 40 a day and thirteen colonists drink 27: one pump cannot fill a store in the five to eight days Hard gives.
Two pump workers from day 2 can (about +50 a day).

**Model:**

| Hard drought | Days | Water per colonist to store | Shoot bamboo alive | Cabbage | Timber bamboo | Oak (15) |
|---|---|---|---|---|---|---|
| 1 | 3-6 | 13 | 67% | 100% | 100% | 100% |
| 2 | 4-8 | 17 | 25% | 75% | 100% | 100% |
| 3 | 5-10 | 21 | 5% | 40% | 95% | 100% |
| 4 | 6-12 | 25 | 0% | 17% | 67% | 100% |
| 6 | 8-16 | 34 | 0% | 0% | 25% | 86% |
| 8 | 10-20 | 40 | 0% | 0% | 3% | 50% |
| 13+ | 15-30 | 61 | 0% | 0% | 0% | 3% |

Where the faction is under strain, in order:

1. **Day 6 to 9, the first drought.** Water, as in vanilla. Today two pump shelves (292) are all the storage a
   Hard start needs; after the pump fix it needs two Small Cisterns as well (30 logs). Vanilla needs five Small
   Tanks (75 logs). Still easier than vanilla Hard.
2. **The second and third droughts (4 to 10 days, from about day 15).** No unwatered staple survives the third.
   The answer is a flume and a Cistern Tap, 640 science today (450 with M3 to M5) by about day 25: three or four inventors, not two. The
   Hard tip names cabbage as the staple; it should name the tap as well.
3. **From the fourth drought, timber bamboo dies** (67% alive, then 25%). The Pole Mill and oak carry building.
   This is where the 2026-11-14 change from 7 to 10 dry days earns its keep.
4. **Badtides (Hard: from cycle 4, 6 to 12 days at first).** A Flume Gate shuts on badwater, so every field on
   that line is in a drought. The Cistern Tap pours clean water: it is the badtide answer too. Rice dies 1.5 days
   after its paddy drains; a paddy costs a quarter of what a strip costs to keep wet (0.047 m3 a tile a day), so a
   Medium Cistern holds 140 paddy tiles for nine days.
5. **Late Hard (15 to 30 days).** A hundred colonists need about 6,100 water to drink (five Large Cisterns) and
   one more Large Cistern through a tap for 500 tiles of crops. Vanilla Hard asks for the same order of storage.

Nothing breaks that the design has not planned for. No Hard-only number change is proposed.

## Proposed changes

Files are under `catalogue/`. "Run" is the game run that would confirm it; none has been made.

### Applied on 2026-11-25 (catalogue lane; `tools/balance/run.py all` on the regenerated build)

The coordinator approved the list below (DESIGN.md change log, 2026-11-25). The tables that follow keep the "Now"
column as it stood when the proposals were written; this is what the catalogue holds today. No game run has been
made on any of it.

| # | Applied | Where | In the build now |
|---|---|---|---|
| M1 | yes | `rules.toml [shelves] no_ingredient_hours = 16` (generator rule: recipes with no ingredients, never below vanilla) | Water Pump holds 49 (was 146), Large Water Pump 240 (was 720), Badwater Pump 49; `BadwaterExtracted` and `Dirt` are back on their vanilla shelves (16 hours is less) |
| M2 | no (code) | the Bell and Ringtails code lanes | A Ringtail builder is still 0.62 to 0.73 of an Inkpaw at 12/12 as shipped; 0.83 to 0.97 with the bonus by their own night (the model's row, Q4) |
| M3 | yes | `building_stats.toml` | Flume, Flume Corner, Flume Drop: 0 science |
| M4 | yes | `building_stats.toml` | Flume Gate 40 |
| M5 | yes | `building_stats.toml` | Scoop Wheel 60 |
| M6 | yes | `buildings.toml` | **Opera Stage ships** as an ordinary attraction (Well-being group, its own model, no workers, no Ringtail claim in data). **Star Tower ships** as a Ringtail night post: the vanilla Observatory without its power need, 4 workers, 12 science a four-hour cycle each, 60 poles, 30 gears, 10 paper, and it keeps its 1,000 science (`PandabornNightPostSpec.UnlockOnArrival = false`, Ringtails code 3aff2c9: the first Moon Loft unlocks the other posts for free, not the tower). No Bot unlock on a night post. The Q10 text in `tools/balance/questions.py` still says the tower is not in the build: that sentence is written by hand there |
| M7 | text lane | `catalogue/text/**`, DESIGN.md | DESIGN.md is changed; the need tooltip of Opera still says "while the Ringtail performers are at work" (`text/needs.json`, Performance) |
| W1 | yes | `rules.toml [shelves] recipe_hours` (`FlowingWater = 0`, `FlowingBadwater = 0`: the vanilla shelf) | Cistern Tap and Discharge hold 15 water (was 144) |
| W2 | yes | `faction.toml`, adult `PandabornBellSpec` both curves: 12 h +0.33, 13 h +0.228, 14 h +0.14, 15 h +0.064, 16 h 0 | Workshop, builder and carrier output 1.00 at 12, 13, 14, 15 and 16 hours at every wellbeing level (was 1.01 to 1.02 at 13 to 15). `BellMovementSpeedCap` stays 2.66: 2.0 x 1.33 is exactly the cap |
| W3 | yes | `needs.toml` | Steamed Rice 2, Sweet Rice Balls 3 |
| W4 | yes | `needs.toml` | Play 2, Ink painting 2, Watching the young 3, Tea 4 |
| W5 | yes | `needs.toml` | Memorial Arch 6, Great Sitting Panda 14 |
| W6 | yes | `recipes.toml` | Wooden Ox: 20 cured poles, 20 gears, 4 metal blocks, 96 h |
| W7 | yes | `needs.toml` | Festive spirit and Grand festival fade at 0.04 a day (25 days) |
| W8 | yes | `building_stats.toml` | Lantern Workshop 100, Festival Square 200 |
| W9 | yes | `recipes.toml` | Pickles: 2 cabbage to 5, 1.7 h (1.50 food a tile-day, was 1.80; the Pickle Yard holds 29 cycles) |
| W10 | yes | `rules.toml [shelves] recipe_hours` (`Plank = 24`) | Pole Mill holds 20 logs (was 39) |
| W11 | **no** | models lane | The Ink Studio's model is one cell with one `#Slot#Spot`; four seats need a model with four slots (a 2 x 2 studio). Capacity stays 1 |
| W12 | yes | `recipes.toml` | Bamboo seed cakes: 6 a seed (a 40-colonist Flowering: 486 cakes, 4.7 days of all food; was 324 and 3.2) |
| W13 | later | | Left as it is |

Two more data fixes went in with them, both making the build match what was already decided: the **Flume Bridge
Span** had no entry in `building_stats.toml` and so cost what its shell does (a Throttling Valve: 5 cured poles, 5 metal
blocks, 500 science); it now costs 4 poles, 1 log and 120 science, as the Flume Bridge. The **Smoke Kiln** still asked
for the Wood Workshop's 250 hp although the first sheet says "log smoke instead of resin and 250 hp"; it needs no power
now.

What the model says after them:

* **Wellbeing ceiling 95** against the Folktails' 84 (basic 5, nutrition 19, social 9, fun 15, aesthetics 12, awe 30,
  boosts 5). The trims took 4 off (94 to 90) and the Opera Stage, now shipped, put 5 back. Without festivals 90; the
  ceiling is not lower than before the trims, it is one higher. Mid game (wellbeing a colony can hold at equal science,
  the Q1 table): Inkpaws 17 / 20 / 21 / 25 / 28 / 34 / 41 / 44 / 47 at 200 / 400 / 700 / 1,000 / 1,500 / 2,500 / 4,000 /
  6,000 / 10,000 science against the Folktails' 16 / 18 / 20 / 26 / 28 / 31 / 32 / 34 / 39: level up to 1,500 science,
  3 to 10 ahead after it (was 2 to 14 ahead throughout).
* **The water beat** (Flume Gate 40 + Scoop Wheel 60; flumes free) costs 100 science, was 290. In the design's new
  order (Steamer, then water; tea in cycle 2) the running total is 140: day 13.7 with one inventor, **day 9.1 with two,
  7.8 with two at wellbeing 10 or more, 6.1 with four** (the same formula as Q10, 15.3 science an inventor-day from day
  4.5). The Q10 table in `tools/balance/out/q10.md` still lists the Teahouse before the water beat (its beat order is
  written in `questions.py`), so its own row reads day 22 with two inventors: the order there needs the same move.
* **First festival** (Lantern Workshop 100, Festival Square 200, plus paper): 650 science for the beat, was 850.
* **First drought**: one pump holds 1.8 days of water for 13 colonists (was 5.3; Folktails 0.55).
* **Whole tree** 123,220 science (was 122,910: the Opera Stage's 1,200 is in, the water set's 890 is out).
* **Ringtail parity** is unchanged by data and is the code lane's (M2).

### Rulings after the second audit, 2026-11-25 (catalogue lane)

| Ruling | State | In the build now |
|---|---|---|
| Bamboo seed always has a use | applied | New Steamer recipe `PandabornBambooSeedCakesSteamed`: 1 seed to 2 cakes, 1.0 h, log fuel (cycle and fuel are the Steamer's rice numbers; no one has tuned them). The Kitchen's recipe with rice flour stays at 6. The seed-cake good and need wait for Flowering only; with the Water module off the Flowering still ends in food |
| Dew Collector | applied | `PandabornDewWater` one Water every 7.5 h (was 12), store 6 (was 4): **3.2 a day, 1.1 in a drought**. A colonist drinks 2.11 a day, so four collectors (12.8 a day) keep an outpost of six in water outside droughts: 0.7 collectors a colonist in fair weather, 1.9 in a drought (model). Cost unchanged (15 poles, 4 paper, 300 science). Against a pump worker's 48 a day, fifteen collectors (225 poles, 60 paper, sixty tiles) replace one worker: not a spam worth doing early, and the code still has no crowding rule |
| Goldfish Bowl, Garden Moon Gate | applied | +2 each, so the Panda Statue's price and reach: 50 logs, 10 poles, three tiles (were a Shrub's 12 logs and one tile). 500 science without the Festival module; with it Tradition gates them and science is 0 |
| Hanging Lantern at Tradition 2 | applied | The same Lantern need and price as the Standing Lantern, but it reaches two tiles instead of one (`RangedEffectBuildingSpec.EffectRadius` 2): one hung lantern lights a 5 x 5 patch where a standing one lights 3 x 3 |
| Potted Pine | applied | Paid in poles (6) where the Shrub takes 12 logs; same Shrub need and reach |
| Pine resin | **not removed** | The Inkpaws do not gather it: a pine's resin is in the `Tappable` group and the faction has no Tapper's Shack, and no Inkpaws building costs it (the Indicator was recosted). It remains only as a row in storage pickers and as the pine's own yield line. Taking it out of the faction's goods would make every other mod's building that costs resin throw when placed in an Inkpaws game (`GoodService.GetGood`), and the pine template would need its `GatherableSpec` cut by a modifier nobody has run. No recipe can want it honestly while nothing taps it |
| Timber bamboo growth 5 to 7 days | **held: first bamboo poles land on day 10 or after** | Poles per tile-day: bamboo 2 / 5 = 0.40 against birch and mill 1 / 7 = 0.143 (2.8 times) and pine 2 / 12 = 0.167. At 7 days 0.286: 2.0 times birch, the intent. At 6 days 0.333: 2.3 times. First bamboo poles: the model staffs the Forester on day 2.5, planting is half an hour a tile, cutting 1.5 h: day 7.6 to 8 at 5 days (the first pass's "after day 8"), **day 9.6 to 10.1 at 7**, 8.6 to 9.1 at 6. A newcomer following the tutorial builds the Forester after the Pole Mill and twenty poles (about day 3 to 3.5), so day 10.6 to 11.1 at 7 days. DESIGN.md's first-hours row says "days 6 to 10: the first bamboo is cut". Nothing is blocked by it (the Pole Mill makes 27 poles a worker-day from logs, the Scoop Wheel and flumes are affordable from milled poles), but the row would have to read "about day 10". `tools/balance` has no first-poles figure of its own; these are its day constants worked by hand |

### Must change, or must be decided

| # | File | Key | Now | Proposed | Why | Confidence | Run to confirm |
|---|---|---|---|---|---|---|---|
| M1 | `rules.toml` `[shelves]` (new key; generator) | hours for recipes with no ingredients (`Water`, `Water.Efficient`, `Badwater`, `BadwaterExtracted`, `Dirt`) | 48 (pump holds 146, large pump 720) | 16, never below vanilla (pump 49, large pump 240) | The pump is a better cistern than the cisterns; careless villages never meet thirst (Q1) | High (data, measured) | `inkpaws-careless` and `inkpaws-hard` again: water at the first drought near 50 plus cisterns; some thirst, no deaths on Normal |
| M2 | `faction.toml` `[characters.ringtail_adult]` (and the Bell and Ringtails code), or data only | the Ringtails' rested bonus | none: a Ringtail is 0.75 to 0.87 of an Inkpaw at 12/12 | A: the bonus by the length of their night (code). B: `WalkerSpeedManagerSpec.BaseWalkingSpeed` and `BaseSlowedSpeed` 2.7 to 3.6. C: `GoodCarrierSpec.BaseLiftingCapacity` 14 to 16 | DESIGN.md says a night builder equals a day builder at twelve and twelve; the build says 0.75 (Q4) | High on the arithmetic; the choice is the coordinator's | `rt-throughput2` (queued, never ran) with day and night builders on the same queue of dens: goods carried per worker per shift |
| M3 | `building_stats.toml` | `PandabornFlume`, `PandabornFlumeCorner`, `PandabornFlumeDrop` science | 60 each | 0 | The "days 5 to 8" water beat costs 290 science: day 15 with two inventors (Q10) | High (data); the day is model | An Inkpaws standard playtest with two inventors: day of the first flume |
| M4 | `building_stats.toml` | `PandabornFlumeGate` science | 80 | 40 | Same | High | Same |
| M5 | `building_stats.toml` | `PandabornScoopWheel` science | 150 | 60 | Same | High | Same |
| M6 | decision (catalogue `buildings.toml` `PandabornStarTower`, or `building_stats.toml`) | late science | Star Tower hidden; 38,000 science of monuments on Inventors alone | Ship a day-staffed science building until RingtailVenues exists, or cut `PandabornMemorialArch`, `PandabornGreatSittingPanda`, `PandabornSkyLantern` science by 40% until it does, or accept | 826 inventor-days against 275 Observatory worker-days (Q10) | High (data) | None needed |
| M7 | text lanes, not catalogue numbers | Dew Collector description; Teahouse tutorial stage; DESIGN.md first-two-hours table; DESIGN.md "a cup takes the edge off thirst" | "Collectors built close together share the same dew"; no word of haulers; Teahouse on days 3 to 5; thirst | Drop the dew sentence or write the rule; say the Teahouse and Hot Spring Bath are stocked by haulers or night couriers; move the Teahouse to cycle 2; drop the thirst clause | The toolbar must not lie (Q3, Q6, Q10) | High (code and data read) | None needed |

### Would improve

| # | File | Key | Now | Proposed | Why | Confidence | Run to confirm |
|---|---|---|---|---|---|---|---|
| W1 | `rules.toml` `[shelves]` (per-recipe exception; generator) | `FlowingWater`, `FlowingBadwater` (Cistern Tap, Discharge) | 48 cycles: 144 water held | vanilla 5 cycles: 15 water | Haulers move 144 water out of the cisterns into a store nobody can drink from (Q5) | Medium (data; no run) | Water lane's W3 drought with a Hauling Post: water left to drink |
| W2 | `faction.toml` `[characters.adult]` `module_specs.Bell.PandabornBellSpec` | `WorkingSpeedCurve`, `MovementSpeedCurve` | 12 h +0.33, 16 h 0 | 12 h +0.33, 13 h +0.228, 14 h +0.14, 15 h +0.064, 16 h 0 | Flat from 12 to 16; today 14 hours beats 12 by 2% (Q2). (For exactly 16 hours' worth use 0.3333 at 12 and raise `modifiers.toml` `BellMovementSpeedCap` from 2.66 to 2.67, or the module reports the cap as too low) | High (data) | Bell probe at 13, 14, 15 hours: multipliers |
| W3 | `needs.toml` | `PandabornSteamedRice` / `PandabornSweetRiceBalls` `favorable_wellbeing` | 3 / 2 | 2 / 3 | The harder dish gives less (Q9) | High (data) | None needed |
| W4 | `needs.toml` | `PandabornPlay`, `PandabornContemplation`, `PandabornCubWatching`, `PandabornTea` `favorable_wellbeing` | 3, 3, 4, 5 | 2, 2, 3, 4 | Mid-game wellbeing 7 to 14 above Folktails at equal science; ceiling 94 against 84 (Q9) | Medium-low (model of a buying order) | Paired 60-day playtests with a driver that can grow: wellbeing and population by day |
| W5 | `needs.toml` | `PandabornMemorialArch` / `PandabornGreatSittingPanda` `favorable_wellbeing` | 8 / 12 | 6 / 14 | A Brazier's price for a Hall's awe (Q9) | Medium (data) | None needed |
| W6 | `recipes.toml` | `PandabornWoodenOx` `ingredients`, `cycle_hours` | 10 cured poles, 15 gears, 2 metal; 72 h | 20, 20, 4; 96 h | Out-hauls a fully boosted bot, no upkeep, cheaper (Q9) | Medium-low (bot upkeep never measured) | Grid run with one ox and one Inkpaw hauler on the same pile: goods moved per day |
| W7 | `needs.toml` | `PandabornFestive`, `PandabornFestiveGrand` `daily_delta` | -0.05 (20 days) | -0.04 (25 days) | A cycle lasts up to 26 days (Q8) | Medium (data) | None needed |
| W8 | `building_stats.toml` | `PandabornLanternWorkshop` / `PandabornFestivalSquare` science | 200 / 300 | 100 / 200 | First festival in cycle 2 for a two-inventor village (Q10) | Low (model) | Standard playtest: day of the first festival |
| W9 | `recipes.toml` | `PandabornPickles` | 1 cabbage to 3 pickles, 1.0 h | 2 cabbage to 5 pickles, 1.7 h | Best food in the game on four counts at once; 1.5 a tile-day is bread's (Q1) | Low (static sums; land never bound in a run) | A land-limited map playtest |
| W10 | `rules.toml` `[shelves]` (per-recipe exception) | `Plank` (Pole Mill) | 39 logs | 24 hours: 20 logs | The one early input everything waits for (Q5) | Low | `rt2-shelves` layout with a Pole Mill and queued dens |
| W11 | `buildings.toml` | `PandabornInkStudio` `EnterableSpec.CapacityFinished` | 1 (vanilla) | 4, if the model has the slots | A hundred colonists need four studios (Q3) | Low (model) | None needed |
| W12 | `recipes.toml` | `PandabornBambooSeedCakes` `products` | 4 | 6 | The Flowering's seed about repays the food it cost; "windfall" wants more (Q7) | Low | Events lane's flowering run with a Kitchen |
| W13 | `building_stats.toml` | `PandabornGreatSittingPanda` science | 15,000 | 20,000, **only once the Star Tower ships** | Awe 20 for 18,000 against 28,000 (Q9) | Medium (data) | None needed |

### Leave alone (checked, fine)

| What | Value | Why it holds |
|---|---|---|
| Shoot bamboo growth, yield, dry days | 3 d, 2, 5 | One day ahead of carrots (measured); 0.67 a tile-day is under the carrot's 0.75; 0.77 work hours a shoot is the dearest raw food |
| Cabbage, timber bamboo dry days | 7, 10 | Taper on Normal is cycle 3 then 5; Hard needs them |
| Steamer ratio and science | 1 to 2, 40 | Day 5.8; labour 0.64 h a food, more than a carrot |
| `harvest_hours` | 16 | A day's harvest; doubles the food buffer, by design |
| `workshop_hours` for workshops with inputs | 48 | No hoarding without haulers (code); 1.4 working days at wellbeing 30 |
| Inkpaw lift, pole weight | 18, 3 | +40% per builder, hidden behind logs in every run |
| Bell peak and cap | +33% at 12 h, 2.66 | Equal work at every wellbeing; cap never reached |
| Nap | -0.6 a day, wellbeing 3, Hammock 1 seat, Platform 5 | Fits a 15-hour day; 3 to 6 colonists a hammock (measured 3 to 4 at 16 h) |
| Tea decay, seats, consumption | -0.4, 5 seats, 1 tea and 0.5 water an occupied hour | 23 to 46 colonists a Teahouse; under one worker per hundred |
| Moon Loft and night posts | 200; 50, 150, 100; 4, 6, 2 workers | Reachable at the end of cycle 1; about 20 Ringtails per 100 |
| Kit valve | one kit a loft a day while night jobs are open | Measured: never over the jobs, stops when anyone is hungry |
| Cisterns | 40 / 300 / 1200; 0, 100, 500 science | Cheaper and earlier than vanilla on purpose |
| Flume Bridge Span | 4 poles, 1 log, 120 science: the catalogue lane's pending entry, asked of this lane | Confirmed: it is the Flume Bridge's trestle. In the build read here it still costs its shell's 5 cured poles, 5 metal blocks and 500 science, which puts crossing two lines behind metal |
| Scoop Wheel rate, tap rate, tap text | 0.10 m3/s; 3 Water an hour; "100 Water, 200 tiles, six days" | Measured by the water lane; the rule of thumb gives 206 |
| Dew Collector rate | 2 a day, 0.7 in drought | Too weak to spam |
| Flowering | first cycle 6, 9 days of rest, 3 seed | Not a death sentence with the advice fixed |
| Festival cost and Festive +4 | 40 lanterns, 3 x 20 dishes | Pays to wellbeing 50, a pleasure after |
| Sky Lantern | cost and fill | 7% under the Earth Recultivator in labour |
| Ox lift and life | 30, 90 days | The design's sentence; fix the price instead |
| Births, lifespan, hunger, thirst | vanilla | First pass Q6; nothing new |

## Where the evidence is thin

1. **Everything past day 20 and 20 colonists.** No run got there. The single most useful thing is a playtest
   driver that keeps cutting trees, so a Folktails and an Inkpaws colony both reach 50. It would settle W4, W8, W9
   and the pole reserve.
2. **Time off duty.** The 3.9 hours for bed and 1.2 for meals are rules of thumb. One colonist's behaviour logged
   every half hour for five days at 12 and 16 working hours (the telemetry already samples workplaces this way)
   would settle Q2 and Q3.
3. **Ringtails at scale.** Courier hours per night and "20 per 100" come from workshop arithmetic. `rt-throughput2`
   never ran.
4. **Tea in a living village.** No run has stocked a Teahouse.
5. **Bots.** The Folktails bot's upkeep is an estimate; the ox has never been timed.
6. **The scripted player.** It plays one build order. A careless human does different careless things.

## Corrections to the first pass

| First pass | Second pass | Why |
|---|---|---|
| Q5: "a Ringtail at lift 14 equals an Inkpaw builder at 12/12" | 0.75 as shipped | The first pass gave Ringtails the rested bonus by their own shift; the build does not |
| Q2: "16 hours keeps 2 of 8 rituals: -10 wellbeing, -17% output" | 16 hours loses the nap: -3 | The first pass left 2.3 hours of leisure at 16 hours; the same budget would stop Folktails holding their own attractions, which they do. Tea has also moved to the Teahouse since |
| Q2: "MovementSpeed is clamped at 2.0" | Cap 2.66, never reached | Fixed in the build on 2026-11-14 |
| Q8: Memorial Arch "+6 = Farmer Monument + Brazier" | The build has +8 at that price | Raised later to reach 30 awe |
| Q8: ox "a fair trade" | Out-hauls a boosted bot | The sheet's ox walked at 1.8 tiles a second; the build's walks at 2.7 like the bot it copies, with lift 30 |
| Q3: tea "a cup, 0.27 hours, wellbeing 2" | One Tea need, 5, at the Teahouse; under one worker per hundred | Redesigned 2026-11-14 |
| Q4: dew needs a crowding rule | Not implemented; not needed at 2 a day | The catalogue's recipe is 12 hours a unit, not the prototype's 4 |
| Wellbeing ceiling 85 against 84 | 94 against 84 | Needs raised by one each while three modules were off |
| Calibration: self-supplied lumber mill 52%, bakery 58% | 64%, 71% | The second pass does not charge a full output trip per input trip. Still unmeasured in game |

---

# First pass (2026-11-14): the colony model and the first stat sheet

Kept as written, because other pages cite its question numbers. It describes the stat sheet of
2026-11-14, not today's catalogue; the second pass above corrects it where they differ.

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
must not be replantable at once: the shipped rule is **9 days of rest after the Flowering** (docs/tech/events.md 5;
DESIGN.md 2decaec). Then the advised reserve is **about 11 food a colonist** (8 above 60 colonists, when shoots matter
less) and 5 poles a colonist, and the seed (3 a plant,
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

