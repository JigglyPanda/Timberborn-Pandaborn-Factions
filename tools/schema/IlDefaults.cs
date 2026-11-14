using System.Reflection;
using System.Reflection.Emit;
using System.Reflection.Metadata;
using System.Reflection.Metadata.Ecma335;
using System.Reflection.PortableExecutable;

namespace SchemaDump;

/// <summary>Result of scanning constructors for one auto-property.</summary>
abstract record InitValue;
sealed record ConstInit(object? Value) : InitValue;   // a constant (boxed int/long/float/double/string/null) or EmptyArray
sealed record UnknownInit : InitValue;
sealed record EmptyArray
{
    public static readonly EmptyArray Instance = new();
}

/// <summary>
/// Finds simple property initializers by reading the IL of a type's parameterless instance constructors:
/// <c>ldarg.0; &lt;constant&gt;; stfld &lt;Prop&gt;k__BackingField</c> (or <c>call set_Prop</c>).
/// Uses System.Reflection.Metadata directly, so nothing is executed.
/// </summary>
sealed class IlDefaults : IDisposable
{
    static readonly Dictionary<ushort, OpCode> OpCodesByValue = typeof(OpCodes)
        .GetFields(BindingFlags.Public | BindingFlags.Static)
        .Select(f => (OpCode)f.GetValue(null)!)
        .ToDictionary(o => (ushort)o.Value);

    readonly Dictionary<string, (PEReader pe, MetadataReader md)> _readers = new(StringComparer.OrdinalIgnoreCase);
    readonly Dictionary<Type, Dictionary<string, InitValue>?> _cache = new();

    public void Dispose()
    {
        foreach (var r in _readers.Values) r.pe.Dispose();
    }

    (PEReader pe, MetadataReader md) Reader(Assembly asm)
    {
        if (!_readers.TryGetValue(asm.Location, out var r))
        {
            var pe = new PEReader(File.OpenRead(asm.Location));
            r = (pe, pe.GetMetadataReader());
            _readers[asm.Location] = r;
        }
        return r;
    }

