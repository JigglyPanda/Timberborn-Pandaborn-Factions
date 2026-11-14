using System.Collections.ObjectModel;
using System.Globalization;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;

namespace SchemaDump;

/// <summary>
/// Mirrors Timberborn.BlueprintSystem (SpecTypeCache, BasicDeserializer, AdvancedDeserializer,
/// SerializableTypeExtensions) over assemblies loaded into a MetadataLoadContext.
/// </summary>
sealed class SchemaBuilder
{
    const BindingFlags AllInstance = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    const string SerializeAttr = "Timberborn.BlueprintSystem.SerializeAttribute";
    const string SpecAliasAttr = "Timberborn.BlueprintSystem.SpecAliasAttribute";
    const string ComponentSpecName = "Timberborn.BlueprintSystem.ComponentSpec";
    const string AssetRefName = "Timberborn.BlueprintSystem.AssetRef`1";
    const string ImmutableArrayName = "System.Collections.Immutable.ImmutableArray`1";
    const string NullableName = "System.Nullable`1";

    static readonly Dictionary<string, string> PrimitiveKinds = new(StringComparer.Ordinal)
    {
        ["System.Int32"] = "int",
        ["System.Single"] = "float",
        ["System.Boolean"] = "bool",
        ["System.String"] = "string",
        ["System.Char"] = "char",
        ["System.Guid"] = "guid",
        ["UnityEngine.Vector2"] = "vector2",
        ["UnityEngine.Vector2Int"] = "vector2int",
        ["UnityEngine.Vector3"] = "vector3",
        ["UnityEngine.Vector3Int"] = "vector3int",
        ["UnityEngine.Quaternion"] = "quaternion",
        ["UnityEngine.Color"] = "color",
        // PrimitiveTypeSerialization.Deserialize passes a SerializedObject through unchanged (any JSON object)
        ["Timberborn.SerializationSystem.SerializedObject"] = "serializedobject",
    };

    readonly Type _componentSpec;
    readonly IlDefaults _il;
    readonly HashSet<Assembly> _modAssemblies;
    public readonly List<string> Errors = new();
    public readonly List<string> Warnings = new();

    readonly JObj _specs = new();
    readonly JObj _types = new();
    readonly JObj _enums = new();
    readonly HashSet<Assembly> _usedAssemblies = new();
    readonly Queue<Type> _pendingTypes = new();
    readonly HashSet<string> _seenTypes = new(StringComparer.Ordinal);
    readonly Dictionary<string, Type> _keyOwners = new(StringComparer.Ordinal);

    public int SpecClassCount { get; private set; }

    public SchemaBuilder(Type componentSpec, IlDefaults il, IEnumerable<Assembly> modAssemblies)
    {
        _componentSpec = componentSpec;
        _il = il;
        _modAssemblies = new HashSet<Assembly>(modAssemblies);
    }

    public JObj Specs => _specs;
    public JObj Types => _types;
    public JObj Enums => _enums;
    public IEnumerable<Assembly> UsedAssemblies => _usedAssemblies;

    // ---------- spec discovery (SpecTypeCache) ----------

    public void AddAssembly(Assembly asm)
    {
        Type?[] types;
        try
        {
            types = asm.GetTypes();
        }
        catch (ReflectionTypeLoadException e)
        {
            types = e.Types;
            var msgs = e.LoaderExceptions.Where(x => x != null).Select(x => x!.Message).Distinct().Take(5);
            Errors.Add($"{asm.GetName().Name}: GetTypes failed partially: {string.Join("; ", msgs)}");
        }

        foreach (var t in types)
        {
            if (t == null) continue;
            bool isSpec;
            try
            {
                isSpec = t.IsClass && !t.IsAbstract && _componentSpec.IsAssignableFrom(t);
            }
            catch (Exception e)
            {
                Errors.Add($"{t.FullName}: cannot resolve base types: {e.Message}");
                continue;
            }
            if (isSpec) AddSpec(t);
        }
    }

