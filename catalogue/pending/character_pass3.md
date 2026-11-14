# Staged, not adopted: character pass 3 (docs/tech/ringtail-body.md 8)

Waiting for the coordinator's word after the character lane's runs rb-p3a / rb-p3b. The catalogue does not read this
folder. To adopt, make these edits, regenerate, and take the build through the install gate.

1. `catalogue/faction.toml` `[characters.bot]`:
   `models = { "Model_Preserved" = "Characters/Pandaborn/WoodenOx.Model" }`
2. `tools/pandaborn.ps1` `$meshes`:
   `'Characters\Pandaborn\WoodenOx.Model.timbermesh' = Join-Path $RingtailMeshSource 'WoodenOx.Model.timbermesh'`
   (source `E:\PandabornDev\build\characters\out`).
3. `tools/pandaborn.ps1` `-BundleDirs` += `E:\PandabornDev\build\characters\attachments` (bundle `pandabornattachments`
   `_win` and `_mac`; the validator already accepts the name).
4. `catalogue/faction.toml` `[characters.adult]` and `[characters.ringtail_adult]`, `add`:
   `TemplateAttachmentsSpec` is on the basis, so use `set` on the whole list or a generator `append` (to write):
   `{ AttachmentId = "PandabornConicalHat", Prefab = "Characters/Pandaborn/Attachments/ConicalHat", Parent = "#Head",
   Position/Rotation zero, Scale one, CreateInstantly = false }` and the same for `PandabornBackBasket` on `#Backpack`.
5. Outfits: the Inkpaw `Farmer` outfit (copied from Folktails) gets `Attachments += "PandabornConicalHat"`; the Inkpaw and
   Ringtail `Gatherer` outfits get `Attachments += "PandabornBackBasket"` (the copy step needs a per-outfit `set` or
   `append`, to write).
6. Ringtail fur masks are already in `mod/` (`Characters/Pandaborn/RingtailAdult|RingtailChild.Model.FurMask.png`).
