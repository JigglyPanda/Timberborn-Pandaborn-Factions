# Inkpaws design review: first-time player and creative director

**Verdict.** The design has two strong hooks (bamboo aqueducts and the day/night handover), but as written the first 90 minutes play as Folktails with pandas, and the first three hours ask for about twelve new ideas. Several land in clumps at the worst moments. The biggest risks are the day-1 food path, afternoons that look like idle pandas, flumes that fail silently, and Ringtails that read as a night-shift servant class.

**Basis.** I read `DESIGN.md`, `CONTENT.md` and all three tech notes in full; nothing was run in game. Sichuan and cultural details come from my own knowledge and were not checked against sources, so a native reader should confirm them. "Needs prototype" marks feasibility I inferred from the tech notes.

**Pacing assumption.** At 3x a day lasts about 2.5 real minutes, so three hours with pausing is roughly 40–60 game days, or cycles 1–3 on Normal.

---

## 1. Concept-by-concept learning audit

Marks: **K** known from vanilla; **1+** one new idea, well introduced; **1?** one new idea with no clear teaching moment; **M** more than one new idea at once.

| # | When | Concept | Mark | Note |
|---|---|---|---|---|
| 1 | min 0 | Start, Village Hall, water, forager, woodcutter | K | About 25 vanilla buildings are renamed, and each costs a moment of recognition |
| 2 | min 2 | Poles replace planks; no mill | 1? | Only visible in cost lines; nothing says where poles come from |
| 3 | min 3 | Bamboo: planted by Grove Keeper, shoots by Forager, poles by Woodcutter, thirsty, two kinds | **M** | Five facts at the survival-critical moment; vanilla maps have no wild bamboo |
| 4 | day 1 | Shoots are the staple; under 4 days of food | K, with a trap | The vanilla reflex is farmhouse and carrots; cabbage is not listed as edible raw |
| 5 | day 1, hour 12 | Twelve-hour day | 1? | First seen as "everyone stopped while the sun is up" |
| 6 | day 1 | Inkpaws work faster | 1? | Invisible |
| 7 | days 3–8 | Rest need, hammock, overwork backfires | 1? | Three near-identical labels: Sleep (vanilla), Rest (design; also the Rooftop Terrace's need in CONTENT), Nap (CONTENT) |
| 8 | days 3–8 | Steamer, the "first kitchen" | K, broken | It only makes steamed rice, and rice arrives in cycle 2 |
| 9 | week 1 | Slow births, "welcome cubs" switch, wellbeing gate | M, not urgent | "Why no babies?" has no answer on screen |
| 10 | first drought | Bamboo dies back and is replanted | K | The docs disagree: "first to die" (DESIGN) against "browns and regrows" (CONTENT) |
| 11 | cycle 2 | Three zones; a separate Hill Farm for dry crops | 1+ | The planting overlay teaches it; "Hill" wrongly implies slope |
| 12 | cycle 2 | Bamboo spout | 1? | Fiddly placement; needs a walled field and water behind it |
| 13 | cycle 2 | Ten foods plus tea; pickles as "pantry" | K | The pattern is known, but the ladder is long |
| 14 | cycle 2–3 | Flume: one-way, level or downhill, intake needs head, corners need a 2x2 box, trestles, gate, blocks walking | **M** | Six or more rules, and every failure is silent |
| 15 | cycle 2–3 | Noria: needs current, lifts a fixed height | 1? | The name is obscure |
| 16 | cycle 2–3 | Loft brings Ringtails | 1+ in intent, **M** in practice | Bundled with rooftop placement, a second set of buildings, new hours and a new home type |
| 17 | cycle 2–3 | Ringtail hours | 1? | Not specified to the player; no interface |
| 18 | cycle 2–3 | Ringtail-only buildings | 1? | Scattered across toolbar categories |
| 19 | cycle 3 | Kindergarten, cub-watching | 1+ | Self-explanatory |
| 20 | cycle 3–4 | Festival: stockpile, call, once per cycle, both off duty, Tradition | M, but player-paced | Acceptable with a checklist panel; gated too deep (see 2.6) |
| 21 | after 3 h | Flowering, Oxen, monuments | M / K | Later |

About twelve new ideas in three hours is on the heavy side for the owner's stated worry. A budget of one new idea per 20 minutes (nine at most) is reachable with the fixes below.

### The first three hours as a player

| When | Sees and thinks | Gets wrong | Finds out by |
|---|---|---|---|
| Minutes 0–5 | Familiar opening. Looks for the lumber mill and carrots | Builds a Farmstead for cabbage as "carrots"; delays the Grove Keeper as vanilla players delay the forester | Starvation on day 4. Nothing warns them |
| Day 1, hour 12 | Everyone stops and the sun is up. "Bug?" | Drags the hours slider to 16 or 18 | A slow wellbeing sag days later, never linked to the cause |
| Days 1–3 | Pandas mill about near the hall for 12 hours a day | Concludes the afternoon is dead time | Never. This is the anti-moment of the mod |
| Days 2–3 | First poles. Marks the grove for cutting, as with any tree | Woodcutters clear-cut the food source | Shoots stop |
| Days 3–8 | Builds the Steamer | It has nothing to cook | "Lack of resources" status |
| First drought | Bamboo browns; food stops | Expects it back when water returns | Dead stalks must each be cut before replanting (one plant per trip); the food gap is drought plus clearing plus three days |
| Cycle 2 | Spout and paddy | Does not wall the field, so a shallow sheet floods cabbage and bamboo; or puts the spout where no water reaches its back | Dying crops |
| Cycle 2 | Tea on dry ground | Later runs a flume past it; the moist strip kills the tea | "Dying" with no reason given |
| Cycle 2–3 | Runs a flume from the river bank | River surface is below the flume bed, so nothing enters; draws a bend without a turning box; runs it across the village and cuts paths | A dry flume and no message |
| Cycle 2–3 | Loft built; red pandas appear | Expects them to fill open jobs; builds no Ringtail workplace; or opens the Courier Loft by day and sees it empty with a vanilla "no workers" alert | Idle red pandas wandering |
| Cycle 3 | Wants the Festival | Needs paper, lacquer (slow late tree), charcoal, pepper, two Ringtail workshops, and a feast food that only a Flowering provides | Not reachable in three hours |

---

## 2. Ranked confusions and dull spots, with fixes

1. **Day-1 food trap, and a kitchen with nothing to cook.**
   - Spawn a small wild bamboo grove by the Village Hall on a new Inkpaws game, so the vanilla woodcutter-and-forager reflex works at minute one (small code, new-game event).
   - Make cabbage edible raw so the farmhouse reflex also works (data).
   - Give the Steamer a shoots recipe from day 3 (data).
   - Make bamboo regrow after cutting if `RemoveOnCut: false` regrows yield (water.md mentions the flag; needs prototype). Then bamboo is "a tree that grows back", which is one idea.

2. **The golden afternoon looks like idle pandas.** A fun or social visit lasts about 1.7 hours and holds for a week, so twelve off-duty hours are mostly vanilla wandering.
   - Add an off-duty "flop" behaviour: with nothing to do, an Inkpaw sits or sprawls where it is, using the vanilla sit and sleep animations, and slowly fills Rest (small code; reuses the root-behaviour insert already planned for Ringtail sleep).
   - Move the Hammock to tier 0.
   - Post one message at the first bell (wording in section 5).

3. **Flumes fail silently in four ways:** no head at the intake, a bend without a box, a long flat run starving, and a ground flume cutting the district.
   - Add status lines on segments (small code).
   - Make "scoop wheel plus flume" the taught starter kit.
   - Let dragging the tool insert corners automatically (code), or at least flag misaligned neighbours.
   - Prototype must show that a level run of 40 or more tiles still delivers.
   - Ship one map with a spring one terrace above the start (content, no code).
   - Teach bamboo along a flume first, not paddies. The moist strip 1–2 tiles either side is the natural first payoff, and it can come in hour 1.

4. **Ringtails: who works where, why a building is empty, what hours.** See section 3. Fixes are a single moon toolbar group, statuses, a clock arc, a two-row population panel, and the first Ringtail workplace unlocked with the Loft.

5. **Homes cannot be restricted by kind without a patch** (two-peoples.md §3, §16). As designed, Inkpaws will move into lofts, and an Inkpaw couple in a loft will produce Ringtail kits. This needs a code decision before art: the optional Harmony prefix, or a custom home assigner. It is not a text fix.

6. **The Festival is gated behind the deepest chains.** Tier it:
   - Small Festival: paper lanterns from paper and poles, plus any two cooked dishes. Reachable in cycle 2.
   - Grand Festival: adds fireworks.
   - Bamboo-seed cakes become a bonus, not a requirement.

7. **Signature features arrive late.** Flume, Ringtails and Festival all land after about 90 minutes, and many players decide in 30. Proposed order: flop and hammock (minute 8), scoop wheel and a short flume to a grove (days 5–8), first loft at the end of cycle 1, Small Festival in cycle 2, paddies in cycle 2.

8. **Slow births with an invisible gate.** Vanilla growth is an early pleasure, and 13 pandas for an hour is dull. Show the gate on the den panel, default the switch on, and keep the first cubs arriving in cycle 1.

9. **The signature switches off in every drought.** Sources stop, thin flumes evaporate about 6.5 times faster, norias stall, and survival falls back to a vanilla reservoir.
   - Add a Cistern Tap (re-themed vanilla Water Dump, data) that pours stored water into a flume to keep one moist strip alive.
   - Give the two bamboos an everyday difference: river bamboo survives about 3 dry days, cloud bamboo about 8.
   - Stage the drought's end, when water races back through every flume, as a moment.

10. **The hours-slider reflex.** Add a notification when the player raises hours past 12, and a "Weary" status on pandas.

11. **Paddy flooding and tea drowning.** Spout tooltip plus a "roots too wet" reason on dying tea.

12. **Flowering forecast.** Three days' notice cannot answer "grow the slower bamboo". Forecast a full cycle ahead with a visible bud stage, name the kind, and never place it in a badtide cycle (first badtide is possible from cycle 5 on Normal).

13. **Ringtails are weak haulers by the design's own facts.** Load decides hauling, and they walk fast but do not lift more. Set their carrying speed equal to their walking speed (`BaseSlowedSpeed`, data): "Ringtails run with their loads." They become good with light goods and poor with logs.

14. **Treadwheel power runs when Inkpaw workshops are shut.** Power wheels only work while staffed. Either make the Treadwheel an Inkpaw building and keep only the Lift for Ringtails, or teach "Ringtails wind the counterweights at night". "R (or I)" contradicts "nothing to configure".

15. **Oxen overlap Ringtails.** Late-game 24-hour haulers automate the small people away. Keep Oxen to the Porters' Hall and District Crossing, framed as heavy haulage.

16. **"Hardship foods" are fiction.** Food never rots, so pickles are only another dish. Give pickles a high-yield recipe (stretches a harvest). Make tea quench thirst at several cups per unit of water (data), and say so.

17. **Renamed infrastructure.** Details in section 6.

**Doc inconsistencies found.**
- Scaffolders' Loft is in DESIGN but not CONTENT.
- A Scrolls good is missing from the goods list.
- The Steamer is tier 1 but rice is tier 2.
- Bamboo "dies" (DESIGN) against "browns and regrows" and "spreads when left unmarked" (CONTENT).
- Rest against Nap.
- The Opera Stage is "run by Ringtails", but no vanilla attraction has workers (new code).
- "Shoots from far groves" ignores the hardcoded 20-tile range.
- two-peoples.md still describes shift-flipping on shared workplaces, which revision 3 dropped.

---

## 3. The two peoples: is "one rule" one rule?

No. To use Ringtails well a player must understand all of this:

1. Ringtails exist only after the first loft.
2. More come only from kits born in lofts.
3. They work only in Ringtail buildings, and Inkpaws cannot work there.
4. Those buildings must be unlocked and built separately.
5. Their hours.
6. Those buildings are closed by day, and that is normal.
7. Lofts are their homes (not enforceable today).
8. Each one is a mouth and counts for wellbeing.
9. Their stats and lifespans differ.
10. The treadwheel exception.
11. Idle Ringtails cannot fill Inkpaw jobs.

**Cut it to three lines by design, not by text:**
- **Hours.** I recommend replacing the overlapping day table with a clean handover: Ringtails work from the Inkpaws' closing bell until dawn. That is one slider and one clock, and it matches two-peoples.md §16 point 3. Over-long Inkpaw days then visibly shrink the night shift.
- **Buildings.** One toolbar group with a moon icon holds every Ringtail home and workplace.
- **Unlock.** Unlocking the Loft also unlocks the first workplace (science cost 0, data).
- **Stats.** Give them the same lifespan as Inkpaws and show one stat only.

**What the interface must show.**
- A sun or moon badge on every home and workplace, in the toolbar and the panel header.
- A moon arc beside the vanilla working-hours widget.
- A two-row population panel. The vanilla top bar counts only the Beaver worker type, so its totals will not add up.
- A red-panda silhouette in empty Ringtail slots.
- A "closed for the day" status in place of the vanilla no-workers alert.
- A one-time alert for idle Ringtails.

### Per-feature teaching moment and likely misunderstanding

| Feature | Teaching moment | Likely misunderstanding |
|---|---|---|
| Twelve-hour day | First bell on day 1 | "Free 33% if I set 16" |
| Rest need | First "Weary" status; hammock tooltip | Confused with Sleep. Rename it Lounging |
| Three zones | Planting overlay when marking a crop | Hill Farm must be on a hill; tea next to water is fine |
| Flume | First dry segment status | Auto-corners like paths; water climbs; it starts at any bank |
| Bamboo | Starter grove and bamboo tooltip | Clear-cutting the food; expecting dead bamboo to return |
| Flowering | Bud stage one cycle ahead | "Pretty event"; demolishing dead groves instead of cutting them |
| Festival | Checklist on the Festival Square | It costs a night of work; the square is filled only by haulers if built as a goods-consuming building |

---

## 4. Creative director

### Identity

The sentence a player would say: **"It's the cozy panda faction: you run bamboo aqueducts down to rice terraces, and red pandas take over the village at night."**

- **Serves it:** flume, spout, scoop wheel, paddies, bamboo, lofts and lanterns, the bell handover, hammocks, teahouse, kindergarten, festival.
- **Clutter:** the lacquer chain, tofu and soy, ox upkeep, Scroll Workshop, Great Kite Array, surplus monuments, lotus, persimmon cakes, the Long Nap, and a two-bamboo choice at minute 5.

### Where it is "Folktails with pandas"

- **Drought prep** is a vanilla reservoir (fix 9 above).
- **The food chain** is the bread chain three times over.
- **One-for-one clones:** lacquer is resin, tea is coffee, scrolls are books, oxen with oil are bots with biofuel.
- **Power** is vanilla. The strongest twist is to let water be the power line: a rice mill and paper maker as water trip-hammers driven directly by a flume, using the same isolated-node trick as the noria (probably data plus art; needs prototype).
- **Monuments** are four awe tiers again. Make the top one water-themed and show both peoples on it.

### Proposed cuts (about a third of the identity catalogue)

Ranked by how little they would be missed:

1. The Long Nap. It is all custom code, pandas do not hibernate, and it has the worst optics in the design (see section 4, relationship).
2. Lacquer tree, Tapper's Shack, Lacquer Workshop and lacquer. Replace lacquered poles with "cured poles" made at the Charcoal Kiln.
3. Tofu Press, tofu and soybean. Hot pot becomes cabbage plus pepper, with mushrooms as a bonus.
4. Oil Press, Scroll Workshop and ox cards. Oxen need no upkeep; mechanics §10 allows a bot with no needs.
5. Hill Farm, merged into the Farmstead. The crop menu tags tea as "dry ground".
6. Drying Rack and persimmon cakes. Persimmons stay as a raw snack.
7. Lotus and lotus root, deferred to a later update.
8. Hall of Harvests and Drum Tower. Keep the gate, one mid monument and the Great Sitting Panda as the top tier.
9. Great Kite Array; Rooftop Terrace (it competes with lofts for roofs); Moon Gate Garden as an attraction (make it a decoration); Nap Platform as a separate unlock (make it a hammock variant).
10. Flume set from six pieces to four: Flume with automatic legs, Flume Bridge, Corner, Gate.
11. Cloud bamboo is kept but hidden until the first Flowering forecast.

### Moments

- **Produced today:** the water front running down a flume; mirror terraces; lantern-lit night work; festival lanterns; the gold Flowering; the kindergarten.
- **Missing:**
  - pandas visibly eating bamboo while sitting;
  - any clumsiness (rolling, tumbling);
  - a staged bell handover;
  - a terrace cascade (confirm spouts chain downhill);
  - a drought moment that belongs to this faction;
  - dawn mist, which the pitch promises and nothing delivers.

**Trailer, ten shots.**
1. Dawn mist over a bamboo valley, with water arriving and the camera following it down a trestle flume.
2. Spouts filling terraces one after another.
3. Pandas planting rice in the mirror.
4. The afternoon bell: tools down, hammocks, a panda tumbling off the slide.
5. A panda sitting and munching bamboo while a cub rolls past.
6. Dusk: lanterns light in a wave and Ringtails pour out of the lofts.
7. Night timelapse: Ringtails raise a building, and at dawn the Inkpaws wake to it finished.
8. Hillsides turn gold.
9. Festival: both peoples dancing, sky lanterns reflected in the paddies.
10. Pull back to the cliff-carved panda with a Ringtail on its shoulder and water running at its feet.

**The first-five-minutes smile.** A panda sits down and flops the moment the bell rings; a forager carries a shoot bundle bigger than itself; a colonist is named "Le Le (Joy)".

### Whimsy within the vanilla animation set

- **Sit plus a bamboo prop** in the hands reads as eating. Benches become real sit spots.
- **Cubs asleep in a row** in a kindergarten crib (sleep animation).
- **Adults use the slide** (sit animation).
- **Building animation:** the scoop wheel turns, the trip-hammer thumps, kites bob, the steamer puffs, pinwheels follow the wind, lanterns light staggered by position.
- **Sound:** panda bleats and cub squeaks; a red-panda twitter; a bamboo "tok" as each flume segment fills; wind in the groves; mahjong tiles clattering in the teahouse; a rare cub sneeze; a faint night-watch clapper every two hours; different bells for the day and night shifts.
- **One new animation worth paying for:** a roll or tumble for Inkpaws, or the red panda's arms-up stand.

### The two peoples as a relationship

On a feature list it reads badly today. The smaller, shorter-lived, faster-breeding people live in "tiny" roof lofts, arrive when housed, do the carrying and the treadwheel and the night shift, "so Inkpaws start the day with full shelves", perform "for off-duty Inkpaws", and keep the village running while the Inkpaws sleep through droughts. That is a servant caste. Shoulder poles on the couriers push it towards coolie imagery.

Fixes, in order:

1. Cut the Long Nap.
2. Frame Ringtails as the village's **Night Watch**, plus its astronomers and artists (Star Tower, lanterns, opera). The night watchman's clapper is authentic.
3. Arrival is an invitation, not a hire: a lantern lit in a high window.
4. Give both peoples the same lifespan, and call lofts "snug and high" with the same shelter values.
5. Show reciprocity: Ringtails take their leisure in the morning teahouse while Inkpaws work; cubs and kits share one kindergarten; Inkpaws cook what everyone eats.
6. Keep the treadwheel off the list of defining Ringtail jobs, or frame it as sport.
7. Text never says "helpers", "serve" or "for the Inkpaws"; say "the village".
8. The top monument shows both.
9. Do not give the two peoples different ethnic architectural codes (see section 6, flag 6).

### What is missing that panda players expect

- Visible bamboo eating.
- Rolling and clumsiness.
- Tree-climbing cubs.
- Panda names. The name pool is global, so this needs a small namer.
- A voice set.
- Dawn mist.
- A guided first-objectives checklist. The tutorial route in two-peoples.md §10 is untested and scheduled last; it should come at milestone 2.
- A showcase map.

---

## 5. Best ten additions or twists

| # | Idea | Cost | Why players love it |
|---|---|---|---|
| 1 | Off-duty flop: sit, sprawl, munch | Small code; optional prop | "Lazy pandas" is visible at minute 8 with no player action |
| 2 | A start that teaches itself: starter grove, raw cabbage, steamer shoots recipe, six-step objectives, one bundled map | Small code, data, map authoring | Removes the day-1 trap and makes the first flume eight tiles long |
| 3 | The bell handover staged: two bells, lantern wave, clock with sun and moon arcs | Small code, audio, emissive art | The signature clip, twice a day, for free |
| 4 | Tiered Festival from cycle 2 | Data; small code already planned | The main moment lands inside the first two hours and repeats |
| 5 | Lofts on stilts over the paths, with a ground ladder | Data and new art; needs prototype | No rooftop-and-stairs puzzle at the teaching moment; a distinctive skyline |
| 6 | Water-driven trip-hammer mill and paper maker | Probably data and new art; needs prototype | "Lead the water" becomes power as well as irrigation |
| 7 | Flowering as feast then famine: a large one-time seed harvest, budding one cycle ahead | Data, bud art; code already planned | A windfall people prepare for, not only a punishment |
| 8 | Drought trickle (Cistern Tap) and the staged return of water | Data, audio | The toolkit stays relevant in drought, and every drought ends with a show |
| 9 | Face-changing opera: Ringtails already have mask faces | New art; small code or building animation only | A Sichuan signature that suits red pandas exactly |
| 10 | Real reduplicated names with glosses; star names for Ringtails | Small code; native review | Charm on every click |

Runners-up: Ringtails run with their loads (data); a shared kindergarten (data); dawn mist particles on paddies and the hot spring (small code).

---

## 6. Names and wording

### Names to change

| Current | Problem | Suggested |
|---|---|---|
| Noria | Obscure, and an Arabic-derived word | Scoop Wheel (the Chinese bamboo-tube wheel) |
| Turning box / step / covered run | Unclear | Flume Corner / Flume Drop / Flume Bridge |
| Courier Loft, Scaffolders' Loft | "Loft" is also the home | Night Courier Post, Night Builders' Post |
| Forager's Nest | Does not signal Ringtails or night | Night Forager's Post |
| Hill Farm | Implies slope | Merge into Farmstead, or Dry-Field Farm |
| Bamboo rice | Reads as "rice cooked in bamboo" | Bamboo Seed, Bamboo Seed Cakes |
| Nap / Rest | Collide with Sleep | Lounging |
| Terrace Wall, Weir, Water Carrier | Hide known functions; "carrier" sounds like a job | Levee, Dam, Water Pump (a bamboo prefix is fine) |
| Cellar and Pickle Cellar | Two cellars | Pickle Jars or Pickle Yard |
| Woven Granary | Suggests grain only | Woven Storehouse |
| Tea Drier | Spelling; near "Drying Rack" | Tea Roastery |
| Paifang Gate | Opaque | Memorial Arch |
| Bamboo Spout | Does not say level control | Paddy Spout |
| "Welcome cubs" on lofts | Wrong word for the young | "Welcome kits" |

"Flume" is accurate. Use "bamboo aqueduct" in store text and in the first tooltip line.

### Key teaching messages

`[sun]` and `[moon]` stand for icons.

- **First bell (once).** "The work bell. Inkpaws work a short day and work it well. Afternoons are for hammocks, tea and company."
- **Hours raised past 12.** "Long days wear pandas out. Weary Inkpaws work slower than rested ones."
- **Status.** "Weary: no time to lounge. Works slower. Needs a free afternoon and a hammock."
- **Hours panel.** "Inkpaws work from dawn to this bell. Ringtails work from this bell to dawn."
- **Bamboo.** "Foragers pick its shoots. Woodcutters cut its poles. Thirsty: the first plant to wither in a drought."
- **Poles.** "Cut from bamboo; no mill needed. Light: a builder carries a whole bundle."
- **Flume.** "An open bamboo aqueduct. Water runs one way, along the arrow, level or downhill. It never climbs and never leaks."
- **Dry intake.** "No water can enter: the water here is lower than the flume. Raise it with a dam or lift it with a Scoop Wheel."
- **Bad bend.** "Flumes do not bend. Use a Flume Corner."
- **Spout.** "Keeps the field in front of it flooded to a set depth. Needs water at its back and walls around the field."
- **Tea dying.** "Roots too wet. Tea needs dry ground."
- **Den.** "Cubs arrive when this household is content (wellbeing 5 or more). Now: 3."
- **Loft.** "Home for Ringtails and their kits. Your first loft invites a Ringtail family to the village."
- **Arrival (modal, once).** "The Ringtails have come down from the trees. A lantern in a high window is an old invitation. Ringtails keep the night: they start when the Inkpaws' bell rings and stop at dawn. They work in buildings marked [moon]. They eat, drink and rest like everyone else. Build a Night Courier Post to give them their first job." Button: "Show me".
- **Closed by day.** "Closed for the day. Ringtails start at the afternoon bell."
- **No Ringtails free.** "No free Ringtails. Kits are raised in lofts."
- **Idle alert.** "3 Ringtails have no work. Ringtails work only in [moon] buildings."
- **Population panel.** "[sun] Inkpaws 14, 2 idle. [moon] Ringtails 6, 0 idle."
- **Flowering forecast.** "The river bamboo is budding. In 12 days it will flower, drop its seed and die. Cloud bamboo is not affected."
- **Festival Square.** "Lanterns 12/20. Feast dishes 30/30. Light the lanterns: both peoples take the night off."

---

## 7. Cultural flags

Ranked by risk.

1. **Fake Chinese writing.** AI-generated textures routinely produce gibberish characters. Rule: no script anywhere unless a native reader has proofread it. Scrolls show ink bamboo and paw prints.
2. **The Great Sitting Panda "after the Leshan Giant Buddha".** Swapping a panda for a sacred image can read as irreverent. Use no Buddhist iconography (hand gestures, lotus throne, attendants) and never say "Buddha" in public text; say "cliff carving". The original was built to calm a river confluence, so adding water at its feet is on theme.
3. **Japanese-coded items in a catalogue that forbids them.**
   - Bonsai: use penjing or "potted pine". Sichuan has its own school.
   - Stone lantern.
   - Fish-kite weathervane: reads as carp streamers. Use a bamboo pinwheel.
   - Headbands: use the cloth head-wrap of rural Sichuan.
   - "Paper screens": avoid the shoji grid; use Chinese lattice windows.
   - Persimmons hung on strings: dry them on round bamboo trays.
   - Never a bamboo deer-scarer on the water features.
4. **Labourer caricature.** Conical hats and shoulder poles on a small night-working people. Keep hats on paddy farmers only. Give couriers back-baskets, which are the everyday Sichuan carrier.
5. **Generic or Beijing "China".**
   - Hall of Harvests echoes the Temple of Heaven.
   - Courtyard House risks a Beijing courtyard; draw the Sichuan timber frame with white infill and grey tile.
   - Lacquer-red columns and upturned yellow roofs read as Chinatown.
   - Drum Tower is northern or Dong.
   - Better grounded: bamboo-grove farmsteads of the Chengdu plain; Dujiangyan's fish-mouth divider and bamboo-cage weirs for the dam re-theme; the bamboo rope bridge; Zigong's bamboo brine pipelines and tall wooden derricks for the Aquifer Drill; Zigong's lantern festival; the long-spout teapot pour; the Dujiangyan water-releasing ceremony as a model for the end of a drought.
6. **Do not code the two peoples as majority and minority.** Panda country is also Tibetan and Qiang country, and a Star Tower can drift into a Qiang watchtower. Use one architectural vocabulary for both peoples, differing in scale and height only.
7. **Food.**
   - Dumplings are generic northern. Sweet rice balls (tangyuan) from rice flour are a Chengdu snack and the Lantern Festival food.
   - Tofu, if kept, should be mapo tofu.
   - Bamboo mushrooms are a real Sichuan hot-pot delicacy and should stay.
8. **Smaller points.**
   - Avoid yin-yang as the emblem, the stock "oriental riff" in music, kung-fu jokes and accented text.
   - The Flowering reflects real panda deaths, so keep the tone bittersweet.
   - Keep jokes about slow panda breeding gentle.
   - Generated names must be real words checked by a native speaker.
