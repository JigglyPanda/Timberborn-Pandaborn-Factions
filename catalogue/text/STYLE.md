# Writing for the Inkpaws: voice and rules

For anyone who adds or changes player-facing English text. The rules were derived by reading the game's own
English files (`enUS.csv`, 2,143 keys, game 1.1.2.8) next to `docs/DESIGN.md` revision 4. Written by an AI and
not yet reviewed by the owner.

The text itself is in the JSON files beside this page: `buildings.json`, `goods.json`, `plants.json`,
`needs.json`, `faction.json`, `tutorial.json`, `names.json`, and the store pages in `store/`. Panel lines, statuses and
notifications are written with the code and live in `src/code/Pandaborn.*/mod/Localizations/enUS_*.csv`; the same
rules apply there.

## Who reads it

English-speaking Timberborn players, and many more who read the English through machine translation. A new
key in a mod exists in English only. So:

* Write short, whole sentences with the subject stated. "Raise the water with a dam", not "Raise it".
* No idioms, no puns, no rhymes, no wordplay that depends on English spelling or sound.
* One term per thing (see the glossary). A translator, human or machine, will give two English words two
  different translations.
* **Keep a vanilla key whenever its words are true and do not mention beavers.** Vanilla text is already
  translated into every language the game ships. A replacement is English-only. This is why most re-themed
  buildings in `buildings.json` have `null` for their strings.

## The vanilla voice, by kind of text

| Kind | Vanilla key | How vanilla writes it | Example |
|---|---|---|---|
| Building name | `Building.<Id>.DisplayName` | Title Case. One to three words. A plain noun for what it is. Sizes go in front: Small, Medium, Large, Double, Triple. Trades take a possessive | `Water Pump`, `Builders' Hut`, `Large Warehouse` |
| Building description | `Building.<Id>.Description` | One sentence, sometimes two. 4 to 20 words (median 51 characters, nine in ten under 100, longest 154). A verb with no subject for things that work ("Pumps…", "Employs…", "Stores…"), or a noun phrase for places ("A place to…"). States the one constraint a player must know. Ends with a full stop | `Blocks water up to an adjustable height.` |
| Building flavor | `Building.<Id>.FlavorDescription` | One line, rarely over 20 words. Dry. A deadpan fact about how the colonists behave, or a short quote with an em dash and a name and no space after the dash | `They used to be tied to trees, until a few too many tree cutting accidents.` |
| Good | `Good.<Id>.DisplayName`, `.PluralDisplayName` | Sentence case: only the first word is capitalized. Singular and plural. Mass nouns repeat the word. No description | `Maple pastry` / `Maple pastries`, `Wheat flour` / `Wheat flour` |
| Plant | `NaturalResource.<Id>.DisplayName`, `.FlavorDescription` | Title Case. Flavor only; the description field exists but vanilla leaves it empty. Soil rules are keyword lines | `Chestnut Tree` |
| Keyword line | `Buildings.GroundOnly`, `NaturalResources.Arid`, `Work.BeaverOnly` | `<YellowHighlight>Keyword:</YellowHighlight>` then one sentence | `<YellowHighlight>Arid:</YellowHighlight> Must be placed on dry terrain.` |
| Need | `Need.<Id>.DisplayName` | A food need shows the good's plural name. An attraction need shows the building's name. Only Hunger and Thirst carry more (a death fragment and a one-word status) | `Bread`, `Campfire`, `Wet fur` |
| Status, long | `Status.<System>.<Problem>` | A sentence in the object's panel. Says what is wrong and, where it helps, what to do. Full stop | `Building needs power to operate. Connect it to a generator.` |
| Status, short | `Status.<System>.<Problem>.Short` | The alert at the screen edge. Two to four words, sentence case, no full stop | `Building lacks power` |
| Notification | various | A bare fact, usually without a full stop | `Drought started`, `{0} was born!` |
| Tutorial | `Tutorial.<Section>.<Stage>` | One to three short paragraphs with a blank line between: why, what to do, then an optional `Tip:`. Says "let's". Capitalizes building and good names | `Beavers need a stable source of Logs. Duh.` |
| Loading tip | `Tip.Game.<Id>` | Starts with `Tip:`. One sentence, key term in yellow | |
| Faction blurb | `Faction.<Id>.Description` | Two or three sentences, then a new line: `Their motto: <i>…</i>` | |
| Game over | `Faction.<Id>.GameOver.Message`, `.Flavor` | Message: one sentence, then "This is the end." Flavor: one line, a moral or an image | |
| Wonder | `Faction.<Id>.WonderCompletionMessage`, `.Flavor` | Message opens with "Congratulations!" and ends "…to build the faction's wonder." Flavor: two or three sentences in the past tense | |