    void AddSpec(Type t)
    {
        SpecClassCount++;
        var aliases = GetAliases(t);
        var keys = aliases.Append(t.Name).ToList();
        foreach (var key in keys)
        {
            if (_keyOwners.TryGetValue(key, out var owner))
            {
                Errors.Add($"Duplicate spec key '{key}': {owner.FullName} ({owner.Assembly.GetName().Name}) and {t.FullName} ({t.Assembly.GetName().Name})");
                continue;
            }
            _keyOwners[key] = t;
        }

        var entry = new JObj
        {
            ["fullName"] = t.FullName,
            ["assembly"] = t.Assembly.GetName().Name,
            ["visibility"] = Visibility(t),
            ["isRecord"] = IsRecord(t),
            ["base"] = t.BaseType != null ? TypeName(t.BaseType) : null,
            ["aliases"] = aliases,
            ["origin"] = _modAssemblies.Contains(t.Assembly) ? "mod" : "game",
        };
        FillMembers(t, entry);
        _usedAssemblies.Add(t.Assembly);

        if (_specs.TryGetValue(t.Name, out _) && _keyOwners[t.Name] != t)
            return; // duplicate already reported; keep the first
        _specs[t.Name] = entry;
        foreach (var alias in aliases)
        {
            if (_keyOwners[alias] == t && alias != t.Name)
                _specs[alias] = new JObj { ["aliasOf"] = t.Name };
        }
    }

    /// <summary>
    /// GetCustomAttributes(SpecAliasAttribute, inherit: true).SingleOrDefault(): AllowMultiple is false, so the
    /// most derived class carrying the attribute wins.
    /// </summary>
    static List<string> GetAliases(Type t)
    {
        for (var c = t; c != null; c = c.BaseType)
        {
            var data = c.CustomAttributes.FirstOrDefault(a => a.AttributeType.FullName == SpecAliasAttr);
            if (data == null) continue;
            var list = new List<string>();
            foreach (var arg in data.ConstructorArguments)
            {
                if (arg.Value is ReadOnlyCollection<CustomAttributeTypedArgument> arr)
                    list.AddRange(arr.Select(x => (string)x.Value!));
                else if (arg.Value is string s)
                    list.Add(s);
            }
            return list;
        }
        return new List<string>();
    }

    // ---------- members (SerializableTypeExtensions / AdvancedDeserializer) ----------

    void FillMembers(Type t, JObj entry)
    {
        var fields = new JObj();
        var derived = new JObj();
        foreach (var p in t.GetProperties(AllInstance))
        {
            var attr = GetSerializeAttribute(p);
            if (attr == null) continue;
            string? source = attr.ConstructorArguments.Count > 0 ? attr.ConstructorArguments[0].Value as string : null;
            if (source != null)
            {
                derived[p.Name] = new JObj { ["source"] = source, ["type"] = TypeName(p.PropertyType) };
                continue;
            }
            var desc = Describe(p.PropertyType, inArray: false);
            var field = new JObj
            {
                ["type"] = desc,
                ["declaredOn"] = TypeName(p.DeclaringType!),
                ["access"] = Access(p),
            };
            var (def, defSource) = DefaultOf(p, desc);
            field["default"] = def;
            field["defaultSource"] = defSource;
            var attrs = OtherAttributes(p);
            if (attrs.Count > 0) field["attributes"] = attrs;
            fields[p.Name] = field;
        }
        entry["fields"] = fields;
        entry["derived"] = derived;
    }

    /// <summary>
    /// PropertyInfo.GetCustomAttribute&lt;SerializeAttribute&gt;() uses inherit: true, which for properties walks
    /// overridden base property definitions.
    /// </summary>
    static CustomAttributeData? GetSerializeAttribute(PropertyInfo p)
    {
        for (var cur = p; cur != null; cur = BaseProperty(cur))
        {
            var a = cur.CustomAttributes.FirstOrDefault(x => x.AttributeType.FullName == SerializeAttr);
            if (a != null) return a;
        }
        return null;
    }

