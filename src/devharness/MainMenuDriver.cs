using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Bindito.Core;
using Newtonsoft.Json.Linq;
using Timberborn.FactionSystem;
using Timberborn.GameSceneLoading;
using Timberborn.MapRepositorySystem;
using Timberborn.Modding;
using Timberborn.NewGameConfigurationSystem;
using Timberborn.SingletonSystem;
using UnityEngine;

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

    /// <summary>Starts the requested new game from the main menu without any input.</summary>
    public class MainMenuDriver : ILoadableSingleton, IUpdatableSingleton
    {
        private const float DelaySeconds = 2f;

        private readonly GameSceneLoader _gameSceneLoader;
        private readonly MapRepository _mapRepository;
        private readonly GameModeSpecService _gameModeSpecService;
        private readonly FactionSpecService _factionSpecService;
        private readonly ModRepository _modRepository;
        private float _startAt;

        public MainMenuDriver(GameSceneLoader gameSceneLoader, MapRepository mapRepository, GameModeSpecService gameModeSpecService,
                              FactionSpecService factionSpecService, ModRepository modRepository)
        {
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
            Harness.GameRequested = true;
            try { StartGame(); }
            catch (Exception e)
            {
                Harness.Error("starting the new game failed", e);
                Harness.Finish("error");
            }
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
