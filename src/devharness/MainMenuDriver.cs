using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Bindito.Core;
using Newtonsoft.Json.Linq;
using Timberborn.CoreUI;
using Timberborn.FactionSystem;
using Timberborn.GameSceneLoading;
using Timberborn.MainMenuPanels;
using Timberborn.MapRepositorySystem;
using Timberborn.Modding;
using Timberborn.NewGameConfigurationSystem;
using Timberborn.SingletonSystem;
using UnityEngine;
using UnityEngine.UIElements;

namespace PandabornDevHarness
{
    [Context("MainMenu")]
    public class MainMenuHarnessConfigurator : Configurator
    {
        protected override void Configure()
        {
            if (!Harness.Active) return;   // no request: bind nothing at all
            Bind<MainMenuDriver>().AsSingleton();
        }
    }

    /// <summary>
    /// Starts the requested new game from the main menu without any input. Optionally first opens the new-game faction
    /// panel and takes a screen capture with each faction selected. With loadSave the game itself loads the save given
    /// on the command line (-saveName/-settlementName), so nothing is started here.
    /// </summary>
    public class MainMenuDriver : ILoadableSingleton, IUpdatableSingleton
    {
        private const float DelaySeconds = 2f;
        private const float PanelSettleSeconds = 1.5f;

        private readonly GameSceneLoader _gameSceneLoader;
        private readonly MapRepository _mapRepository;
        private readonly GameModeSpecService _gameModeSpecService;
        private readonly FactionSpecService _factionSpecService;
        private readonly ModRepository _modRepository;
        private readonly PanelStack _panelStack;
        private readonly NewGameFactionPanel _newGameFactionPanel;
        private float _startAt;
        private int _panelStep = -1;   // -1 not started; 0..n-1 faction being shown; n done
        private float _panelWaitUntil;
        private bool _panelPushed;
        private bool _captureDue;

        public MainMenuDriver(GameSceneLoader gameSceneLoader, MapRepository mapRepository, GameModeSpecService gameModeSpecService,
                              FactionSpecService factionSpecService, ModRepository modRepository, PanelStack panelStack,
                              NewGameFactionPanel newGameFactionPanel)
        {
            _panelStack = panelStack;
            _newGameFactionPanel = newGameFactionPanel;
            _gameSceneLoader = gameSceneLoader;
            _mapRepository = mapRepository;
            _gameModeSpecService = gameModeSpecService;
            _factionSpecService = factionSpecService;
            _modRepository = modRepository;
        }

        public void Load()
        {
            _startAt = Time.unscaledTime + DelaySeconds;
            Harness.ApplyRuntimeSettings();
            Harness.ApplyWindow();
            try { RecordEnvironment(); }
            catch (Exception e) { Harness.Error("recording the environment failed", e); }
        }

        public void UpdateSingleton()
        {
            if (Harness.GameRequested || Harness.Finished) return;
            Harness.ApplyRuntimeSettings();
            if (Time.unscaledTime < _startAt) return;
            if (Harness.Request.LoadSave)
            {
                // the game's AutoStarter loads the save from the command line; just wait for the game scene
                Harness.GameRequested = true;
                Harness.Result["newGame"] = new JObject { ["loadSave"] = true, ["commandLine"] = string.Join(" ", Environment.GetCommandLineArgs()) };
                Harness.Info("waiting for the save given on the command line to load");
                return;
            }
            if (Harness.Request.FactionPanelShots && _panelStep != int.MaxValue && !FactionPanelDone()) return;
            Harness.GameRequested = true;
            try { StartGame(); }
            catch (Exception e)
            {
                Harness.Error("starting the new game failed", e);
                Harness.Finish("error");
            }
        }

        /// <summary>
        /// Steps through the new-game faction panel: push it, then per faction select it, let it settle, capture the screen.
        /// Returns true when finished (the panel is popped again). Uses the panel's private members (dev-only harness).
        /// </summary>
        private bool FactionPanelDone()
        {
            float now = Time.unscaledTime;
            if (now < _panelWaitUntil) return false;
            try
            {
                const BindingFlags flags = BindingFlags.Instance | BindingFlags.NonPublic;
                var specsField = typeof(NewGameFactionPanel).GetField("_factionSpecs", flags);
                var listField = typeof(NewGameFactionPanel).GetField("_factionList", flags);
                var select = typeof(NewGameFactionPanel).GetMethod("SelectFaction", flags);
                if (specsField == null || listField == null || select == null) throw new MissingMemberException("NewGameFactionPanel internals changed");
                var specs = ((IEnumerable<FactionSpec>)specsField.GetValue(_newGameFactionPanel)).ToList();
                if (_panelStep < 0)
                {
                    _panelStack.HideAndPush(_newGameFactionPanel);
                    _panelPushed = true;
                    Harness.Result["factionPanel"] = new JArray();
                    _panelStep = 0;
                    _captureDue = false;
                }
                else if (_captureDue)
                {
                    var spec = specs[_panelStep];
                    string file = Path.Combine(Harness.OutputDir, "factionPanel_" + spec.Id + ".png");
                    ScreenCapture.CaptureScreenshot(file);
                    ((JArray)Harness.Result["factionPanel"]).Add(new JObject
                    {
                        ["faction"] = spec.Id,
                        ["order"] = spec.Order,
                        ["displayName"] = spec.DisplayName.Value,
                        ["description"] = spec.Description.Value,
                        ["logo"] = spec.Logo.Path,
                        ["logoSize"] = SpriteSize(spec.Logo.Asset),
                        ["newGameFullAvatar"] = spec.NewGameFullAvatar.Path,
                        ["newGameFullAvatarSize"] = SpriteSize(spec.NewGameFullAvatar.Asset),
                        ["file"] = Path.GetFileName(file)
                    });
                    Harness.RecordScreenshot("factionPanel_" + spec.Id, "screen", Path.GetFileName(file), new JObject { ["faction"] = spec.Id }, null);
                    Harness.Info("screenshot factionPanel_" + spec.Id + " -> " + file);
                    _captureDue = false;
                    _panelWaitUntil = now + 0.7f;
                    return false;
                }
                else _panelStep++;
                if (_panelStep < specs.Count)
                {
                    var list = (VisualElement)listField.GetValue(_newGameFactionPanel);
                    select.Invoke(_newGameFactionPanel, new object[] { specs[_panelStep], list[_panelStep], false });
                    _captureDue = true;
                    _panelWaitUntil = now + PanelSettleSeconds;
                    return false;
                }
            }
            catch (Exception e)
            {
                Harness.Error("faction panel screenshots failed", e);
            }
            if (_panelPushed) { _panelStack.Pop(_newGameFactionPanel); _panelPushed = false; }
            _panelStep = int.MaxValue;
            return true;
        }

