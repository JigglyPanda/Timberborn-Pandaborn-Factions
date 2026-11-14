# Pandaborn - Factions: design

Status: direction approved by the owner 2026-11-14. Numbers are placeholders until the balance pass.
Items marked **bet** need a prototype before they are promised to players.

The test for every idea in here: *would a player enjoy this, and would they notice it within a minute?*

## Decisions made by the owner

* One faction, the **Inkpaws**. Red pandas (**Ringtails**) live in it alongside giant pandas.
* Core identity: **lead the water** rather than hold it back.
* Two peoples the player can balance: a few big pandas, or many small quick red pandas. The owner likes
  different working hours for the two, and requires the system to be smooth to learn; if a prototype shows it
  is not, fall back to one people with coat variety.
* Signature events are in scope.
* Art volume about what Emberpelts ships. All art is generated in code / by AI and disclosed.
* The faction is unlocked from the start.
* Tone: cozy and whimsical.
* Reach: Steam Workshop and mod.io; Windows and Mac.
* The Reskin is a head start on the look, not a constraint on design or method.
* Development is as autonomous as possible.

## The one-sentence pitch

Beavers hold water back; the Inkpaws lead it — two panda peoples who share one village, guide mountain water
through bamboo pipes into rice terraces, and would rather feast and nap than hurry.

## Setting

The misty bamboo highlands of Sichuan, where giant and red pandas really live. One real place, used closely:

| Real thing | In the mod |
|---|---|
| Dujiangyan, a 2,200-year-old irrigation system that waters a plain with no dam | The water philosophy |
| Rice terraces, hill tea, Sichuan pepper | Three-zone farming |
| Bamboo mass flowering and die-off, which really starves pandas | The Great Flowering |
| The Wooden Ox, a walking hauler from Sichuan legend | The faction's bots |
| The sky lantern, credited by legend to the same inventor | The wonder and the festival |
| Panda nurseries | The Kindergarten |
| Red pandas being active at dusk and night | Ringtails work the night shift |

Same world as vanilla: the pandas are another people who outlived the humans.

## What players should feel

* **First minute:** "These are pandas, and they play differently." Two body sizes on screen, bamboo going in
  the ground, a conical hat on a farmer.
* **First hour:** "I'm not building a dam, I'm building a hillside." Water arrives through something the player
  built and can watch.
* **Every cycle:** a reason to look forward (festival, cubs, a new dish) and a reason to prepare (drought,
  flowering).
* **Always:** nothing happens to the player without warning, and every hardship has more than one answer.

## Pillar 1 — Two peoples, one village

### The rule a player has to learn

**Inkpaws work the day. Ringtails work the night.**

That is the whole system. Everything else is either automatic or optional.

### Why it is built this way

The owner's concern (2026-11-14): two species could be a steep learning curve that turns players off. Learning
one new thing is fun; learning a system from scratch is tedious. So the design follows four rules:

1. **One idea at a time.** The game opens with Inkpaws only and plays like a familiar faction with new crops.
   Ringtails arrive later, when the player chooses.
2. **Nothing to configure.** Both peoples can work in every workplace. They take turns: a day crew and a night
   crew, staffed automatically.
3. **Ignoring it still works.** A player who never builds a loft has a complete, slower, single-people colony.
4. **Depth is found, not taught.** The stat differences reward attention but never demand it.

Earlier drafts had a three-way toggle on every workplace, jobs restricted to one people, and extreme stats.
Those are cut: each was another rule to memorise.

### How the Ringtails arrive

The first **loft** the player builds — a small home on a rooftop or scaffold, lit by a lantern — draws a family
of Ringtails down from the high forest. A short message introduces them and the one rule. From then on they
breed in lofts. The player picks the moment, so the new idea lands when they are ready for it.

### What changes when they arrive

* **Buildings stop sleeping.** Every workplace gains a night crew, so the same kitchens, mills and farms produce
  around the clock. This is the impact: a visible jump in output from buildings the player already owns.
* **Day makes, night moves.** Inkpaws are strong and slow, so they shine at standing still and producing.
  Ringtails are quick and light, so they shine at hauling, gathering and delivering. The felt result: queue
  buildings in the evening, and by morning the materials are on site and the stores are sorted.
* **Dusk and dawn are shared hours.** Both peoples are awake, the teahouse is full, and festivals happen at
  dusk. The two crews pass each other on the paths.
* **The village is lit.** Lanterns come on at night, and Ringtails enjoy lantern-lit paths.