Other habits worth copying:

* US spelling: center, color, flavor, neighbor. "Well-being" has a hyphen.
* Parameters are `{0}`, `{1}`. A label with a value is `Label: {0}`.
* Numbers that the game already prints (growth days, drought resistance, capacity, cost, recipe amounts) are
  not repeated in prose. Neither is any number the catalogue can change (hours, percentages, days of an effect): a
  text with a parameter shows the live value, and a text without one uses words.
* Exclamation marks appear almost only inside quotes and in "{0} was born!".

## Tone

Vanilla is dry, warm and lightly witty. It is never cute on purpose. The joke is nearly always that small
animals take engineering very seriously. For the Inkpaws the joke is that they take rest very seriously, and
it is told the same way: **by observation, not by adjectives.**

* Yes: "When the bell rings, the hammer goes down. The nail can wait until morning."
* Yes: "The slide is for the young. The queue is mostly adults."
* No: "adorable", "fluffy friends", "sleepy little pandas", baby-talk, sound effects, exclamation marks.
* A flavor line states something the player could watch happen, then stops.
* The Great Flowering is bittersweet. It reflects something that really kills pandas. No jokes in its text.

## Standards for this faction

* **The two peoples are equals.** The Ringtails are the village's Night Watch, its stargazers and its artists.
  Never write helpers, servants, serve, little ones, or "for the Inkpaws". Say "the village". Text a player can read
  before building a Moon Loft does not mention Ringtails, apart from the faction description. Ringtail homes
  are "snug", never "tiny".
* **One real place: Sichuan.** Nothing Japanese-coded. Never "oriental". No religious words: the Great Sitting
  Panda is a "cliff carving" of a seated panda and nothing else. No jokes about accents, kung fu or the zodiac.
* **No Chinese characters in game text.** They appear only in the checking column of `names.json`.
* **Every description is true to the mechanics.** If the stat sheet has no number, describe the effect without
  one. If you cannot find the behaviour in the catalogue or the code, cut the sentence. Nothing in the toolbar lies.
* **Vanilla functions keep vanilla names.** A player should never relearn a levee.

## Glossary

One name per thing and one word per job: [GLOSSARY.md](GLOSSARY.md). It is also the brief for translators. The
short of it: **Inkpaws** and **Ringtails** are the two peoples, **panda** is anyone of either people (never
"villager"), **the afternoon bell** divides the day, a **night post** is a Ringtail workplace, the Inkpaws build with
**poles**, and the farm is the **Farmhouse**.

## The cast

Vanilla flavor leans on four recurring beavers (Ma' Ngonel, Ol' Kazko, Pina, Suli). Their quotes read wrongly
in a panda village, so every re-themed building that quoted one has a new line.

The Inkpaw text does not need a cast to work: no line in the JSON files depends on one. If later text wants
quotes, use these four and no others, so they become familiar. All four names are in `names.json` and wait on
the same native check.

| Name | Who | Speaks about |
|---|---|---|
| Granny Nuo Nuo | An Inkpaw elder and cook | Food, cubs, the right way to do things |
| Old Song Song | An Inkpaw who lays flumes | Water, patience, slopes |
| Hua Jiao | A Ringtail, captain of the Night Watch | The night, speed, getting things finished |
| Dou Dou | An Inkpaw cub | Questions |

Attribution follows vanilla: the quote in double quotes, an em dash, the name, no space after the dash.
Sayings are attributed to the village ("—Village saying"), never to one people.

## Keys and files

* Loc keys begin with `Pandaborn` (`docs/ENGINEERING.md`). Each JSON file records the vanilla key pattern its
  strings correspond to and a suggested mod key.
* A mod key equal to a vanilla key replaces the vanilla text for **every** faction. Never write Inkpaw words to
  a vanilla key. The shared vanilla lines that say "beaver" are swapped for Inkpaws games only by the Words table
  (`src/code/Pandaborn.Words/words.review.enUS.txt`).
* The game's CSV validator rejects an empty line, a fourth column, and a quote next to a comma with a space
  between them. Paragraph breaks inside a text are fine; a blank line between rows is not.
* `[sun]` and `[moon]` in a text stand for the day and night icons. A line must still read correctly without
  them.

## Before you add a line

1. Is there a vanilla key that already says it truthfully? Use it.
2. Does it say what the thing does before it says anything else?
3. Is every claim in it true in the build, or marked `confirm`?
4. Would it survive machine translation word for word?
5. Does it use the glossary's term?
6. If it is flavor: could a player watch it happen? Is it one line?
