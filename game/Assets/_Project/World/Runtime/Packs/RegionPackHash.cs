using System.IO;
using System.Security.Cryptography;

namespace Game.World.Packs
{
    /// <summary>SHA-256 helpers for region packs (ADR 0234). Hashing a pack runs on a worker thread from the menu, never while driving.</summary>
    public static class RegionPackHash
    {
        const int BufferSize = 1 << 20;

        /// <summary>Lowercase hex SHA-256 of a file (streamed in 1 MB blocks).</summary>
        public static string Sha256File(string path)
        {
            using (var sha = SHA256.Create())
            using (var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read, BufferSize))
                return ToHex(sha.ComputeHash(fs));
        }

        public static string Sha256Bytes(byte[] data)
        {
            using (var sha = SHA256.Create())
                return ToHex(sha.ComputeHash(data ?? new byte[0]));
        }

        public static string ToHex(byte[] hash)
        {
            const string digits = "0123456789abcdef";
            var c = new char[hash.Length * 2];
            for (int i = 0; i < hash.Length; i++)
            {
                c[2 * i] = digits[hash[i] >> 4];
                c[2 * i + 1] = digits[hash[i] & 15];
            }
            return new string(c);
        }

        public static bool IsSha256Hex(string s)
        {
            if (s == null || s.Length != 64) return false;
            foreach (char ch in s)
                if (!((ch >= '0' && ch <= '9') || (ch >= 'a' && ch <= 'f'))) return false;
            return true;
        }
    }
}