    static PropertyInfo? BaseProperty(PropertyInfo p)
    {
        var acc = p.GetMethod ?? p.SetMethod;
        if (acc == null || !acc.IsVirtual || (acc.Attributes & MethodAttributes.NewSlot) != 0) return null;
        for (var b = p.DeclaringType!.BaseType; b != null; b = b.BaseType)
        {
            var bp = b.GetProperty(p.Name, AllInstance | BindingFlags.DeclaredOnly);
            if (bp != null) return bp;
        }
        return null;
    }

    bool IsSerializable(Type t)
    {
        if (_componentSpec.IsAssignableFrom(t)) return true;
        try
        {
            return t.GetProperties(AllInstance).Any(p => p.CustomAttributes.Any(a => a.AttributeType.FullName == SerializeAttr)
                                                         || GetSerializeAttribute(p) != null);
        }
        catch (Exception)
        {
            return false;
        }
    }

    static bool IsGeneric(Type t, string definition) =>
        t.IsGenericType && !t.IsGenericTypeDefinition && t.GetGenericTypeDefinition().FullName == definition;

    // ---------- type descriptors (BasicDeserializer / PrimitiveTypeSerialization) ----------

    JObj Describe(Type t, bool inArray)
    {
        if (IsGeneric(t, AssetRefName))
            return new JObj { ["kind"] = "assetref", ["asset"] = TypeName(t.GenericTypeArguments[0]) };
        if (!inArray && IsGeneric(t, ImmutableArrayName))
            return new JObj { ["kind"] = "array", ["element"] = Describe(t.GenericTypeArguments[0], inArray: true) };
        if (IsSerializable(t))
        {
            EnqueueType(t);
            return new JObj { ["kind"] = "object", ["type"] = TypeName(t) };
        }
        // single values unwrap Nullable<T> before PrimitiveTypeSerialization; array elements do not
        if (!inArray && IsGeneric(t, NullableName))
            return new JObj { ["kind"] = "nullable", ["inner"] = DescribePrimitive(t.GenericTypeArguments[0]) };
        return DescribePrimitive(t);
    }

    JObj DescribePrimitive(Type t)
    {
        if (t.FullName != null && PrimitiveKinds.TryGetValue(t.FullName, out var kind))
            return new JObj { ["kind"] = kind };
        if (t.IsEnum)
        {
            AddEnum(t);
            return new JObj { ["kind"] = "enum", ["enum"] = TypeName(t) };
        }
        return new JObj { ["kind"] = "unsupported", ["clr"] = TypeName(t) };
    }

    void EnqueueType(Type t)
    {
        var name = TypeName(t);
        if (_seenTypes.Add(name)) _pendingTypes.Enqueue(t);
    }

    public void DrainTypes()
    {
        while (_pendingTypes.Count > 0)
        {
            var t = _pendingTypes.Dequeue();
            var entry = new JObj
            {
                ["assembly"] = t.Assembly.GetName().Name,
                ["visibility"] = Visibility(t),
                ["isRecord"] = IsRecord(t),
            };
            FillMembers(t, entry);
            _types[TypeName(t)] = entry;
            _usedAssemblies.Add(t.Assembly);
        }
    }

    void AddEnum(Type t)
    {
        var name = TypeName(t);
        if (_enums.ContainsKey(name)) return;
        var values = new List<object?>();
        foreach (var f in t.GetFields(BindingFlags.Public | BindingFlags.Static))
        {
            values.Add(new JObj { ["name"] = f.Name, ["value"] = NumericValue(f.GetRawConstantValue()) });
        }
        _enums[name] = new JObj
        {
            ["assembly"] = t.Assembly.GetName().Name,
            ["flags"] = t.CustomAttributes.Any(a => a.AttributeType.FullName == "System.FlagsAttribute"),
            ["values"] = values,
        };
        _usedAssemblies.Add(t.Assembly);
    }

    static object NumericValue(object? raw) => raw switch
    {
        ulong u => u,
        null => 0L,
        _ => Convert.ToInt64(raw, CultureInfo.InvariantCulture),
    };

    // ---------- defaults ----------

