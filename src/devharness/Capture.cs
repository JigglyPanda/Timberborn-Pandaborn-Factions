using System;
using System.IO;
using UnityEngine;

namespace PandabornDevHarness
{
    /// <summary>Off-screen rendering to PNG. Independent of the game camera's zoom limits and of the UI.</summary>
    public static class Capture
    {
        /// <summary>Renders what the given camera sees (same pose and settings) to a PNG.</summary>
        public static void RenderView(Camera source, int width, int height, string path)
        {
            var texture = Render(source, width, height, null, null, null);
            Save(texture, path);
        }

        /// <summary>
        /// Lifts the model high above the map for one render so nothing blocks the view, takes a front 3/4 and a back 3/4
        /// view side by side, and puts the model back. The caller picks a subject whose body renderer is visible.
        /// </summary>
        public static void RenderStudio(Camera source, Transform model, Renderer body, int cell, string path)
        {
            var bounds = body.bounds;
            float height = Mathf.Clamp(bounds.size.y, 0.25f, 2.5f);
            var savedPosition = model.position;
            var savedRotation = model.rotation;
            var lift = new Vector3(0f, 80f, 0f);
            var sheet = new Texture2D(cell * 2, cell, TextureFormat.RGBA32, false);
            try
            {
                model.position = savedPosition + lift;
                var focus = new Vector3(bounds.center.x, bounds.min.y + height * 0.5f, bounds.center.z) + lift;
                var views = new[] { new Vector3(0.55f, 0.3f, 1f), new Vector3(-0.7f, 0.35f, -1f) };
                for (int v = 0; v < views.Length; v++)
                {
                    var direction = savedRotation * views[v].normalized;
                    var position = focus + direction * (height * 3.6f);
                    var rotation = Quaternion.LookRotation(focus - position, Vector3.up);
                    var cellTexture = Render(source, cell, cell, position, rotation, new Color(0.36f, 0.42f, 0.5f, 1f));
                    sheet.SetPixels32(v * cell, 0, cell, cell, cellTexture.GetPixels32());
                    UnityEngine.Object.Destroy(cellTexture);
                }
            }
            finally
            {
                model.SetPositionAndRotation(savedPosition, savedRotation);
            }
            sheet.Apply(false);
            Save(sheet, path);
        }

        private static Texture2D Render(Camera source, int width, int height, Vector3? position, Quaternion? rotation, Color? background)
        {
            var cameraObject = new GameObject("PandabornDevHarnessCamera");
            var camera = cameraObject.AddComponent<Camera>();
            camera.enabled = false;
            if (source) camera.CopyFrom(source);
            if (position.HasValue) camera.transform.position = position.Value;
            if (rotation.HasValue) camera.transform.rotation = rotation.Value;
            if (background.HasValue)
            {
                camera.clearFlags = CameraClearFlags.SolidColor;
                camera.backgroundColor = background.Value;
                camera.fieldOfView = 24f;
                camera.nearClipPlane = 0.05f;
                camera.farClipPlane = 60f;
                camera.ResetProjectionMatrix();
            }
            camera.aspect = width / (float)height;
            var target = RenderTexture.GetTemporary(width, height, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            var texture = new Texture2D(width, height, TextureFormat.RGBA32, false);
            var previous = RenderTexture.active;
            try
            {
                camera.targetTexture = target;
                camera.Render();
                RenderTexture.active = target;
                texture.ReadPixels(new Rect(0, 0, width, height), 0, 0);
                texture.Apply(false);
            }
            finally
            {
                RenderTexture.active = previous;
                camera.targetTexture = null;
                RenderTexture.ReleaseTemporary(target);
                UnityEngine.Object.Destroy(cameraObject);
            }
            return texture;
        }

        private static void Save(Texture2D texture, string path)
        {
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(path));
                File.WriteAllBytes(path, ImageConversion.EncodeToPNG(texture));
            }
            finally
            {
                UnityEngine.Object.Destroy(texture);
            }
        }
    }
}
