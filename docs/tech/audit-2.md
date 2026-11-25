# Second independent audit of Pandaborn - Factions

2026-11-25. Written by an independent reviewer (an AI agent) that changed no other file. The first audit was on
2026-11-14 at commit 45dab79; its findings and the decisions on them are in `docs/DESIGN.md`.

## What was reviewed

- **Start commit:** 804fff1. **Data re-checked at:** db71ebd, the last catalogue commit at the time (edee84b after it
  only added docs).
- **Generation:** the shared `build\gen` folder was stale (14 Nov 12:32, before Water, Festival and Flowering were
  switched on). db71ebd was generated into `E:\PandabornDev\build\scratch\audit2`, with all modules on and with each of
  Water, Festival, Flowering and Ringtails off.
- **Assembled build:** `build\stage5\stage` is the 804fff1 data; the release validator was run on it read-only.
- **Working tree:** the catalogue, text and code lanes were editing during the review. Flagged items were re-read once;
  line numbers in edited files are working-tree lines of that moment.
- **Not done:** no game run. Module behaviour comes from the tech docs and code, not from play.

## Top ten, in the order a player meets them

| # | When | Finding | Evidence | Fix | Owner |
|---|---|---|---|---|---|
| 1 | Minute 1 | The tutorial teaches the lumberjack after "Have 20 bamboo shoots". A colony starts with no logs, so a player who follows it places a pump and a Farmhouse that never get built, and the chain never advances. Vanilla teaches Wood first. | `catalogue/tutorial.toml:24-32` (stage list :27, FirstShoots :77, Lumberjack :82) | Put lumberjack and mark-trees straight after Basics. Take "Have 20 shoots" out of the chain. | catalogue |
| 2 | Day 2-4 | The tutorial asks for a Steamer (40 science) and no stage teaches the Inventor. The step shows a locked button. Vanilla has a Science tutorial; ours switches it off. | `tutorial.toml:39-42, 101`; `building_stats.toml:73` | Add an Inventor stage before Cooking, or make the Steamer free. | catalogue |
| 3 | First drought | Nothing teaches storing water. The pump no longer hides a 146-water tank (decided; landing at `rules.toml:54`), so the first drought is now as hard as vanilla. | No cistern stage in `tutorial.toml`; the hard playtest lost 8 of 13 to thirst | Add a stage: Small Cistern plus "have N water". | catalogue |
| 4 | Day 5+ | Tea is taught right after the bell, ahead of flumes (order 55 against 60). It needs 400 science, brown ground and tea no earlier than day 12. The decision moved tea to cycle 2. Whether the game holds Flumes behind an unfinished Tea tutorial is unverified. | `tutorial.toml:49-58` | Flumes first; Tea after it. | catalogue |
| 5 | First drought | "Foresters replant dead trees by default" has no implementation. Dead tea, pepper and persimmon stay dead, because nobody cuts them. Already listed in `docs/CONTENT.md:285` with no owner. | `docs/DESIGN.md:120`; `buildings.toml:41`; `Forester.ReplantDeadTrees` is runtime-only | A few lines of code setting it on new Inkpaw foresters. | code |
| 6 | Day 10+ | Slide and Swing only works standing in water at least 0.2 deep (inherited from the Lido). The text now says "by the water", which reads as beside it. | `buildings.toml:166`; `text/buildings.json:664` | Say "must stand in shallow water", or drop the water spec. | text or catalogue |
| 7 | Mid game | Ringtails can die out for good. The family arrives once per save, and kits need a living Ringtail adult in the district. | `RingtailService.cs:162`; `MoonLoft.cs:171` | Invite a new family when a district has open night jobs and no Ringtails. | code |
| 8 | Day 30+ | Late science is still inventors only: 1 point per worker-hour against 122,910 to unlock everything. The Star Tower decision has not landed; it is blocked because the first Moon Loft would unlock it free. As a Ringtail post it also makes late science depend on Ringtails, against DESIGN.md:181. | `buildings.toml:119-124` (the lane's own note); `rules.toml:38` | Add the unlock field. Rule on whether a one-people colony gets second-tier science. | code, then owner |
| 9 | Cycle 6 | Bamboo seed is useless without a Kitchen and a Trip-Hammer Mill. With Water off the seed has no use at all. The forecast only says "store food". | `goods.toml:121`; `recipes.toml:59`; `plants.toml:116, 125` | A Steamer recipe for seed, or say what the seed needs in the forecast. Make the seed wait for Water too. | catalogue, text |
| 10 | Any time | The build with every module on has never run assembled. There is no gate file, and the installed build has no Water, Festival or Flowering. The catalogue Trip-Hammer Mill, night building, badwater shut-off and the generated tutorial are unplayed. | No `*.gate.json` under `E:\PandabornDev\build`; installed `Modules\modules.txt` | One gate run on the real stage, then install. | coordinator |

## First-review findings

| Finding | Status | Evidence |
|---|---|---|
| Code shipped with no data switching it on | Fixed in data; not gated or installed | `rules.toml` [modules]; item 10 |
| 23 buildings whose text lied | Fixed by the hidden-until-wired rule; three text fixes were uncommitted (below) | Validator: 0 unmet needs, 0 unused goods |
| Poles from one fragile source | Fixed | `buildings.toml:45`; timber bamboo `dry_days = 10` |
| Tea and pepper in the farm list | Fixed | `plants.toml`: `planter = "Forester"`, gathered |
| Two tea needs | Fixed | One need; tea has no consumption effect |
| Wonder reward fading in three days | Fixed | `needs.toml`: `daily_delta = -0.01` |
| Roof-only Nap Platform | Fixed | Generated blueprint: ground or stackable |
| Bath and wall needing dirt | Fixed in data; the wall's moisture block is not shown in game | Bath uses water; wall costs 4 logs, 2 poles |
| Exploit-priced stand-ins | Mostly fixed | Goldfish Bowl and Moon Gate still cost a Shrub's 12 logs for +2 wellbeing each |
| No tutorial | Partly fixed | Nine tutorials exist; items 1-4; never played |
| Toolbar clashes | Fixed | No shared slot in any group |
| Wellbeing below Folktails | Overshot (94 against 84); trims decided, landing | `needs.toml` diff |
| Folktails decals and bot avatar | Fixed | 10 banners, 4 tails, own bot avatar |
| Text inconsistencies | Partly fixed | "Farmstead" against "Efficient Farmhouse" (`CONTENT.md:287`) |

## Decided on 25 November: check it landed

All of these were uncommitted edits in the working tree at the time of the review, not in db71ebd.

- Flumes cost 0 science, gate 40, scoop wheel 60.
- Pump shelves back to vanilla size.
- Wellbeing trims and the pickle recipe.
- Wooden Ox price.
- Opera Stage as an ordinary attraction.
- Flat bell taper.
- **Not landed:** the Star Tower (item 8).
- **Not seen:** the Ringtails' own rested bonus. No code change for it was in the tree.

Three lies found at db71ebd were already corrected in the working tree:

- the Smoke Kiln said "no power" and needed 250 hp;
- the Cistern Tap said "no workers" and has one;
- the Dew Collector promised crowding the code does not have.

## Other new findings

**Major**

- **The data-only build cannot be generated.** `generate --no-code` fails: "modifier BellMovementSpeedCap (waits for
  Bell)" is not in `ids.lock.json` (`modifiers.toml:7`). Owner: catalogue.
