// Stand-ins for the game types the linked production files name, and fake "game" types for the API check.
using System.Collections.Generic;

namespace Timberborn.ModManagerScene
{
    public interface IModEnvironment
    {
        string ModPath { get; }
    }

    public interface IModStarter
    {
        void StartMod(IModEnvironment modEnvironment);
    }
}

namespace UnityEngine
{
    /// <summary>Collects what the production code logs.</summary>
    public static class Debug
    {
        public static readonly List<string> Lines = new List<string>();

        public static void Log(object message) => Lines.Add("LOG " + message);

        public static void LogWarning(object message) => Lines.Add("WARN " + message);

        public static void LogError(object message) => Lines.Add("ERROR " + message);
    }
}

// What a game assembly may look like to the API check (this test assembly is named Timberborn.*).
namespace Fake
{
    public class Service
    {
        public int Count;
        internal int Hidden;

        public Service() { }

        public string Name => "x";

        public List<string> Items(int limit) => null;

        public T Pick<T>(IEnumerable<T> from) => default;

        internal void Internal() { }

        protected virtual void Hook() { }

        public class Nested
        {
            public void Go() { }
        }
    }

    internal class Secret { }

    public sealed class Closed { }

    public interface IBase
    {
        void A();
    }

    public interface IDerived : IBase
    {
        int B(string s);

        string Title { get; }
    }

    public interface IProvider<T>
    {
        T Get();
    }

    public abstract class Abstract
    {
        public abstract void X();

        protected abstract int Y { get; }

        public virtual void Z() { }
    }

    public abstract class Generic<T>
    {
        public abstract T Make(T seed);
    }

    /// <summary>Still abstract in Make(int): the check must see it as Make(!0), the form the build list has.</summary>
    public abstract class Middle : Generic<int>
    {
    }

    /// <summary>Implements the abstract member of its base: nothing left to implement for a class deriving from it.</summary>
    public class Done : Abstract
    {
        public override void X() { }

        protected override int Y => 1;
    }
}