### The two peoples

| | Inkpaws (giant pandas) | Ringtails (red pandas) |
|---|---|---|
| Hours | Day | Night |
| Body | Big: strong, slow walkers | Small: quick, light |
| Appetite | Hearty | Light eaters and drinkers |
| Homes | Dens on the ground | Lofts on roofs, scaffolds and groves |
| Lives | Long; one cub at a time, only when content | Shorter; litters |
| Naturally best at | Producing in one place | Anything made of walking |

The differences are moderate, not extreme. A player never needs the numbers; the interface shows a sun or a
moon and a big or small paw.

### The player's levers, in the order they are met

1. **Housing sets the mix.** More dens, more Inkpaws; more lofts, more Ringtails.
2. **Optional: day only / night only / both** on a workplace, for players who want to tune. The default is both.
3. **The Long Nap (bet).** In a drought the player can send the Inkpaws to bed. Sleeping Inkpaws need far less
   food and water, and the light-eating Ringtails keep the village ticking at night. It turns the big eaters'
   weakness into a choice, and it is the moment the two peoples most obviously need each other.

### How it is taught

* A short Inkpaws tutorial, a handful of steps, if the game's tutorial system allows custom ones.
* One message when the Ringtails arrive, one at the first drought (the Long Nap), one at the first Flowering
  forecast. No walls of text.
* The population panel shows the two crews side by side, with idle workers per shift.

### If it does not work

Judged by a prototype against the first-hour test, in this order of fallback:

1. Shared workplaces with automatic day and night crews (the design above).
2. Each workplace set to one people by a simple toggle with a sensible default, as vanilla does for bots.
3. One people only, with Ringtail coats as visual variety and no mechanical difference.

### Open questions for the prototype

* Two crews on one workplace: the game assumes one kind of worker per workplace.
* A second adult character type needs its own spawner; the vanilla one assumes a single adult template.
* Night work and day sleep for one people, including leisure and beds.
* Per-people appetite and stats.

## Pillar 2 — Lead the water

Inkpaws still have terrace walls and a simple weir, so any vanilla map is playable from day one. What they add
is a toolkit that suits what they grow — shallow water at many heights, with dry ground kept dry.

| Tool | What it does | Why it is fun |
|---|---|---|
| Bamboo pipeline (**bet**) | Carries water from an intake to an outlet at the same height or lower, on the ground or on trestles; no power | A contraption the player draws across the hillside and watches fill |
| Noria | Sits in a current and lifts water a few levels with no workers | A machine that runs on the river itself |
| Treadwheel lift | The same lift where there is no current, turned by an Inkpaw | A panda on a wheel |
| Bamboo spout | Holds the pool below it at a set shallow depth | Paddies that look after themselves |
| Mist catcher | Collects a trickle of water from the air, even in drought | A lifeline with no river |
| Clay cistern | Stores water | The plain answer to the first drought |
| Charcoal filter | Passes clean water and strips a little badwater, burning bamboo charcoal | An active, costed answer to badtides |

Rules that keep pipes pleasant: fixed flow per pipe, clear arrows when placing, no pressure or mixing puzzles,
and they connect to vanilla valves and sensors.

## Pillar 3 — Every kind of land has a use

To a beaver, dry land is dead land. Inkpaws farm three zones, so the player reads the map differently from the
first minute and wasteland becomes an asset.

| Zone | Crops |
|---|---|
| Flooded (ankle-deep) | Rice, lotus |
| Moist | Bamboo, cabbage, soybean |
| Dry, near irrigation but not on it | Tea, Sichuan pepper |
| Trees | Mulberry (paper), persimmon |

### Bamboo

* One plant, two harvests: shoots (food) and poles (light building material).
* It spreads into empty moist soil by itself. It never takes over fields, paths or buildings, and anything
  outside the marked grove is harvested as a bonus. Spreading is a gift, not a chore.
* The thirstiest plant in the game and the first to brown in a drought, but it regrows from its roots when
  water returns. No replanting.
* Two kinds: river bamboo (fast, lowland) and cloud bamboo (slower, hardier). This matters in the Flowering.
* Balance guard: poles replace planks in light construction only. Logs still come from trees.

## Pillar 4 — Contentment is the engine

* **Bamboo keeps them alive; cooking makes them thrive.** Raw shoots are nearly free but fill little. Each
  dish is a recognisable Sichuan food and a step up the wellbeing ladder.