- **Poles are about three times cheaper than planks.** Timber bamboo gives 0.4 poles per tile-day at 0.75 worker-hours
  each, with no power. Birch through a mill gives 0.14 at 2.25 hours. The balance lane flagged it; no decision is
  recorded. Owner: owner.
- **Tradition stops at level 3**, after three festivals. Level 2's Hanging Lantern meets the same need at the same cost
  as the Standing Lantern (`buildings.toml:184`). Owner: catalogue.

**Minor**

- Dew Collector yields 2 water a day (0.7 in drought); a pump worker makes about 48 (`recipes.toml:134`).
- Potted Pine duplicates the Shrub. Pine resin is gathered and nothing uses it.
- The flowering plants' names and descriptions are defined twice with different wording
  (`enUS_PandabornPlants.csv:14, 25` and `enUS_PandabornEvents.csv:48-53`).
- `text/tutorial.json:28` says steamed shoots "fill better"; both give the same hunger. The truth is one shoot makes
  two.
- `catalogue/text/messages.json` (52 KB of teaching text) feeds nothing.
- Flume Bridge Span has no icon and shows the valve's.
- From the docs, not checked by the reviewer: the top-bar job count leaves Ringtails out, festival lanterns are vanilla
  comets, and Flowering buds cannot be seen.

## Economy

Every tier is reachable from berries and water. No cost needs a good that only comes later; science is the only gate.
Every good type has storage.

