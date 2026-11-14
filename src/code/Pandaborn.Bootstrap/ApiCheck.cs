using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;

namespace Pandaborn.Bootstrap
{
    /// <summary>
    /// Resolves a required-API list (written by tools/Pandaborn.ApiScan, format in its Program.cs) against the assemblies
    /// of the running game, without loading the module. Types are formatted exactly as ApiScan formats signature types.
    /// </summary>
    internal static class ApiCheck
    {
        private const BindingFlags All = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly;
        private static readonly Dictionary<string, Assembly> Assemblies = new Dictionary<string, Assembly>(StringComparer.Ordinal);
        private static readonly Dictionary<string, Type> Types = new Dictionary<string, Type>(StringComparer.Ordinal);

        public static List<string> Missing(IEnumerable<string> lines)
        {
            var missing = new List<string>();
            foreach (var line in lines)
            {
                var p = line.Split('\t');
                try
                {
                    switch (p[0])
                    {
                        case "T":
                            if (ResolveType(p[1], p[2]) == null) missing.Add("type " + p[2]);
                            break;
                        case "F":
                        {
                            var type = ResolveType(p[1], p[2]);
                            if (type == null) missing.Add("type " + p[2]);
                            else if (FindField(type, p[3]) == null) missing.Add("field " + p[2] + "." + p[3]);
                            break;
                        }
                        case "M":
                        {
                            var type = ResolveType(p[1], p[2]);
                            if (type == null) missing.Add("type " + p[2]);
                            else if (!HasMethod(type, p[3], int.Parse(p[4]), p.Length > 5 ? p[5] : "")) missing.Add("method " + p[2] + "." + p[3] + "(" + (p.Length > 5 ? p[5] : "") + ")");
                            break;
                        }
                    }
                }
                catch (Exception e)
                {
                    missing.Add(line.Replace('\t', ' ') + " (" + e.GetType().Name + ")");
                }
            }
            return missing;
        }

        /// <summary>Spec class names (D lines) that a loaded assembly already defines as a ComponentSpec; SpecTypeCache would throw on them.</summary>
        public static List<string> SpecNameClashes(IEnumerable<string> lines)
        {
            var ours = new HashSet<string>(lines.Where(l => l.StartsWith("D\t")).Select(l => l.Substring(2)), StringComparer.Ordinal);
            var clashes = new List<string>();
            if (ours.Count == 0) return clashes;
            foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                Type[] types;
                try { types = assembly.GetTypes(); }
                catch (ReflectionTypeLoadException e) { types = e.Types.Where(t => t != null).ToArray(); }
                catch (Exception) { continue; }
                foreach (var t in types)
                {
                    if (t == null || !ours.Contains(t.Name) || !t.IsClass || t.IsAbstract) continue;
                    for (var b = t.BaseType; b != null; b = b.BaseType)
                        if (b.FullName == "Timberborn.BlueprintSystem.ComponentSpec")
                        {
                            clashes.Add(t.Name + " in " + assembly.GetName().Name);
                            break;
                        }
                }
            }
            return clashes;
        }

        private static Type ResolveType(string assemblyName, string typeName)
        {
            string key = assemblyName + "|" + typeName;
            if (Types.TryGetValue(key, out var cached)) return cached;
            var assembly = ResolveAssembly(assemblyName);
            var type = assembly?.GetType(typeName, false);
            Types[key] = type;
            return type;
        }

        private static Assembly ResolveAssembly(string name)
        {
            if (Assemblies.TryGetValue(name, out var cached)) return cached;
            var assembly = AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a => a.GetName().Name == name);
            if (assembly == null)
            {
                try { assembly = Assembly.Load(new AssemblyName(name)); }
                catch (Exception) { assembly = null; }
            }
            Assemblies[name] = assembly;
            return assembly;
        }

        private static FieldInfo FindField(Type type, string name)
        {
            for (var t = type; t != null; t = t.BaseType)
            {
                var f = t.GetField(name, All);
                if (f != null) return f;
            }
            return null;
        }

        private static bool HasMethod(Type type, string name, int arity, string parameters)
        {
            foreach (var t in SelfBasesAndInterfaces(type))
            {
                IEnumerable<MethodBase> candidates = name == ".ctor" ? (IEnumerable<MethodBase>)t.GetConstructors(All)
                    : name == ".cctor" ? (t.TypeInitializer != null ? new MethodBase[] { t.TypeInitializer } : new MethodBase[0])
                    : t.GetMethods(All).Where(m => m.Name == name);
                foreach (var m in candidates)
                {
                    int mArity = m.IsGenericMethodDefinition ? m.GetGenericArguments().Length : 0;
                    if (mArity != arity) continue;
                    if (string.Join(";", m.GetParameters().Select(x => Format(x.ParameterType))) == parameters) return true;
                }
                if (name == ".ctor") break;
            }
            return false;
        }

        private static IEnumerable<Type> SelfBasesAndInterfaces(Type type)
        {
            for (var t = type; t != null; t = t.BaseType) yield return t;
            foreach (var i in type.GetInterfaces()) yield return i.IsGenericType ? i.GetGenericTypeDefinition() : i;
        }

        /// <summary>Same format as Pandaborn.ApiScan's SignatureNames.</summary>
        public static string Format(Type t)
        {
            if (t.IsByRef) return Format(t.GetElementType()) + "&";
            if (t.IsPointer) return Format(t.GetElementType()) + "*";
            if (t.IsArray)
            {
                int rank = t.GetArrayRank();
                return Format(t.GetElementType()) + (rank == 1 && t == t.GetElementType().MakeArrayType() ? "[]" : "[" + new string(',', rank - 1) + "]");
            }
            if (t.IsGenericParameter) return (t.DeclaringMethod != null ? "!!" : "!") + t.GenericParameterPosition;
            if (t.IsGenericType)
            {
                var def = t.GetGenericTypeDefinition();
                return DefinitionName(def) + "<" + string.Join(",", t.GetGenericArguments().Select(Format)) + ">";
            }
            return DefinitionName(t);
        }

        private static string DefinitionName(Type t)
        {
            if (t.IsNested && t.DeclaringType != null) return DefinitionName(t.DeclaringType) + "+" + t.Name;
            return string.IsNullOrEmpty(t.Namespace) ? t.Name : t.Namespace + "." + t.Name;
        }
    }
}