        private static string SpriteSize(Sprite sprite)
        {
            return sprite ? (int)sprite.rect.width + "x" + (int)sprite.rect.height : null;
        }

        private void RecordEnvironment()
        {
            var mods = new JArray();
            foreach (var mod in _modRepository.EnabledMods)
                mods.Add(new JObject
                {
                    ["name"] = mod.Manifest.Name,
                    ["id"] = mod.Manifest.Id,
                    ["version"] = mod.Manifest.Version.Full,
                    ["source"] = mod.ModDirectory.DisplaySource,
                    ["path"] = mod.ModDirectory.Path
                });
            Harness.Result["mods"] = mods;
            Harness.Result["factionsAvailable"] = new JArray(_factionSpecService.Factions.Select(f => (object)f.Id).ToArray());
            Harness.Result["mapsAvailable"] = new JObject
            {
                ["builtin"] = new JArray(_mapRepository.GetBuiltinMapNames().Cast<object>().ToArray()),
                ["user"] = new JArray(_mapRepository.GetUserMapNames().Cast<object>().ToArray())
            };
            Harness.Result["gameModesAvailable"] = new JArray(_gameModeSpecService.GetSpecsOrdered().Select(m => (object)ModeName(m)).ToArray());
            Harness.WriteResult("running");
        }

        private void StartGame()
        {
            var request = Harness.Request;
            var faction = _factionSpecService.Factions.FirstOrDefault(f => string.Equals(f.Id, request.Faction, StringComparison.OrdinalIgnoreCase));
            if (faction == null)
            {
                Harness.Error("unknown faction '" + request.Faction + "'; available: " + string.Join(", ", _factionSpecService.Factions.Select(f => f.Id)));
                Harness.Finish("error");
                return;
            }
            var map = ResolveMap(request.Map);
            var mode = ResolveGameMode(request.GameMode);
            Harness.Result["newGame"] = new JObject
            {
                ["faction"] = faction.Id,
                ["map"] = map.Name,
                ["mapIsResource"] = map.Resource,
                ["gameMode"] = ModeName(mode),
                ["settlementName"] = request.SettlementName
            };
            Harness.Info("starting new game: " + faction.Id + " on " + map.Name + " (" + ModeName(mode) + ") as " + request.SettlementName);
            Harness.WriteResult("running");
            _gameSceneLoader.StartNewGame(new NewGameConfiguration(faction.Id, map, mode, request.SettlementName));
        }

        private MapFileReference ResolveMap(string wanted)
        {
            if (!string.IsNullOrEmpty(wanted) && wanted.EndsWith(".timber", StringComparison.OrdinalIgnoreCase) && File.Exists(wanted))
                return MapFileReference.FromDisk(wanted);
            var builtin = _mapRepository.GetBuiltinMapNames().ToList();
            var user = _mapRepository.GetUserMapNames().ToList();
            string match = Match(builtin, wanted);
            if (match != null) return MapFileReference.FromResource(match);
            match = Match(user, wanted);
            if (match != null) return MapFileReference.FromUserFolder(match);
            string fallback = builtin.Contains("Diorama") ? "Diorama" : builtin.First();
            Harness.Warn("map '" + wanted + "' not found, using " + fallback + "; builtin maps: " + string.Join(", ", builtin));
            return MapFileReference.FromResource(fallback);
        }

        private static string Match(List<string> names, string wanted)
        {
            if (string.IsNullOrEmpty(wanted)) return null;
            return names.FirstOrDefault(n => n == wanted)
                   ?? names.FirstOrDefault(n => string.Equals(n, wanted, StringComparison.OrdinalIgnoreCase))
                   ?? names.FirstOrDefault(n => n.IndexOf(wanted, StringComparison.OrdinalIgnoreCase) >= 0);
        }

        private GameModeSpec ResolveGameMode(string wanted)
        {
            var modes = _gameModeSpecService.GetSpecsOrdered();
            if (!string.IsNullOrEmpty(wanted))
            {
                foreach (var mode in modes)
                    if (ModeName(mode).IndexOf(wanted, StringComparison.OrdinalIgnoreCase) >= 0
                        || (mode.DisplayNameLocKey ?? "").EndsWith("." + wanted, StringComparison.OrdinalIgnoreCase))
                        return mode;
                Harness.Warn("game mode '" + wanted + "' not found, using the default");
            }
            return _gameModeSpecService.GetDefaultSpec();
        }

        private static string ModeName(GameModeSpec mode)
        {
            return mode.Blueprint != null ? mode.Blueprint.Name : mode.DisplayNameLocKey;
        }
    }
}