| Build | Hidden | What is left odd |
|---|---|---|
| All on | Star Tower | Pine resin unused |
| Water off | 13 water buildings, Kitchen, rice flour, rice balls, seed cakes, Flumes tutorial | Bamboo seed has no use; persimmons raw only |
| Festival off | Square, both festive needs | Goldfish Bowl and Moon Gate free at 12 logs |
| Flowering off | Flowering plants, seed, seed cakes | Nothing |
| Ringtails off | Loft, three posts, toolbar group, tutorial | No second-tier science |

Food, water and labour are arithmetic from the blueprint numbers at 60% working time, not measured. A colonist needs
2.67 food and 2.12 water a day. Under the decided flat taper, output is the same at any day length from 12 to 16 hours.

| Colonists | Shoot tiles (steamed) | Farmers, cooks, pump workers | Share of adults | With 30% Ringtails |
|---|---|---|---|---|
| 20 | 40 | 2, 1, 2 | about 30% | not computed |
| 50 | 100 | 5, 2, 3 | about 25% | about 36% |
| 100 | 200 | 9, 3, 3 | about 19% | about 27% |

Ringtails eat like Inkpaws and grow no staple food, so the Inkpaw share doing food and water rises.

## First hour as the data offers it

1. **Minutes 1-10:** a veteran ignores the tutorial and is fine. A newcomer stalls (item 1).
2. **Day 1-2:** Pole Mill plus Power Wheel works with no science.
3. **Day 3-5:** first shoots; the Steamer step is locked (item 2). The Hammock and the bell step follow and are sound;
   the bell also has a one-time message from day 3.
4. **Day 5-10:** the flume lesson is two short stages, and the science costs that delayed it are being removed.
5. **First drought:** untaught (item 3).
6. **Ringtails:** one tutorial stage plus an arrival message.
7. **Festival, Flowering, rice, Kitchen, Oxen:** no tutorial. Each relies on its panel and description. The Festival
   Square panel and the Flowering forecast are specific enough; the rice paddy is not.

## Fallbacks

- **Hidden at build time:** nothing left lies.
- **Shipped but failing its API check at run time:** buildings stay in the toolbar with their texts. A flume is a solid
  block, and night posts employ Inkpaws under "Employs Ringtail…". Only a Core notice explains it.
- **Ringtails module off for one load:** Ringtails become Inkpaws permanently; the arrival flag stays set.

## Rules and release

- **Rules:** clean. No game files or binaries in git, every id scoped, no vanilla loc key or asset path overridden.
- **Validator:** `--release` on stage5 gives 0 errors.
- **`package` would refuse (at the time of the review):** the Festival API list in
  `src/code/Pandaborn.Festival/FEATURE.md` was uncommitted.
- **Mac:** all four bundles have `_mac` twins.
- **Manifest:** version 0.0.1; the description still says flumes and the festival "come in later versions"
  (`manifest.json:3, 6`).
- **Store and licence:** README was untracked, there is no licence file, and the store drafts are marked unpublished and
  describe the pre-balance design. AI disclosure is present in all of them.

## Enjoyment

**Likely to delight**

- A grove along a flume in the first week.
- The bell with pandas visibly napping.
- The Ringtail family's arrival and lit night work.
- The festival day.
- Hot pot as a real cooking goal.

**Likely to annoy** (fixes are in the tables above unless given here)

- Items 1-9.
- The bell is set once and forgotten.
- Science crawl after day 50, with nothing new after Tradition 3. Fix: cosmetic rewards beyond level 3.
- A festival that halts worker-turned power.
- A Flowering that only takes.

**After day 50** the goals are the Great Sitting Panda (15,000 science) and the Sky Lantern (20,000), which at inventor
speed is mostly waiting.

**The wonder** is a re-themed Earth Recultivator with its own model, sound and image. Whether its launch has been played
is not stated in anything the reviewer read.

## Must still be done

**No game run needed**

- Tutorial order, an Inventor stage, a water stage (items 1-4).
- Commit the balance edits; lock the `BellMovementSpeedCap` id.
- Forester default, Ringtail re-invite, Star Tower unlock field.
- A use for bamboo seed.
- Slide and Swing wording.
- Duplicate loc keys.
- Manifest, licence, store text.
- A ruling on pole cost and on science without Ringtails.

**Game runs needed**

- The gate on the full assembled build, then install.
- The generated tutorial played from a new game.
- The catalogue Trip-Hammer Mill.
- Night builders at night.
- Badwater shut-off and dew under the module.
- A first drought with vanilla-sized pump shelves.
- A festival with a real pump crew.
- The wonder launch.
- A Folktails game after an Inkpaws game on the final build.
