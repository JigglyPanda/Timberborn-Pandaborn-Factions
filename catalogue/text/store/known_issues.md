# Known issues and compatibility

Draft, written by an AI (Claude), 2026-11-25. The long form behind the "Works with, and known issues" section of
the store pages and the README.

**Where this comes from.** Two sources, kept apart below:

1. Runs of the game recorded in the technical notes (`docs/tech/`). These are facts.
2. The compatibility audit, `docs/reviews/2026-11-25-mod-compatibility.md`. It read the code of this mod, of the
   game and of every mod on the author's machine. **It ran no game.** Its findings are marked there as certain,
   likely or unverified; this page keeps those words.

**The rule for the store page:** a line may say "tested" only after a run of the complete build shows it. An
earlier clean run beside 35 other mods (`docs/tech/look.md`) predates the Ringtails, the water toolkit, the
festival and the flowering. It does not count, and no page says "tested with" because of it.

## The four things every player should be told

* **Use one copy only.** A Workshop copy plus a manual copy of this mod stops the game at start when TimberUi is
  installed, and TImprove and Choo!Choo! both need TimberUi. (Seen in game: `docs/tech/stage0.md`, run `fd-dup-2`.
  TimberUi does this for any mod enabled twice.)
* **Removing the mod breaks Inkpaws saves.** A game played as the Inkpaws needs the mod to load. Folktails and
  Iron Teeth saves are not affected.
* **After a Timberborn update, wait for this mod's update before loading an Inkpaws save.** Most of the mod
  switches a broken feature off and carries on. Three things cannot: a vanilla file the faction changes that
  disappears, a part of a copied vanilla building that is renamed, or the mod's own data definitions failing to
  load. Any of those stops Inkpaws games until the mod is updated. Other factions stay fine. (Audit, M5: certain.)
* **It changes nothing for Folktails or Iron Teeth**, and adding it to an existing game is safe.

## Proven in game

### Pandaborn - Panda Reskin

Source: `docs/tech/ringtail-body.md` sections 8.1 and 8.3.

* With the released Reskin 7.0.0 and this mod together, nothing breaks (run `rb-p3a`: no errors, save and
  reload included).
* The Reskin treats the Inkpaws as an unknown modded faction. It replaces the Inkpaws' coat list with its own
  Folktails panda coats, which are the same files, so the coats look right. It replaces the faction's
  **portraits** with its Folktails ones.
* Ringtails keep their own coats and portraits. They get the Reskin's fur in the giant panda's pattern (longer
  on the ears than on the head).
* Wooden Oxen get no fur.
* With the Reskin on, Folktails and Iron Teeth are pandas too. That is the Reskin's purpose, not an effect of
  this mod.
* **The fix** is a small Reskin update (one file): the Inkpaws keep their own coats and portraits, and a body
  may bring its own fur pattern, which the Ringtails do. It is written and tested (run `rb-p3b`) and not yet
  published. It should go out the same day as this mod.

Store sentence if the Reskin update is out: "Pandaborn - Panda Reskin: works. Update it too, so the Inkpaws keep
their own portraits and the Ringtails get their own fur."
Store sentence if it is not: "Pandaborn - Panda Reskin: works. Until its next update it shows its own portraits
for the Inkpaws and gives Ringtails giant-panda fur."

### Two copies of the mod

Source: `docs/tech/stage0.md`, "Duplicate copies".

* The game loads both copies when a local folder and a Workshop item carry the same mod.
* Without TimberUi this mod copes by itself: the first copy runs, the second parks its asset bundles in a
  folder `AssetBundles.parked` and stays quiet, and the player gets one notice saying which copy runs (run
  `fd-dup-3`).
* With TimberUi the game stops at start (run `fd-dup-2`).

### The Inkpaws' look and Folktails materials

Source: `docs/tech/look.md`. The look is applied in code and the faction keeps listing the Folktails material
collection, so mods that add Folktails materials keep loading in Inkpaws games. If the look's asset bundle is
missing, the faction looks like Folktails and nothing else changes.

### TimberCommons and the flumes

Source: `docs/tech/water.md`, run W2. The flumes, the spout and the Scoop Wheel behaved the same with
TimberCommons enabled and disabled.

### Mac

Source: `docs/tech/mac.md`.

* Every asset bundle has a Mac twin, built for macOS on Windows and checked there: the right platform, the
  same assets as the Windows file, Metal shaders, no build errors.
* **Nobody has run the mod on a Mac.** Until someone does, Mac is untested. The note lists what a tester should
  check: the game starts, plants show their leaves, the look applies, windows glow at night, a second load
  works, other factions look vanilla, performance holds.
* The plants have no fallback. If the plant bundle failed to load on a Mac, an Inkpaws game would not start.
  That is the first thing a tester should try.

## From the audit (read from code, no game run)

### Not tested yet: say so

| Mods | Why it matters | Audit |
|---|---|---|
| **T3MP, Performance Plus** | They rewrite the game's tick loop, needs, bonuses, water tasks, plant caches and walking, which this mod's features run inside. Spot checks found no clash; three areas were not read through (flowering, water, festival needs) | M2, unverified. First thing to test |
| **Other faction mods** | Expected to live side by side: no id of ours collides. One open risk: a mod that ships its own tutorial could stop Inkpaws games from loading, because the game builds every tutorial for a faction that has one | Section 4 and M6, likely; no such mod was installed |
| **Moddable Tool Groups with the Inkpaws tutorial** | It redirects the tutorial's toolbar lookups | m4, unverified |

