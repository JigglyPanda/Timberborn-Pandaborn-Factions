using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;

namespace Pandaborn.Bootstrap
{
    /// <summary>
    /// Resolves a required-API list (written by tools/Pandaborn.ApiScan, format in its Program.cs) against the assemblies
    /// of the running game, without loading the module. Types are formatted exactly as ApiScan formats signature types.
    ///
    /// A line is missing when the module could not bind to it at run time: the type, method or field is gone; it is no
    /// longer accessible from another assembly (made internal or private); a method returns, or a field holds, another
    /// type than the one the module was compiled against (the runtime binds by full signature); a game class the module
    /// derives from is sealed or an interface it implements has a member the module does not know (V lines); or another
    /// Pandaborn assembly it names is not loaded (R lines). Any of these, in a loaded assembly, ends in a type or method
    /// that cannot load, and the game's SpecTypeCache calls GetTypes() on every assembly in every game.
    /// </summary>
    internal static class ApiCheck
    {
        private const BindingFlags All = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly;
        private const BindingFlags InstanceWithInherited = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;
        private static readonly Dictionary<string, Assembly> Assemblies = new Dictionary<string, Assembly>(StringComparer.Ordinal);
        private static readonly Dictionary<string, Type> Types = new Dictionary<string, Type>(StringComparer.Ordinal);

        /// <param name="lines">the module's required-API list</param>
        /// <param name="pandabornLoaded">tells whether a Pandaborn assembly (R line) is loaded; null skips R lines</param>
        public static List<string> Missing(IEnumerable<string> lines, Func<string, bool> pandabornLoaded = null)
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
                        {
                            var type = ResolveType(p[1], p[2]);
                            if (type == null) missing.Add("type " + p[2]);
                            else if (!Accessible(type)) missing.Add("type " + p[2] + " (no longer public)");
                            break;
                        }
                        case "F":
                        {
                            var type = ResolveType(p[1], p[2]);
                            if (type == null) { missing.Add("type " + p[2]); break; }
                            var field = FindField(type, p[3]);
                            if (field == null) missing.Add("field " + p[2] + "." + p[3]);
                            else if (!(field.IsPublic || field.IsFamily || field.IsFamilyOrAssembly)) missing.Add("field " + p[2] + "." + p[3] + " (no longer public)");
                            else if (p.Length > 4 && p[4].Length > 0 && Format(field.FieldType) != p[4])
                                missing.Add("field " + p[2] + "." + p[3] + " (now " + Format(field.FieldType) + ")");
                            break;
                        }
                        case "M":
                        {
                            var type = ResolveType(p[1], p[2]);
                            if (type == null) { missing.Add("type " + p[2]); break; }
                            string parameters = p.Length > 5 ? p[5] : "";
                            string why = MethodProblem(type, p[3], int.Parse(p[4]), parameters, p.Length > 6 && p[6].Length > 0 ? p[6] : null);
                            if (why != null) missing.Add("method " + p[2] + "." + p[3] + "(" + parameters + ")" + (why.Length > 0 ? " (" + why + ")" : ""));
                            break;
                        }
                        case "V":
                        {
                            var type = ResolveType(p[1], p[2]);
                            if (type == null) { missing.Add("type " + p[2]); break; }
                            string why = BaseProblem(type, p[3] == "I", p.Length > 4 ? p[4] : "");
                            if (why != null) missing.Add(why);
                            break;
                        }
                        case "R":
                            if (pandabornLoaded != null && !pandabornLoaded(p[1])) missing.Add("needs " + p[1] + ", which is not loaded");
                            break;
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

        /// <summary>Usable from another assembly: public, or nested public/protected inside such a type.</summary>
        private static bool Accessible(Type type)
        {
            for (var t = type; t != null; t = t.DeclaringType)
            {
                if (!t.IsNested) return t.IsPublic;
                if (!(t.IsNestedPublic || t.IsNestedFamily || t.IsNestedFamORAssem)) return false;
            }
            return true;
        }

        private static bool Accessible(MethodBase m) => m.IsPublic || m.IsFamily || m.IsFamilyOrAssembly;

        private static FieldInfo FindField(Type type, string name)
        {
            for (var t = type; t != null; t = t.BaseType)
            {
                var f = t.GetField(name, All);
                if (f != null) return f;
            }
            return null;
        }

