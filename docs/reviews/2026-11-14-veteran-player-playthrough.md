# Adversarial play review: Inkpaws design, revision 3

I read `docs/DESIGN.md`, `docs/CONTENT.md` and `docs/tech/game-mechanics.md` in full, and skimmed `docs/tech/water.md` and `docs/tech/two-peoples.md`. I wrote no files. Section references below (§n) point to game-mechanics.md.

**Bottom line.** The opening is not smoother than Folktails. Overall it is a little rougher:
- **Smoother:** there is no lumber mill, so planks need no power, and the starting adults live long.
- **Rougher:**
  - The first day has only 8 working hours.
  - The thirst deadline falls after the shift ends.
  - Food and building material come from one plant.
  - The woodcutter can wipe out the food grove.
  - The first drought takes away both the staple food and the plank substitute at the same time.
- **On Hard, cycle 1 falls apart.**

The water toolkit and the population switch are the strongest parts. The golden afternoon and the Rest need, as written, are what players will switch off.

---

## A. Playing it through

### Normal, day 0 to end of cycle 3

**Day 1 (game starts at hour 4, §1.1).**
- At 12 working hours the first day has 8 working hours. Folktails get 12.
- First critical thirst comes at 1.43 days, which is day 2, hour 14.
- Working hours available before that: Inkpaws 8 + 12 = 20, Folktails 12 + 14 = 26 (−23%).
- For Inkpaws the deadline falls 2 hours after their shift ends. If the water carrier is not producing by day 2, hour 12, nobody can finish it until hour 0 of day 3. That means about 10 hours of critical thirst (−0.25 movement, −10 wellbeing) while pandas lounge in the "golden afternoon". Nobody dies (thirst kills at 5.7 days), but it is the worst possible first impression.

**Days 1–3.**
- 9 adults cover the water carrier (1), woodcutters (2), forager (1–2), builders (3–4) and the grove keeper (1). Nobody is spare.
- No vanilla map has bamboo, so every stalk must be planted, and the grove keeper has to be built first.
- Planting realistically starts day 2. Fruit first appears after the growth time plus one regrowth period (§7.3).
- So first shoots arrive around day 5. The design's claim of "ready within three days because the start has under four days of food" counts from planting, not from day 1.
- The 130 berries run out around day 4.7. Wild berries cover the gap. It is tight but survivable.

**Days 2–3, "buildings go up noticeably faster".**
- This is false unless early costs are rewritten. Only plank costs become poles (CONTENT rule 3).
- Early vanilla-style costs are mostly logs: weight 6, 2 per trip, unchanged.

**Days 3–8, the Steamer.** It has nothing to cook: rice is tier 2, and charcoal (its listed fuel) is tier 2.

