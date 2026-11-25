# Changelog

All notable changes to Pandaborn - Factions.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions are the `Version` in
`mod/PandabornFactions/manifest.json`. Ids never change between versions (`catalogue/ids.lock.json`), so a
newer version loads an older version's saves.

Nothing has been published yet. The manifest says `0.0.1`, which is the development build.

## [Unreleased]

Proposed as **0.1.0, the first public release, early access**. The owner decides the number; the reasons for
this proposal are at the end of this file.

What the first release contains, by the state of each part on 2026-11-25. "Proven" means a run of the game
showed it; the runs are named in `docs/tech/`. The path from here to a release is `docs/RELEASE.md`.

### Added: proven in game, in the installed build

- The Inkpaws, a playable faction of giant pandas, unlocked from the start. Own bodies for adults and cubs, five
  adult and three cub coats, portraits, banners and tail marks. Folktails and Iron Teeth are unchanged with the
  mod enabled.
- The Inkpaws' own building list: the Folktails' staples in the Inkpaws' look, and nearly sixty buildings of
  the faction's own, almost all on new models.
- The look: dark timber, pale plaster, grey clay tile, bamboo, lattice windows and lanterns that glow at night.
  Applied in code to Inkpaws games only.
- The afternoon bell: rested Inkpaws work and walk faster on a shorter working day. The bonus multiplies with
  well-being, is fixed each dawn and is shown on the working-hours panel. A bell rings at the end of the day and
  at dawn.
- Poles in place of planks: timber bamboo yields poles when cut, and a Pole Mill splits logs.
- Seven plants on three kinds of land: shoot bamboo, timber bamboo, cabbage, rice, tea, Sichuan pepper,
  persimmon.
- Dishes: steamed shoots, pickles, steamed rice, hot pot. Tea, roasted and served at the Teahouse.
- Afternoon places: Hammock, Nap Platform, Teahouse, Slide and Swing, Kindergarten, Ink Studio, Hot Spring Bath.
- The Ringtails: a red panda family moves in when the first Moon Loft is finished. Night Builders' Post, Night
  Courier Post, Night Gatherers' Post. Kits are raised while night jobs are open. Their own body, coats, names,
  outfits, population row and clock arc.
- Colonist names with their meaning, and panda words in the interface, in Inkpaws games only.
- Conical hats for farmers and back-baskets for gatherers.
- Wooden Oxen, the faction's bots, on their own body.
- 32 sounds made for the faction. They load and play in tests; nobody has listened to them.
- Safe fallbacks: each code feature checks the game before loading and switches itself off, with a notice, if
  the game changed under it.

### Added: switched on, proven on test copies, not yet through the install gate

- The water toolkit: Flume, Flume Corner, Flume Drop, Flume Bridge, Flume Bridge Span, Flume Gate with its
  badwater shut-off, Paddy Spout, Scoop Wheel, Cistern Tap, Dew Collector.
- The Lantern Festival: called from the Festival Square, a day and a night off, dancing on the square,
  fireworks at a Grand Festival, festive spirit for everyone, and Tradition, which unlocks decorations.
- The Great Flowering: announced a cycle ahead; one bamboo flowers, bears seed and rests; a setting per save
  for normal, rare or off.

### Added: in testing

- Trip-Hammer Mill, rice flour, sweet rice balls and bamboo seed cakes. The mill has not run with a worker in a
  game.
- Treadwheel Lift, on a stand-in model.
- Dry-Stone Wall.
- Opera Stage, as an ordinary attraction on a stand-in model.
- The Inkpaws tutorial.
- Ox Workshop, Memorial Arch, Great Sitting Panda and the Sky Lantern as played content. They are placed and
  finished in tests; no test has reached them by playing.
- Mac asset bundles. Built and checked on Windows; never run on a Mac.

### Changed on 2026-11-25, with no game run behind it yet

Balance decisions recorded in `docs/DESIGN.md` and `docs/tech/balance.md`:

- The bell's bonus tapers hour by hour, so the work done is the same at any day length from twelve to sixteen
  hours.
- Water pumps hold a plain-game stock again. Workshops with ingredients still hold about three working days.
- Flumes cost no science; the Flume Gate and the Scoop Wheel cost less.
- Well-being trimmed for several afternoon needs and monuments; pickles, bamboo seed cakes and the Wooden Ox
  recipe changed.
- Tea no longer claims to quench thirst.

Decided the same day and not in the catalogue or the code when this was written:

- Ringtails rested by the length of their own night shift.
- The Star Tower as a Ringtail night post that makes science.
- A new Ringtail family answers the lantern if a district loses its last Ringtail.
- Bamboo seed can be steamed into seed cakes without a mill.

### Not in this version

- The Star Tower (hidden until its data ships).
- Panda voices for selected colonists. Made, and off until the owner has heard them.
- The festival's own rising-lantern art. The game's firework trails stand in.
- Translations. The faction's own text is English only.

### Known issues

See `catalogue/text/store/known_issues.md`.

## [0.0.1]

Development builds, 2026-11-13 to 2026-11-25. Never published. The history is in git.

---

## Why 0.1.0 and not 1.0.0

The proposal is to publish first as `0.1.0` and call it early access on the store pages.

For 1.0.0:

- The faction is whole on paper: every building from the first den to the wonder exists, on its own model.
- Ids are frozen, so a 1.0 save would keep loading.

For 0.x, and deciding it:

- **The build that would ship has never been run.** Water, Festival and Flowering are switched on in the
  catalogue and were proven one at a time on test copies. No staged build with everything on has passed the
  install gate.
- **None of the release tests has been run on that build** (`docs/ENGINEERING.md`, "Tests required before a
  release"): no three-day game per difficulty, no twenty-day soak that passed on Hard, no run with other mods
  since four features were added.
- **Balance moved on the day this was written**, with no game run behind the new numbers.
- **Nobody has played it.** Every proof is a scripted run. The owner has not seen the art by day and night,
  heard the sounds or read the text in game.
- **Mac has never been run**, and the store pages promise Mac.
- **Parts are missing or standing in:** the Star Tower, the rising-lantern art, two stand-in models, panda
  voices, a native speaker's check of the names.

A 0.x number says the true thing: play it, and expect the numbers to move. `1.0.0` should mean that
`docs/RELEASE.md` is green from top to bottom, the Star Tower is in, a Mac tester has reported, and one round of
players' reports has been answered. If the owner wants to signal "nearly there" instead, `0.9.0` says that; it
would be fair only after the install gate and the release soak have passed.