        /// <summary>Null when the method is there as the module expects it; else why not ("" = not found at all).</summary>
        private static string MethodProblem(Type type, string name, int arity, string parameters, string returnType)
        {
            string problem = "";
            foreach (var t in SelfBasesAndInterfaces(type))
            {
                IEnumerable<MethodBase> candidates = name == ".ctor" ? (IEnumerable<MethodBase>)t.GetConstructors(All)
                    : name == ".cctor" ? (t.TypeInitializer != null ? new MethodBase[] { t.TypeInitializer } : new MethodBase[0])
                    : t.GetMethods(All).Where(m => m.Name == name);
                foreach (var m in candidates)
                {
                    int mArity = m.IsGenericMethodDefinition ? m.GetGenericArguments().Length : 0;
                    if (mArity != arity) continue;
                    if (string.Join(";", m.GetParameters().Select(x => Format(x.ParameterType))) != parameters) continue;
                    if (returnType != null && m is MethodInfo info && Format(info.ReturnType) != returnType)
                    {
                        problem = "now returns " + Format(info.ReturnType);
                        continue;
                    }
                    if (name != ".cctor" && !Accessible(m))
                    {
                        if (problem.Length == 0) problem = "no longer public";
                        continue;
                    }
                    return null;
                }
                if (name == ".ctor" || name == ".cctor") break;
            }
            return problem;
        }

        /// <summary>
        /// A game class the module derives from must still be an open class, and it (or an interface the module
        /// implements) must not ask for a member the module was not built against. Null when all is well. This check is
        /// only ever an extra net: if it cannot do its work it says nothing.
        /// </summary>
        private static string BaseProblem(Type type, bool isInterface, string knownMembers)
        {
            if (isInterface != type.IsInterface) return "type " + type.FullName + " (" + (isInterface ? "no longer an interface" : "now an interface") + ")";
            if (!isInterface && (type.IsSealed || type.IsValueType)) return "type " + type.FullName + " (can no longer be derived from)";
            try
            {
                var known = new HashSet<string>(knownMembers.Split(new[] { '|' }, StringSplitOptions.RemoveEmptyEntries), StringComparer.Ordinal);
                if (isInterface)
                {
                    var interfaces = new List<Type> { type };
                    foreach (var i in type.GetInterfaces())
                        if (IsGameAssembly(i.Assembly.GetName().Name)) interfaces.Add(i.IsGenericType ? i.GetGenericTypeDefinition() : i);
                    foreach (var i in interfaces)
                        foreach (var m in i.GetMethods(All))
                            if (m.IsAbstract && !known.Contains(Signature(m)))
                                return "interface " + type.FullName + " now requires " + m.Name;
                }
                else
                {
                    foreach (var m in type.GetMethods(InstanceWithInherited))
                    {
                        if (!m.IsAbstract) continue;
                        var definition = OnTypeDefinition(m);
                        if (definition != null && !known.Contains(Signature(definition)))
                            return "class " + type.FullName + " now requires " + m.Name;
                    }
                }
            }
            catch (Exception) { }
            return null;
        }

        /// <summary>The method as its generic type definition declares it (parameters in terms of !0), or null if unknown.</summary>
        private static MethodInfo OnTypeDefinition(MethodInfo m)
        {
            var declaring = m.DeclaringType;
            if (declaring == null || !declaring.IsGenericType || declaring.IsGenericTypeDefinition) return m;
            try { return MethodBase.GetMethodFromHandle(m.MethodHandle, declaring.GetGenericTypeDefinition().TypeHandle) as MethodInfo; }
            catch (Exception) { return null; }
        }

        private static string Signature(MethodInfo m) =>
            m.Name + "~" + (m.IsGenericMethodDefinition ? m.GetGenericArguments().Length : 0) + "~"
            + string.Join(";", m.GetParameters().Select(x => Format(x.ParameterType))) + "~" + Format(m.ReturnType);

        /// <summary>Same rule as Pandaborn.ApiScan's GameAssembly.</summary>
        private static bool IsGameAssembly(string name) =>
            name.StartsWith("Timberborn.", StringComparison.Ordinal) || name.StartsWith("Bindito.", StringComparison.Ordinal)
            || name.StartsWith("Unity", StringComparison.Ordinal);

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