### Certain or likely

| What a player sees | Why | Audit |
|---|---|---|
| **Building packs are not offered to the Inkpaws**: Staircase, Ladder, More Platforms, Path Extention, Water Extention, Extended Floodgates, Flywheels, Ferris Wheel, Food Stall, The Barkimedes Screw, the 4-way District Center. They keep working for Folktails and Iron Teeth | Those mods list their buildings per faction, and the game reads only the lists of the faction being played. Nothing crashes. An author can add the Inkpaws with one small file (below) | M1, certain |
| Choo!Choo! is available to the Inkpaws, and its stations and wagons take on the Inkpaws' look | It gives unknown factions its default set, and uses Folktails material names | M1, m8, likely |
| A mod that changes a vanilla building (more zipline connections, bigger storage) does not change the Inkpaws' version of it | The Inkpaws' buildings are their own copies | m2, certain |
| With Ferris Wheel installed, Inkpaws show a "Ferris Wheel" need they cannot meet. It costs the last 4 points of well-being and nothing else | That mod puts its need in the list every faction shares | m1, certain |
| MoreGroups keeps Inkpaws buildings in the main toolbar groups, not in its sub-menus | It sorts by template name | m3, likely |
| CustomTools' Levee+, Platform+ and Path+ tools are missing for Inkpaws | Its own faction list | m5, certain |
| Automation and Simple Floodgate Triggers work on Inkpaws floodgates and pumps, and on the Scoop Wheel, Treadwheel Lift and Cistern Tap. They cannot control the Flume Gate | They attach by component; the Flume Gate is not a floodgate | m9, certain |
| TimberCommons' discharge settings do not appear on the Inkpaws' Discharge or Cistern Tap | Hardcoded vanilla names | m7, certain |
| TImprove's all-day light removes night visuals: no lantern glow | Its own feature | m11, certain |
| The 4-way District Center changes the starting building of Folktails and Iron Teeth only | Its faction files | m12, certain |
| Mod Settings is not used | The Great Flowering is set per save, in the game | m14, certain |

### For mod authors: offering a building pack to the Inkpaws

Add one collection file to your mod, the same kind you already write for Folktails, Iron Teeth or Emberpelts,
with the collection id `Buildings.Inkpaws`. Your `.Folktails` templates work as they are.

`TemplateCollections/TemplateCollection.YourMod.Buildings.Inkpaws.blueprint.json`:

```json
{
  "TemplateCollectionSpec": {
    "CollectionId": "Buildings.Inkpaws",
    "Blueprints#append": [
      "Buildings/YourMod/YourBuilding/YourBuilding.Folktails.blueprint"
    ]
  }
}
```

* Give the file a name of your own. Collections join by `CollectionId`, not by path.
* Paths are relative to your mod's root and end in `.blueprint`, without `.json`.
* The Inkpaws list the Folktails material collection, so Folktails models and materials render. In an Inkpaws
  game they take on the Inkpaws' look.
* These goods exist for the Inkpaws, so costs in them work: Log, Plank (shown as Poles), Gear, Metal Block,
  Scrap Metal, Treated Plank (shown as Cured poles), Explosives. A cost or recipe in any other Folktails good
  needs checking against `docs/CONTENT.md`.
* The file is harmless when this mod is absent: no faction then reads that collection.
* Read from the game's code and from how other packs add Emberpelts. **Not yet run with a real pack.**

## Switching one part of the mod off, and reporting a problem

Source: `src/code/Pandaborn.Bootstrap/Bootstrap.cs` (`PlayerSwitch`), added 2026-11-25. **Not yet run in a game.**

* A text file `PandabornFactions.txt` in the game's own folder (the one that holds `Saves` and `Mods`; on Windows
  `Documents\Timberborn`) with a line such as `off: Flowering` or `off: Water, Festival`. `#` starts a note. Letter
  case does not matter. Read once when the game starts.
* Names: Bell, Names, Look, Words, Water, Ringtails, RingtailsFallback, Tutorial, Festival, Flowering. What each
  one turns off is in the README, "Switching one part of the mod off".
* In an Inkpaws game a notice names what is switched off in the file.
* For a bug report, ask for `Player.log`, or at least the line that starts `[Pandaborn] built for game version`:
  it names the game version the mod was built for and the one that is running.

## Other known issues

| Issue | Source |
|---|---|
| The festival's rising lanterns are drawn with the game's firework trails until their own art is finished | `docs/tech/events.md`, "The look of the festival" |
| When the water feature is switched off under a save that had water standing in a flume, that water is pushed out next to the flume once | `docs/tech/water.md`, run W2 |
| A rice field one block below its path needs stairs, or the farmers never reach it | `docs/tech/water.md`, run W1 |
| Ringtails use the giant pandas' voice when selected, and panda voices are off altogether until the owner has heard them | `docs/tech/sound.md` section 10 |
| Coats change after loading a save. The game picks a coat again on every load, for every faction | `CLAUDE.md` |
| With the panda-words feature off, the population tab says "Beaver adult" and "Beaver child" | `docs/tech/stage0.md` |
| The mod's own text is English, with a Simplified Chinese translation made by AI and not yet read by a native speaker. In other languages those texts show in English | commit `de8d249` |