    /// <summary>
    /// Map of field-or-property name -> initializer seen in parameterless ctors of <paramref name="type"/>
    /// (keys are backing field names and setter names). Null when the type has no parameterless instance ctor.
    /// </summary>
    public Dictionary<string, InitValue>? Scan(Type type)
    {
        if (_cache.TryGetValue(type, out var cached)) return cached;
        Dictionary<string, InitValue>? result = null;
        var ctors = type.GetConstructors(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
            .Where(c => c.GetParameters().Length == 0 && c.DeclaringType == type)
            .ToList();
        if (ctors.Count > 0)
        {
            result = new Dictionary<string, InitValue>(StringComparer.Ordinal);
            var (pe, md) = Reader(type.Assembly);
            foreach (var ctor in ctors)
            {
                var handle = (MethodDefinitionHandle)MetadataTokens.EntityHandle(ctor.MetadataToken);
                var def = md.GetMethodDefinition(handle);
                if (def.RelativeVirtualAddress == 0) continue;
                var il = pe.GetMethodBody(def.RelativeVirtualAddress).GetILBytes();
                if (il != null) ScanIl(md, il, result);
            }
        }
        _cache[type] = result;
        return result;
    }

    abstract record Item;
    sealed record This : Item { public static readonly This I = new(); }
    sealed record Const(object? Value) : Item;
    sealed record Unknown : Item { public static readonly Unknown I = new(); }

    static void ScanIl(MetadataReader md, byte[] il, Dictionary<string, InitValue> result)
    {
        var stack = new List<Item>();
        Item Pop()
        {
            if (stack.Count == 0) return Unknown.I;
            var it = stack[^1];
            stack.RemoveAt(stack.Count - 1);
            return it;
        }
        void Record(string name, Item value)
        {
            InitValue v = value is Const c ? new ConstInit(c.Value) : new UnknownInit();
            if (result.TryGetValue(name, out var prev) && !Equals(prev, v)) v = new UnknownInit();
            result[name] = v;
        }

        int pos = 0;
        while (pos < il.Length)
        {
            ushort code = il[pos++];
            if (code == 0xFE) code = (ushort)(0xFE00 | il[pos++]);
            if (!OpCodesByValue.TryGetValue(code, out var op))
                return; // malformed: give up on this ctor
            int operandStart = pos;
            pos += OperandSize(op.OperandType, il, pos);

            switch (op.Value)
            {
                case var v when v == OpCodes.Ldarg_0.Value:
                    stack.Add(This.I); continue;
                case var v when v == OpCodes.Ldnull.Value:
                    stack.Add(new Const(null)); continue;
                case var v when v == OpCodes.Ldc_I4_M1.Value: stack.Add(new Const(-1)); continue;
                case var v when v >= OpCodes.Ldc_I4_0.Value && v <= OpCodes.Ldc_I4_8.Value:
                    stack.Add(new Const(v - OpCodes.Ldc_I4_0.Value)); continue;
                case var v when v == OpCodes.Ldc_I4_S.Value:
                    stack.Add(new Const((int)(sbyte)il[operandStart])); continue;
                case var v when v == OpCodes.Ldc_I4.Value:
                    stack.Add(new Const(BitConverter.ToInt32(il, operandStart))); continue;
                case var v when v == OpCodes.Ldc_I8.Value:
                    stack.Add(new Const(BitConverter.ToInt64(il, operandStart))); continue;
                case var v when v == OpCodes.Ldc_R4.Value:
                    stack.Add(new Const(BitConverter.ToSingle(il, operandStart))); continue;
                case var v when v == OpCodes.Ldc_R8.Value:
                    stack.Add(new Const(BitConverter.ToDouble(il, operandStart))); continue;
                case var v when v == OpCodes.Ldstr.Value:
                {
                    int token = BitConverter.ToInt32(il, operandStart);
                    stack.Add(new Const(md.GetUserString(MetadataTokens.UserStringHandle(token & 0xFFFFFF))));
                    continue;
                }
                case var v when v == OpCodes.Ldsfld.Value:
                {
                    var (name, parent) = MemberInfoOf(md, BitConverter.ToInt32(il, operandStart));
                    if (name == "Empty" && parent == "System.String") { stack.Add(new Const("")); continue; }
                    if (name == "Empty" && parent == "System.Collections.Immutable.ImmutableArray`1")
                    { stack.Add(new Const(EmptyArray.Instance)); continue; }
                    stack.Add(Unknown.I); continue;
                }
                case var v when v == OpCodes.Newobj.Value:
                {
                    var (name, parent) = MemberInfoOf(md, BitConverter.ToInt32(il, operandStart));
                    if (name == ".ctor" && parent == "System.Nullable`1")
                    {
                        var inner = Pop();
                        stack.Add(inner is Const ? inner : Unknown.I);
                        continue;
                    }
                    break; // fall through to poison
                }
                case var v when v == OpCodes.Stfld.Value:
                {
                    var (name, _) = MemberInfoOf(md, BitConverter.ToInt32(il, operandStart));
                    var value = Pop();
                    var target = Pop();
                    if (name != null) Record(name, target is This || target is Unknown ? value : Unknown.I);
                    continue;
                }
                case var v when v == OpCodes.Call.Value || v == OpCodes.Callvirt.Value:
                {
                    var (name, _) = MemberInfoOf(md, BitConverter.ToInt32(il, operandStart));
                    if (name != null && name.StartsWith("set_", StringComparison.Ordinal))
                    {
                        var value = Pop();
                        var target = Pop();
                        Record(name, target is This || target is Unknown ? value : Unknown.I);
                        continue;
                    }
                    break;
                }
            }
            // any other instruction: we do not model its stack effect; forget the stack
            stack.Clear();
        }
    }

    static int OperandSize(OperandType t, byte[] il, int pos) => t switch
    {
        OperandType.InlineNone => 0,
        OperandType.ShortInlineBrTarget or OperandType.ShortInlineI or OperandType.ShortInlineVar => 1,
        OperandType.InlineVar => 2,
        OperandType.InlineI8 or OperandType.InlineR => 8,
        OperandType.InlineSwitch => 4 + 4 * BitConverter.ToInt32(il, pos),
        _ => 4,
    };

    /// <summary>Name and declaring-type full name (generic definition) of a field/method token.</summary>
    static (string? name, string? parent) MemberInfoOf(MetadataReader md, int token)
    {
        var handle = MetadataTokens.EntityHandle(token);
        switch (handle.Kind)
        {
            case HandleKind.FieldDefinition:
            {
                var f = md.GetFieldDefinition((FieldDefinitionHandle)handle);
                return (md.GetString(f.Name), TypeName(md, f.GetDeclaringType()));
            }
            case HandleKind.MethodDefinition:
            {
                var m = md.GetMethodDefinition((MethodDefinitionHandle)handle);
                return (md.GetString(m.Name), TypeName(md, m.GetDeclaringType()));
            }
            case HandleKind.MemberReference:
            {
                var r = md.GetMemberReference((MemberReferenceHandle)handle);
                return (md.GetString(r.Name), TypeName(md, r.Parent));
            }
            case HandleKind.MethodSpecification:
            {
                var s = md.GetMethodSpecification((MethodSpecificationHandle)handle);
                return MemberInfoOf(md, MetadataTokens.GetToken(s.Method));
            }
            default:
                return (null, null);
        }
    }

    static string? TypeName(MetadataReader md, EntityHandle h)
    {
        switch (h.Kind)
        {
            case HandleKind.TypeDefinition:
            {
                var t = md.GetTypeDefinition((TypeDefinitionHandle)h);
                return Join(md.GetString(t.Namespace), md.GetString(t.Name));
            }
            case HandleKind.TypeReference:
            {
                var t = md.GetTypeReference((TypeReferenceHandle)h);
                return Join(md.GetString(t.Namespace), md.GetString(t.Name));
            }
            case HandleKind.TypeSpecification:
            {
                // generic instantiation: GENERICINST (CLASS|VALUETYPE) TypeDefOrRef ...
                var spec = md.GetTypeSpecification((TypeSpecificationHandle)h);
                var blob = md.GetBlobReader(spec.Signature);
                if (blob.ReadSignatureTypeCode() != SignatureTypeCode.GenericTypeInstance) return null;
                blob.ReadSignatureTypeCode();
                return TypeName(md, blob.ReadTypeHandle());
            }
            default:
                return null;
        }
    }

    static string Join(string ns, string name) => ns.Length == 0 ? name : ns + "." + name;
}