    (object? value, string source) DefaultOf(PropertyInfo p, JObj desc)
    {
        var declaring = p.DeclaringType!;
        var backing = declaring.GetField($"<{p.Name}>k__BackingField", AllInstance | BindingFlags.DeclaredOnly);
        Dictionary<string, InitValue>? inits;
        try
        {
            inits = _il.Scan(declaring);
        }
        catch (Exception e)
        {
            Warnings.Add($"IL scan of {declaring.FullName} failed: {e.Message}");
            return (null, "unknown");
        }

        InitValue? init = null;
        if (inits != null)
        {
            if (backing != null) inits.TryGetValue(backing.Name, out init);
            if (inits.TryGetValue("set_" + p.Name, out var viaSetter))
                init = init == null || Equals(init, viaSetter) ? viaSetter : new UnknownInit();
        }
        if (init is ConstInit c)
        {
            var (ok, v) = ConvertConst(c.Value, desc);
            return ok ? (v, "initializer") : (null, "unknown");
        }
        if (init is UnknownInit) return (null, "unknown");
        if (backing == null) return (null, "unknown"); // not an auto-property: the getter may compute anything
        return (TypeDefault(desc), "typeDefault");
    }

    object? TypeDefault(JObj desc)
    {
        switch ((string)desc["kind"]!)
        {
            case "int": return 0;
            case "float": return 0f;
            case "bool": return false;
            case "char": return "\0";
            case "guid": return "00000000-0000-0000-0000-000000000000";
            case "vector2": case "vector2int": return Zeros("X", "Y");
            case "vector3": case "vector3int": return Zeros("X", "Y", "Z");
            case "quaternion": return Zeros("X", "Y", "Z", "W");
            case "color": return Zeros("r", "g", "b", "a");
            case "enum": return EnumName((string)desc["enum"]!, 0);
            case "array": return new List<object?>();
            default: return null; // string, object, assetref, nullable, unsupported, serializedobject
        }
    }

    static JObj Zeros(params string[] keys)
    {
        var o = new JObj();
        foreach (var k in keys) o[k] = 0;
        return o;
    }

    (bool ok, object? value) ConvertConst(object? c, JObj desc)
    {
        var kind = (string)desc["kind"]!;
        if (kind == "nullable")
            return c == null ? (true, null) : ConvertConst(c, (JObj)desc["inner"]!);
        if (c is EmptyArray) return kind == "array" ? (true, new List<object?>()) : (false, null);
        if (c == null) return (true, null);
        switch (kind)
        {
            case "int" when c is int i: return (true, i);
            case "bool" when c is int b: return (true, b != 0);
            case "float" when c is float f: return (true, f);
            case "float" when c is double d: return (true, (float)d);
            case "float" when c is int fi: return (true, (float)fi);
            case "char" when c is int ch: return (true, ((char)ch).ToString());
            case "string" when c is string s: return (true, s);
            case "enum" when c is int e: return (true, EnumName((string)desc["enum"]!, e));
            default: return (false, null);
        }
    }

    /// <summary>Enum.ToString(): exact member name, flags combination, or the number.</summary>
    object EnumName(string enumName, long value)
    {
        var e = (JObj)_enums[enumName]!;
        var members = ((List<object?>)e["values"]!).Cast<JObj>()
            .Select(m => (name: (string)m["name"]!, value: Convert.ToInt64(m["value"], CultureInfo.InvariantCulture)))
            .ToList();
        var exact = members.FirstOrDefault(m => m.value == value);
        if (exact.name != null) return exact.name;
        if ((bool)e["flags"]! && value > 0)
        {
            var parts = new List<string>();
            long rest = value;
            foreach (var m in members.Where(m => m.value > 0).OrderByDescending(m => m.value))
            {
                if ((rest & m.value) == m.value)
                {
                    parts.Insert(0, m.name);
                    rest &= ~m.value;
                }
            }
            if (rest == 0) return string.Join(", ", parts);
        }
        return value;
    }

    // ---------- small helpers ----------

    static string Visibility(Type t) => t.IsVisible ? "public" : "internal";

