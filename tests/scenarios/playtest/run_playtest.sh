#!/bin/bash
# Queue one playtest scenario through tools/run_game_test.ps1 and record what was played:
#   tests/scenarios/playtest/run_playtest.sh <scenario> <faction> <mode> <days> <run id>
# The git commit and the generator report are snapshotted when the game starts (the content lane changes the installed
# build under us), into <run>/playtest_meta/. Then the report tool writes <run>/playtest/verdict.md and charts.
set -u
SCEN=$1; FACTION=$2; MODE=$3; DAYS=$4; RUN=$5
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT=/e/PandabornDev/build/test/$RUN
cd "$REPO"
# real-time cap: about 60 s a game day at speed 30 for a growing colony, plus loading
SECS=$(( DAYS * 75 + 300 ))
(
  # snapshot once the run's folder appears (that is when the game is launched, after the queue)
  until [ -f "$OUT/request.json" ] || [ -f "$OUT/harness.log" ]; do sleep 5; done
  mkdir -p "$OUT/playtest_meta"
  git -C "$REPO" rev-parse HEAD > "$OUT/playtest_meta/commit.txt"
  git -C "$REPO" status --short catalogue src/gen > "$OUT/playtest_meta/catalogue_dirty.txt"
  cp /e/PandabornDev/build/gen/PandabornFactions.report.json "$OUT/playtest_meta/" 2>/dev/null
  cp "$REPO/catalogue/building_stats.toml" "$OUT/playtest_meta/" 2>/dev/null
) &
SNAP=$!
powershell -ExecutionPolicy Bypass -File tools/run_game_test.ps1 -Faction "$FACTION" -Map "${MAP:-Plains}" -GameMode "$MODE" \
  -InGameDays "$DAYS" -RunSeconds "$SECS" -TimeoutSeconds $(( SECS + 600 )) -WaitForGameSeconds 10800 -NoBatchControl \
  -OnlyMods JigglyPanda.PandabornFactions -RequestJson "tests/scenarios/playtest/$SCEN.json" -RunId "$RUN" \
  > "/e/PandabornDev/build/test/$RUN.console.txt" 2>&1
CODE=$?
kill $SNAP 2>/dev/null
/e/PandabornDev/tools/venv/Scripts/python.exe -I tools/playtest_report.py "$OUT" > /dev/null 2>&1
echo "exit $CODE"