* **Inkpaws only have cubs when content.** Happiness has a visible reward the player cares about.
* **Cubs give joy.** Adults gain wellbeing from the Kindergarten, so children are a pleasure, not only mouths.
* **Naps.** Hammocks and nap platforms near workplaces are a leisure need. Pandas flopped in hammocks at midday
  is the image people will share.
* **Tea stretches water.** One measure of water brews more than one serving, which gives tea a real job in a
  drought.

| Leisure | Building |
|---|---|
| Nap | Hammock, nap platform |
| Tea | Teahouse |
| Feasting | Dumpling kitchen, hot pot hall |
| Play | Slide, swing, climbing frame |
| Cub-watching | Panda Kindergarten |
| Performance | Opera stage, run by Ringtails |
| Beauty | Lantern garden, ink-painting studio, hot spring bath |

## Pillar 5 — A third rhythm

### The Great Flowering

* Every fourth or fifth cycle, one of the two bamboo kinds blooms and dies across the map. It is forecast, like
  a drought.
* The hillsides turn gold. Pandas gain wellbeing from the blossoms while the player counts the food.
* Counterplay, all of it visible in advance: grow both kinds of bamboo, lean on rice and persimmons, stock
  pickles and dried goods.
* The payoff: the dead groves yield **bamboo rice**, the rarest food in the mod and the centrepiece of the best
  festival feast.
* Groves return from their roots afterwards.

### Lantern Festival

* Called by the player, at most once per cycle, by spending stockpiled lanterns, fireworks and feast food.
* At night the village dances, lanterns rise and fireworks go off.
* Rewards: a long-lasting festive wellbeing boost, a wave of cubs, and one step of **Tradition**, a permanent
  count that unlocks lantern colours and decorations.

## Pillar 6 — Legend as late game

* **Wooden Oxen** replace bots: slow, tireless haulers that carry enormous loads.
* **Kite windmills**, rigged by Ringtails, replace fuel engines.
* **Bamboo scaffolding, stairs and rope bridges** make tall building cheap and light.
* **The wonder** is a colossal sky lantern that carries seeds out over the wasteland. On completion the sky
  fills with lanterns.

## The first hour

| When | What the player does | What they learn |
|---|---|---|
| Day 1 | Starts with Inkpaws only, berries and water. Places a forager's post, a water carrier and a bamboo plot | Bamboo grows fast; otherwise familiar |
| Days 2–4 | First shoots. The grove creeps along the bank. Builds dens | Spreading is free food |
| Days 5–10 | Clay cisterns and a weir before the first drought. Bamboo browns, then recovers by itself | Droughts are survivable; groves forgive |
| Days 10–20 | First spout-fed paddy and a tea slope on dry ground. First kitchen. Builds a loft when ready: Ringtails arrive and the village works at night | Three zones; cooking lifts wellbeing; the one rule of two peoples |
| Days 20–40 | First pipeline to a higher terrace. Cubs arrive once Inkpaws are content. Paper and lanterns | Leading water; happiness pays |
| Around day 40 | First Lantern Festival | A moment worth a screenshot |
| Later | First Flowering forecast; Wooden Oxen; kites; the sky lantern | The long game |

The first ten days must work with one obvious crop and no pipes.

## Look

* Palette: ink black and white, bamboo green, lacquer red, paper cream, tea green.
* Buildings from one code-driven kit of parts — poles, lashings, woven panels, curved tile roofs, paper
  screens, lanterns — so dozens of buildings share a style.
* Lanterns and paper windows glow at night.
* Faction outfits: conical bamboo hats, straw capes, headbands.
* Characters: keep the Reskin's proportions and coats. Give the faction its own character material so faces and
  fur are no longer bound to the beaver's surface maps (**bet**). Give Ringtails a true red panda body — smaller,
  slim, long ringed tail (**bet**; a scaled Inkpaw body with the red coat is the fallback).

## Draft content list

| Area | Content |
|---|---|
| Raw food | Bamboo shoots, persimmons, lotus root |
| Cooked food | Steamed rice, shoot dumplings, mapo tofu, pickled cabbage, hot pot, dried persimmon cakes, bamboo rice cakes |
| Drink | Tea |
| Materials | Bamboo poles, paper, bamboo charcoal, lacquer, clay roof tiles |
| Festival goods | Paper lanterns, fireworks |
| Power | Noria, bamboo water wheel, treadwheel, kite windmill |
| Storage | Woven granary, clay cistern, pickle cellar |
| Housing | Den, courtyard house, stilt house; rooftop loft, scaffold loft, grove nest |
| Science | Scroll library |