    static bool IsRecord(Type t)
    {
        if (t.IsValueType)
        {
            // record struct: compiler-generated PrintMembers
            var pm = t.GetMethod("PrintMembers", AllInstance | BindingFlags.DeclaredOnly);
            return pm != null && pm.CustomAttributes.Any(a =>
                a.AttributeType.FullName == "System.Runtime.CompilerServices.CompilerGeneratedAttribute");
        }
        return t.GetMethods(AllInstance).Any(m => m.Name == "<Clone>$");
    }

    static string Access(PropertyInfo p)
    {
        var m = p.GetMethod ?? p.SetMethod!;
        if (m.IsPublic) return "public";
        if (m.IsAssembly) return "internal";
        if (m.IsFamily || m.IsFamilyOrAssembly) return "protected";
        return "private"; // private, private protected
    }

    static readonly HashSet<string> IgnoredAttributes = new(StringComparer.Ordinal)
    {
        SerializeAttr,
        "System.Runtime.CompilerServices.CompilerGeneratedAttribute",
        "System.Runtime.CompilerServices.NullableAttribute",
        "System.Runtime.CompilerServices.NullableContextAttribute",
    };

    static List<object?> OtherAttributes(PropertyInfo p)
    {
        var list = new List<string>();
        foreach (var a in p.CustomAttributes)
        {
            var name = a.AttributeType.FullName!;
            if (IgnoredAttributes.Contains(name)) continue;
            var args = a.ConstructorArguments.Select(FormatArg)
                .Concat(a.NamedArguments.Select(n => n.MemberName + "=" + FormatArg(n.TypedValue)));
            list.Add(name + "(" + string.Join(",", args) + ")");
        }
        list.Sort(StringComparer.Ordinal);
        return list.Cast<object?>().ToList();
    }

    static string FormatArg(CustomAttributeTypedArgument arg)
    {
        var v = arg.Value;
        if (v is ReadOnlyCollection<CustomAttributeTypedArgument> arr)
            return "[" + string.Join(",", arr.Select(FormatArg)) + "]";
        if (v == null) return "null";
        if (arg.ArgumentType.IsEnum)
        {
            long n = Convert.ToInt64(v, CultureInfo.InvariantCulture);
            var f = arg.ArgumentType.GetFields(BindingFlags.Public | BindingFlags.Static)
                .FirstOrDefault(x => Convert.ToInt64(x.GetRawConstantValue(), CultureInfo.InvariantCulture) == n);
            return f?.Name ?? n.ToString(CultureInfo.InvariantCulture);
        }
        return v switch
        {
            string s => "\"" + s.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"",
            bool b => b ? "true" : "false",
            Type ty => "typeof(" + TypeName(ty) + ")",
            IFormattable fmt => fmt.ToString(null, CultureInfo.InvariantCulture),
            _ => v.ToString() ?? "",
        };
    }

    /// <summary>Readable CLR name: full name, nested types with '+', generics as Name&lt;Args&gt;.</summary>
    public static string TypeName(Type t)
    {
        if (t.IsArray) return TypeName(t.GetElementType()!) + "[]";
        if (t.IsGenericParameter) return t.Name;
        if (t.IsGenericType)
        {
            var def = t.GetGenericTypeDefinition();
            var baseName = def.FullName ?? def.Name;
            int tick = baseName.IndexOf('`');
            if (tick >= 0) baseName = baseName[..tick];
            if (t.IsGenericTypeDefinition) return def.FullName ?? def.Name;
            return baseName + "<" + string.Join(",", t.GenericTypeArguments.Select(TypeName)) + ">";
        }
        return t.FullName ?? t.Name;
    }

    public static JObj AssemblyInfo(Assembly asm)
    {
        using var sha = SHA256.Create();
        var hash = Convert.ToHexString(sha.ComputeHash(File.ReadAllBytes(asm.Location))).ToLowerInvariant();
        return new JObj
        {
            ["version"] = asm.GetName().Version?.ToString(),
            ["mvid"] = asm.ManifestModule.ModuleVersionId.ToString(),
            ["sha256"] = hash,
        };
    }
}