**First drought (day 14–18, lasting 2–3 days).**
- Bamboo, "the first plant to die" (below wheat's 0.5 days dry), dies within hours. Shoots and poles both stop.
- Replanting needs moist soil, so it waits for the drought to end. Then growth plus one regrowth adds at least 3 more days.
- With about 18 pandas the player needs:
  - Food: 18 × 2.67 × (3 + 3–4) ≈ **290–340 shoots**.
  - Water: 18 × 2.12 × 3 ≈ 115.
- The forecast gives 3 days of warning and no duration (§1.6). Nothing tells the player that bamboo stops, or about the recovery lag. A first-time player stocks water only.
- Construction stops too, because there are no poles.
- Cycles 2 and 3 have droughts of 3–5 and 3–6 days, so the gaps are about 8–9 days with 25–30 pandas: **530–720 shoots** in store.
- Cycle 2–3, "first flume to a higher terrace": flumes cannot climb (water.md).

### Hard

- 90 berries last 2.6 days, so starting food runs out around day 3.6.
- Hunger reaches 0 about 1.25 days later (day ~4.9), giving −50% working speed and −10 wellbeing.
- The first temperate season is 5–8 days, so the first drought hits on day 6–9, before any meaningful stock of shoots. It lasts 3–6 days.
- Bamboo dies, and with replant and regrowth there are no shoots until about day 12–18.
- Hunger kills at −3, which is 3.75 days after reaching 0. Deaths start around day 9–13 unless the player has pivoted to blueberries (9 days dry tolerance).
- The first Hard badtide (cycle 4 or later) lasts **6–12 days**.
- Verdict: unplayable as designed. Hard players will set 16 hours or more on minute 1 and then meet the Rest need.

### First badtide

- On Normal it comes from cycle 5, lasts 1 day, and the first one is always short. Hard is above.
- Every flume intake on a river becomes a badwater delivery network into every paddy and along the moist strip beside every flume.
- Any soil contamination kills every plant in 0.2–0.3 days (§7.2).
- Paddy farmers standing in water with contamination ≥0.05 roll for incubation. Contamination means refusing work and −10 wellbeing, with no natural cure (§3.7).
- Nothing in the design shuts flumes automatically.

### 24 hours, mid-game

Assumptions: Inkpaw shift 0–12. Ringtail shift per the design table runs from "late morning" (about hour 6–8) to dawn, so **16–18 hours**.

**Inkpaw cook.**
- 0–0.6: commute (homes ignore workplace, §2.2). 0.6–12: produces. 12 on: about 1.5 hours of eating and drinking, about 3 hours of sleep from hour 21.
- That leaves about 7 hours awake and idle. Fun and social needs fill in about 1.7 hours and last 7–10 days (§13.1).
- So the golden afternoon is mostly wandering, unless the Rest need eats it (see problem 4).
- Night couriers do keep the cook's input shelves full. Every listed input buffer holds at least 12 hours of work (bakery 38 h, gears 30 h, lumber 16 h). That claim holds.

**Inkpaw builder.**
- Building is about 90% walking (§5.6). The +33% working speed touches only the 0.5-hour build chunks.
- At 12 hours a builder does roughly **77%** of a Folktails builder's work, unless lift makes up the difference.
- Handover to the night scaffolders is clean, because sites queue in placement order.

**Ringtail courier.**
- 0–3: sleep. This depends on the unproven day-sleep behaviour, which is the top risk in two-peoples.md §13.
- 3–6: eat, drink, attractions. 6–24: hauling.
- Two hours of awake off-duty is enough for fun needs, which last a week. It is not enough for any daily need like Rest/Nap.
- The rules are "the same for both" peoples, so Ringtails on 16–18 hour shifts would be **permanently tired** under a Rest need tuned to punish 16 hours.

**Ringtail builder.**
- Same schedule. Overnight construction is real and is the most felt Ringtail benefit.

**Handovers.**
- **Power is the broken one.** Inkpaw workshops draw power from hour 0 to 12 only (§4.3, §8). A Ringtail-staffed treadwheel produces only during Ringtail hours (§8: power wheels produce only while staffed). The overlap is about 6 hours, so a gear workshop (120 hp) on treadwheels runs at about 50%.
- **Closing Ringtail buildings by pausing is dangerous.** Pausing releases workers *and marks the building for emptying* (§4.1). Done every morning, it would haul the lantern workshop's inputs out daily.

### Late game (100+ population)

- What is left: 10 dish chains, monuments, the wonder (which ends the map, §13.3), Festivals, Tradition (cosmetic only) and the Flowering (periodic).
- Wooden Oxen are haul-only. Vanilla bots build, farm and produce 24 hours a day, so Oxen are a downgrade, and they make night couriers redundant.
- There is no long-term loop that changes how the colony plays.

### Map types

**Flat.**
- Flumes need fall. A level dry step needs 0.1 head, and a 1-wide channel evaporates about 6.5× faster (water.md).
- Long level runs deliver little.
- "Terraces" become spout-fed paddies, which is a reskinned vanilla fill valve.
- Lifting needs a noria (only in a current) or a treadwheel lift (Ringtail only).
- The Great Sitting Panda needs a cliff.

**Scarce water.**
- The staple is the thirstiest plant, and dry-land crops are luxuries only, so Inkpaws are weaker than Folktails here.
- Dew collectors become the meta (see the exploits under problem 9).

**Tiny maps.** Three separated zones, 10 food chains and dry land at moisture exactly 0 (more than about 16 tiles from a lake) are hard to fit. Rooftop lofts help.

**Big vertical maps.** This is where the faction shines: reservoir, then flumes down terraces, then spouts. It is also where a badtide wipes everything fastest.

**"Lead the water" in drought.**
- The noria needs a current of at least 0.15. Sources go to 0 in drought and reservoirs are still water, **so every noria stops exactly when terraces need lifting.**
- A flume's own moisture reach is 1–2 tiles, not "anywhere a flume can reach".

---

## B. Problems, ranked

**1. Bamboo is a single point of failure, and the first drought removes it.** Game-breaking on Hard, frustrating on Normal.
- **When it bites:** shoots (staple), poles (all construction), paper, charcoal and gears all come from bamboo. It dies within hours (DaysToDieDry below 0.25). Death is permanent. Replanting waits for moisture, then growth plus one regrowth.
- **The replanting may not happen at all.** A dead tree keeps its yield and stands until cut (§7.2). Planters need an unobstructed spot. So dead stalks in a food grove kept out of the cutting area are **never cut, and never replanted**. "Replanted by themselves" would visibly fail (measure this).
- **Smallest fix (data):**
  - Use the brown-and-pause behaviour from water.md (a long DaysToDieDry; the timer resets fully when moisture returns). River bamboo about 4 days, so it survives the first Normal drought. Cloud bamboo about 12 days, unlocked at tier 1.
  - Make cabbage edible raw (like carrot), so the early staple is not one plant.
  - If death is kept, use code to delete dead bamboo outright (stacks also block replanting, §7.1).

**2. Shoots and poles live on the same plant.** Game-breaking for new players.
- **When it bites:** if bamboo is chestnut-like (cut it and it is gone), the woodcutter cuts any grown stalk in the cutting area the moment it matures. That is before fruit appears (growth plus one regrowth), so a grove inside the cutting area **never yields a shoot**. Folktails habit is to mark the grove for cutting.
- **Smallest fix:** first measure `CuttableSpec.RemoveOnCut: false` with regrowing poles. If that fails, the grove tool should mark "food grove" (excluded from cutting) or "timber grove" (added to cutting) automatically.

**3. The 12-hour default day from minute 1.** Frustrating; a quit risk.
- **When it bites:** the first day has 8 working hours, and the thirst deadline lands off duty (section A).
- **What the speed bonus does not cover:** WorkingSpeed does not touch walking. Approximate throughput at 12 hours:

| Job | Throughput vs Folktails |
|---|---|
| Builders | ~77% |
| Porters | 75% (before any lift bonus) |
| Foragers | ~88% (10.2 picks a day vs 11.6) |
| Workshops with porters | ~100% |

- **Smallest fix:**
  - Start at 16 hours. Turn on the golden afternoon with a message once the colony has water storage and a staple (or on day 5).
  - Specify Inkpaw lift so that 12 × lift ≥ 16 × vanilla. Lift 21 gives 3 logs per trip. Or add a MovementSpeed bonus.

**4. The Rest need cannot be tuned to do what the design says.** Frustrating, and adds hammock spam as a chore.
- **When it bites:**
  - Awake off-duty time is about 7.5 hours at a 12-hour shift and about 3.5 hours at 16 hours.
  - To fail at 16 but hold at 12, Rest must need about 4–5 hours a day in a hammock.
  - Every Inkpaw leaves work at the same hour, so that is about 50+ hammock slots per 100 Inkpaws.
  - The golden afternoon becomes a nap, not the teahouse.
  - Ringtails on 16–18 hour shifts with "the same rules" are always tired.
  - Min-maxers will find the threshold hour, for example 14.
  - The catalogue disagrees with itself (see section E).
- **Smallest fix:** drop Rest. Use a code bonus read from `WorkingHoursManager.EndHours`, covering both working speed and movement: 12 h → +33%, 14 h → +14%, 16 h → 0, over 16 → negative. Show it on the slider tooltip. Hammocks become an ordinary attraction.

**5. Ringtail hours are undefined and inconsistent.** Breaks power; Ringtails become strictly better workers.
- **When it bites:**
  - The design table implies 16–18 hour Ringtail shifts. two-peoples.md §16.3 says the night shift is the complement of the slider. Nothing says what happens when the Inkpaw slider is at 16, 0 or 24.
  - At 18 hours against Inkpaws' 12, plus faster walking, Ringtails are 50% more labour per head, so min-maxers fill every roof with lofts.
  - Treadwheel power arrives at the wrong hours (section A).
- **Smallest fix:**
  - Fix the Ringtail shift at 12 hours, for example hours 10–22 (2 hours of overlap, sleep at dawn). Clamp it whatever the slider says.
  - Make the power treadwheel Inkpaw-staffed. Keep the treadwheel *lift*, which does not care about time of day, for Ringtails.
  - Close Ringtail workplaces by unassigning workers, never by pausing (measure this).

**6. Flumes spread badwater.** Game-breaking at the first badtide.
- **When it bites:** contamination kills soil in 0.2–0.3 days. Flumes are watertight, one-way and efficient, so they deliver badwater to every terrace. On Hard the first badtide lasts 6–12 days.
- **Smallest fix:** the intake gate shuts itself when intake contamination is above about 0.05. About 20 lines reading `ColumnContamination`, on by default and switchable off.

**7. Two labour pools and two breeding pools, and the player cannot see them.** Frustrating in mid game.
- **When it bites:**
  - Ringtails can only take Ringtail jobs, and the reverse.
  - The vanilla population panel counts the Beaver and Bot worker types only, so unemployed Ringtails do not show up.
  - Kits arrive "sooner", so the colony drifts toward Ringtails.
  - Migration moves the unemployed first (§9.3), which ships idle Ringtails to districts with no Ringtail jobs.
  - Anyone can live in any home (two-peoples §16.1), so Inkpaw couples in lofts breed Ringtail kits.
- **Smallest fix:**
  - Job-aware nurseries: a home breeds its people only while that people has open job slots in the district.
  - Show a two-row "sun/moon: employed / idle" panel at milestone 2, not 4.

**8. The golden afternoon's premise is wrong.** Dull.
- **When it bites:**
  - DESIGN's facts table says "leisure buildings only matter if pandas have off-duty daylight". In vanilla, colonists already spend 4–5 night hours on needs and attractions (§1.4), with no time-of-day check (§13.1).
  - A 1.7-hour visit lasts a week, so the extra 4 hours are wandering.
- **Smallest fix:** give the afternoon one daily-decaying, cheap ritual, such as tea at the teahouse: a fast-decaying Tea need worth +2. Otherwise call it flavour, not a pillar.

**9. Drought-proof water exploits.** Trivially strong.
- **When it bites:**
  - The dew collector is workerless water "even in drought". Spam 50 and water management is gone.
  - If tea gives Thirst without a water input, drought-proof dry land waters the colony.
- **Smallest fix:**
  - The dew collector yields about 1–2 water a day, falls to about 0.35× in drought (water.md limiter), and each needs an exclusive radius.
  - The tea recipe needs water (1 water + 1 leaf → 2–3 tea).

**10. The noria stops in drought, and may loop forever.** Frustrating, or an exploit.
- **When it bites:** it needs current, so it is dead in drought (section A). In a closed noria-and-flume loop, the noria could run indefinitely and drive water wheels for free power, even in a drought.
- **Smallest fix:** a tooltip saying "needs flowing water; stops in drought". Measure the loop. If it sustains, the noria refuses an intake whose flow comes from its own outlet, or rate-limit it below the loop's losses.

**11. Flumes oversold for irrigation and walking.** Frustrating.
- **When it bites:** a flume's own moisture reach is 1–2 tiles. Water cells block walking (water.md), so flumes become walls through farms.
- **Smallest fix:** teach "flume → spout → pool" as the irrigation unit, since a pool gives cluster moisture. Make the lidded, walkable segment the default piece. Measure moisture width and delivery per gate setting at 10, 20 and 40 tiles.

**12. Festival content is out of order and changes little for Inkpaws.** Dull, or confusing.
- **When it bites:**
  - The first-hour table puts the first Festival at cycle 3–4. But lanterns need lacquer (lacquer tree "late", tier 3) and Ringtail workshops (tier 3). Vanilla fireworks come from badwater, which appears from cycle 5.
  - If the feast means bamboo rice cakes, the Festival is gated behind a Flowering.
  - "Both peoples off duty for an evening and night" changes nothing for Inkpaws, who are off then anyway.
  - A "wave of cubs" contradicts "no runaway breeding by accident".
- **Smallest fix:**
  - Feast = any 3 dishes. Lanterns from paper + poles. The Festival gives Inkpaws a *working day* off (a real cost).
  - Cubs respect the welcome switches.
  - Add an "auto-call when stock is ready" toggle so it is not a once-a-cycle chore.

**13. The Flowering's warning is too short and its timing is unsafe.** Frustrating.
- **When it bites:**
  - A drought-style forecast is 3 days. Cloud bamboo is "slower" and arrives "later". A Flowering during a drought kills both kinds.
  - Min-maxers will run a permanent 50/50 split, so it becomes a non-event, apart from bamboo rice, which makes it something to wish for. That last part is good.
- **Smallest fix:** announce a full cycle ahead with a visible budding stage. Only during temperate weather. Cloud bamboo at tier 1.

**14. "Nothing else depends on Ringtails" is false.** Breaks the fallback promise.
- **What needs Ringtails:**
  - Explosives, from the firework workshop. Dynamite is the terrace-builder's tool.
  - Lanterns and fireworks, so the Festival and Tradition.
  - Mushrooms, so hot pot.
  - The treadwheel lift: the only workerless-free lift without current before tier 3–4 pumps.
  - The Star Tower and the Opera.
- **Smallest fix:** these buildings take Inkpaws when Ringtails are off. Move explosives to an Inkpaw workshop.

**15. The tier-1 Steamer has nothing to cook.** Confusing.
- **Smallest fix:** a "steamed shoots" recipe gives the first dish around day 5. No charcoal needed at tier 1.

**16. The pantry idea is meaningless.** Dull.
- **When it bites:** goods never rot and every food is Hunger +0.3, so stored shoots are as good a pantry as pickles.
- **Smallest fix:** either raw shoots spoil (code), or pickles yield 1 cabbage → 3 pickles so they are the efficient store. Or drop the claim.

**17. Lofts may never breed.** Minor, but blocks the Ringtails' growth.
- **When it bites:**
  - Child slots are ⌊capacity/3⌋ (§9.2), so a "tiny" loft of 2 has 0 slots.
  - The family arriving at cycle 2–3 is unspecified. Two Ringtails is a flat payoff.
- **Smallest fix:** lofts hold at least 3, or the nursery spec sets slots explicitly. The arrival family is 4 adults and 2 kits.

**18. The first Ringtail building is the dullest one.** Dull.
- **When it bites:** couriers mostly duplicate porters. Overnight construction is the visible win.
- **Smallest fix:** make the Scaffolders' Loft the first Ringtail building, or bundle it with the first loft.

**19. Wooden Oxen are haul-only.** Disappointing.
- **When it bites:** haulers never supply building sites (§5.1), so Oxen add nothing to construction.
- **Smallest fix:** allow Oxen in builders, woodcutters and harvesters too.

**20. A single "Beauty" need makes decoration trivial.** Dull.
- **When it bites:** one lantern equals a monument. Identical effects do not stack (§13.2).
- **Smallest fix:** one need per decoration type, plus separate Awe for monuments, as in vanilla.

**21. Dams can kill tea.** Frustrating.
- **When it bites:** arid plants plant only at moisture 0 and die when wet. Raising a lake (moisture reach about 16 tiles) kills a tea slope.
- **Smallest fix:** add a dry-stone wall using `SoilBarrierSpec` BlockFullMoisture (data), and a long DaysToDieWet.

**22. Construction trivialises in mid game.** Dull.
- **When it bites:** light poles, Inkpaw lift, porters at double load and night builders together remove Timberborn's main mid-game constraint.
- **Smallest fix:** poles weigh 2, not 1. Inkpaw lift +50%, not more.

**23. Per-home "welcome cubs" becomes clicking at 100+ population.** A chore.
- **Smallest fix:** a district default plus batch control.

**24. The Great Sitting Panda needs a cliff.** Minor.
- **When it bites:** flat maps.
- **Smallest fix:** a freestanding variant, or any terrain block 3 or more high.

---

## C. Three quit risks in the first two hours

At 3× a game day lasts 154 seconds, so two hours of play reaches about day 45: the first droughts on Normal, and the whole of cycle 1 on Hard.

1. **Thirsty pandas lounging at noon.** The 8-hour first day and 12-hour shifts while the water carrier is unfinished (problem 3).
2. **The woodcutter eats the food grove**, or no shoot ever appears because stalks are cut as soon as they grow (problem 2).
3. **The first drought.** All bamboo dies within hours, food and building stop together, and dead stalks do not get replanted (problem 1).

## Three things most likely to be loved

1. **Flumes on trestles feeding spout-held paddies.** You can see water run where you drew it. This is the screenshot feature.
2. **Poles with no mill and no early power**, if early costs are actually moved to poles.
3. **Population you control:** per-home cub switches and long-lived pandas. Players install separate mods to get this.

The Great Flowering, with a generous forecast and the bamboo-rice reward, is the likely fourth, and so is the lantern-lit night village, if Ringtails pass the gate.

**Things players would remove:** the 12-hour default, the Rest need, and haul-only Oxen.

**Different rather than more fun:** the spout (a reskinned vanilla fill valve), the noria (a water wheel and a pump in one), and kite windmills (wind turbines).

---

## D. Content catalogue

### Missing
- An early raw field food (cabbage is ingredient-only).
- A food-or-timber grove designation.
- A self-closing badwater gate on flume intakes.
- A moisture barrier to protect tea.
- An antidote input plant: the Herbalist uses dandelion, which is a Folktails plant.
- A Ringtail/Inkpaw workforce panel, needed at milestone 2.
- A "rice cakes" good: it is named under rice flour but has no row.
- A use or need for "scrolls".
- The input for the Oil Press: canola is not listed.

### Redundant or confusing
- Rest vs Nap vs Rooftop Terrace "Rest".
- The Tea need is filled by drinking tea *and* by the Teahouse.
- The bamboo water wheel and the noria fill the same current-dependent role.
- The Paifang Gate and Drum Tower are both early monuments with no distinct job.

### Out of order
- The Steamer (tier 1) comes before rice and charcoal (tier 2).
- The first Festival (cycle 3–4) comes before lacquer (late) and badwater-based fireworks (cycle 5+).
- Cloud bamboo arrives "later", but the first drought and Flowering need it early.
- Explosives come at tier 3 and behind Ringtails, though terraces are the identity.
- The treadwheel lift is tier 2 but needs Ringtails, who arrive at cycle 2–3.

### Miscounted
- "Ten foods": 11 are listed besides berries.

---

## E. Contradictions

### Design vs the mechanics reference
- **Leisure needs daylight.** DESIGN's facts table says it does; §1.4 and §13.1 say attractions work at any hour and colonists already have 4–5 night hours.
- **"Work quicker to match".** WorkingSpeed does not speed walking, which dominates building, hauling and foraging (§5.6, §6).
- **"Shoots within three days, because the start has under four days of food".** The grove keeper must be built first, and fruit comes after growth plus one regrowth (§7.3).
- **"Groves are replanted by themselves".** Dead trees stand until cut, and stacks block planting (§7.1–7.2). Measure this.
- **"First flume to a higher terrace".** Flumes cannot climb (water.md).
- **The treadwheel "turns faster under a quick walker", staffed "R (or I)".** Power follows MovementSpeed only while staffed, at Ringtail hours.
- **"A workplace holds one kind of worker"** vs District Crossing "any" and Treadwheel "R (or I)". Both need a per-building toggle the design says does not exist.
- **The design's homes table vs two-peoples.md §16.1.** DESIGN still lists dens for Inkpaws and lofts for Ringtails. §16.1 says the game cannot restrict who lives where, only which kind a home breeds, and recommends dropping "Inkpaws live in dens".

### Design vs itself or CONTENT
- **Rest.** DESIGN says Rest is filled in hammocks and nap platforms. CONTENT's Needs list has Nap, not Rest, and gives "Rest" to the Rooftop Terrace.
- **"Food and wellbeing rules are the same for both"** vs a Rest need that punishes long shifts while Ringtails work 16–18 hours.
- **Bamboo regrowth.** CONTENT says bamboo "spreads when left unmarked; browns in drought and regrows". DESIGN says spreading is undecided, and the change log replaced regrowth with replanting.
- **Pepper "can follow rice in a drained paddy"** vs the change log dropping crop rotation. Arid plants also need moisture exactly 0, and a paddy beside a flume stays moist.
- **"Nothing else depends on Ringtails"** vs the list in problem 14.
- **"No runaway breeding by accident"** vs the Festival's "wave of cubs".
- **Top monument.** DESIGN names the Great Sitting Panda; CONTENT names the Hall of Harvests.
- **"Forager's Nest: shoots from far groves"** vs the hardcoded 20-tile range (§7.1).
- **The Festival "both off duty together"** is a no-op for Inkpaws.

---

## F. Must be measured in game (the reference does not settle these)

1. Does the forester replant a tile holding a dead tree? Do dead bamboo keep their poles?
2. Does `CuttableSpec.RemoveOnCut: false` regrow the cut yield on a timer?
3. Ringtail day sleep. Close Ringtail workplaces without triggering emptying, and check the slider at 0 and at 24.
4. Is a noria-and-flume loop self-sustaining? How deep must a current be to turn the noria?
5. Flume delivery and evaporation over 10, 20 and 40 level or falling tiles. Moisture width beside a flume and around a spout pool.
6. Does a workerless Drying Rack or dew collector get its input filled and output emptied without porters?
7. Can a staffed attraction (the Opera) be built in data? Do Sleep-effect hammocks get picked?
8. Paddy farmers: the swim penalty and the contamination rate while working rice.
9. Gravity-battery sizing to move Ringtail-hour power into Inkpaw hours.
10. In the colony model: shoot yield per pick and plants per panda, so that one forager feeds about 15 pandas. Inkpaw lift at which 12 hours matches 16. Early costs rewritten to poles so the "fast building" claim is felt on day 2–3.