## What sinks faction mods (design against these)

1. Breaking on game updates. Keep it data-first, keep code small and defensive, keep an automated load test.
2. Dependency chains. Ship with none required.
3. Id clashes with other factions. Prefix everything.
4. Brutal or opaque starts.
5. Reusing a vanilla faction's look, emblem or text.
6. Side effects outside the faction.

## Milestones

| # | Goal | Proves |
|---|---|---|
| 0 | Spike: faction loads with its own panda bodies and vanilla buildings; beavers untouched | Faction registration, faction-only body, automated in-game test |
| 1 | Prototypes of the bets: day and night crews sharing workplaces, bamboo pipeline, own character material | Whether the headline ideas are buildable and smooth to learn |
| 2 | Playable core: bamboo, rice, tea, kitchens, housing for both peoples, text, portraits | The first hour |
| 3 | Its own look: building kit, materials, outfits, night lighting | Art pipeline, Unity bundles, Mac build |
| 4 | Events, Wooden Oxen, wonder | The long game |
| 5 | Release: balance on every difficulty, Workshop and mod.io pages | — |

## Quality bar for every milestone

* The automated test starts a new Inkpaws game, runs it, and finds no exceptions in the log.
* A Folktails game with the mod enabled is unchanged.
* Works with the Reskin installed and without it.
* Works with no other mods installed.

## Candidate changes for the next revision

Written 2026-11-14 after the water and two-peoples studies. None of this is adopted until it has been checked
against `docs/tech/game-mechanics.md` and survived the critic rounds.

### Two peoples: Ringtails as the night folk

* The story everyone already knows: while the big ones sleep, the little helpers tidy the workshop.
* Ringtails staff **their own** small buildings — courier loft, forager's nest, dew nets, star tower, lantern and
  firework workshops — and sleep through the morning. Inkpaws staff everything else by day.
* A day has three acts: morning (Inkpaws alone, working from what was stocked overnight), afternoon (both awake,
  couriers supplying workshops live), night (Ringtails restock, deliver building materials, clear outputs,
  forage, craft and stargaze).
* It is strictly additive. Inkpaws still fetch their own supplies as beavers do, so a colony with no Ringtails,
  or with too few, slows down but never stalls. Inkpaw workshops get roomier input shelves so a night's
  restocking lasts the morning.
* Ringtails carry full loads on shoulder poles: fast walkers with normal capacity, so they are better haulers
  than beavers, not worse.
* No two crews in one workplace and no switching at dusk. The study found a workplace can only ever hold one
  kind of worker, and the switching scheduler is the largest and most fragile piece of code in the plan.
* Later option: let the player hand other workplaces to Ringtails.

### Water and seasons: every season has its harvest

* The pipeline becomes an open **bamboo flume**: one tile wide, one-way, level or downhill, with turning boxes
  at corners. Water is visible running along it.
* Drought stops being dead time. The wet season is for rice and bamboo; in the dry season the same terraces
  can carry fast dry-ground crops, and permanent tea bushes sit on slopes that are always dry. The longer the
  drought, the bigger the dry harvest.
* Bamboo and groves brown in drought and spring back, so the Inkpaw drought is restful: fill cisterns and the
  pantry, nap, and let the land sleep. No giant reservoir needed just to keep fields alive.
* Dry-ground crops must stay luxuries and ingredients, never staple calories, because dry land is unlimited.
* The treadwheel lift is a Ringtail job (its power follows walking speed). The mist catcher becomes a dawn
  dew collector. The charcoal filter is postponed.

### Bamboo as a fast tree

* Bamboo reuses three jobs players already know: a forester plants it, a gatherer picks shoots, a woodcutter
  cuts poles. Groves left unmarked spread, as wild trees do.
* Poles are the Inkpaws' planks and need no mill, which makes the opening smoother than vanilla. The price is
  that the supply browns in drought and dies in a Flowering, so poles must be stockpiled.
* Bamboo mushrooms grow in standing groves and are foraged by Ringtails.

### Population the player can trust

* Inkpaws breed slowly and only when content, and each den has a "welcome cubs" switch. Runaway population is a
  well-known vanilla frustration; here it cannot happen by accident.

### Look

* Test whether a faction-only material set can reuse vanilla material names. If it can, every vanilla building
  model is re-themed for the Inkpaws at no modelling cost, and new models are spent on signature buildings.

### Events

* The Great Flowering never comes before a set cycle, is forecast, and has an off / rare / normal setting.
