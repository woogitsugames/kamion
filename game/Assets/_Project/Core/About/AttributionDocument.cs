using System;
using System.Collections.Generic;
using System.Text;

namespace Game.Core.About
{
    /// <summary>Kind of one block of the "Informacje" (about / licences) screen.</summary>
    public enum AttributionBlockKind
    {
        /// <summary>Section heading (<c>= Title</c>).</summary>
        Section,
        /// <summary>Entry heading inside a section (<c>== Title</c>).</summary>
        Entry,
        /// <summary>Paragraph of visible text (consecutive non-empty lines, line breaks kept).</summary>
        Paragraph,
        /// <summary>Full text of another text resource (<c>@include Path</c>, Resources path without extension).</summary>
        Include,
    }

    /// <summary>One block of the about screen: a heading, a paragraph or an include path.</summary>
    public readonly struct AttributionBlock
    {
        public readonly AttributionBlockKind Kind;
        /// <summary>Visible text (headings, paragraphs) or the resource path (include).</summary>
        public readonly string Text;

        public AttributionBlock(AttributionBlockKind kind, string text) { Kind = kind; Text = text; }

        public override string ToString() => Kind + ": " + Text;
    }

    /// <summary>
    /// The attribution / licence text of the "Informacje" screen (Resources/About/attributions.txt), parsed into blocks.
    /// Pure C#, no UnityEngine (tested in EditMode and in plain .NET, tools/about-runner). Format, one rule per line:
    /// <c># comment</c> (never shown: UNVERIFIED / conditional notes stay in the file only), <c>= Section</c>,
    /// <c>== Entry</c>, <c>@include Resources/Path</c> (whole text of another file, e.g. a full licence), an empty line
    /// ends a paragraph, every other line is paragraph text. Not in the driving loop: allocation is fine.
    /// </summary>
    public sealed class AttributionDocument
    {
        /// <summary>Resources path of the screen text (without extension).</summary>
        public const string ResourcePath = "About/attributions";

        /// <summary>Characters per UI text block. uGUI Text builds 4 vertices per character in one mesh (65 535-vertex
        /// limit), so long licence texts are split well below 16 000 characters. WORKING_VALUE.</summary>
        public const int UiChunkChars = 3000;

        /// <summary>Markers that must never reach the screen: an unresolved note belongs in a <c>#</c> comment.</summary>
        public static readonly string[] ForbiddenVisibleMarkers = { "UNVERIFIED", "WARUNKOWO", "TODO", "[ADRES", "LEGAL_REVIEW", "WORKING_VALUE" };

        readonly List<AttributionBlock> m_Blocks;

        public IReadOnlyList<AttributionBlock> Blocks => m_Blocks;

        AttributionDocument(List<AttributionBlock> blocks) { m_Blocks = blocks; }

        /// <summary>Parses the screen text. Null or empty input gives an empty document.</summary>
        public static AttributionDocument Parse(string text)
        {
            var blocks = new List<AttributionBlock>();
            if (string.IsNullOrEmpty(text)) return new AttributionDocument(blocks);
            var para = new StringBuilder();

            void Flush()
            {
                if (para.Length == 0) return;
                blocks.Add(new AttributionBlock(AttributionBlockKind.Paragraph, para.ToString()));
                para.Clear();
            }

            string[] lines = text.Replace("\r\n", "\n").Replace('\r', '\n').Split('\n');
            for (int i = 0; i < lines.Length; i++)
            {
                string line = lines[i].TrimEnd();
                if (i == 0 && line.Length > 0 && line[0] == '﻿') line = line.Substring(1);   // UTF-8 BOM
                if (line.StartsWith("#", StringComparison.Ordinal)) continue;                     // comment: invisible, keeps the paragraph open
                if (line.Length == 0) { Flush(); continue; }
                if (line.StartsWith("==", StringComparison.Ordinal))
                {
                    Flush();
                    blocks.Add(new AttributionBlock(AttributionBlockKind.Entry, line.Substring(2).Trim()));
                }
                else if (line.StartsWith("=", StringComparison.Ordinal))
                {
                    Flush();
                    blocks.Add(new AttributionBlock(AttributionBlockKind.Section, line.Substring(1).Trim()));
                }
                else if (line.StartsWith("@include", StringComparison.Ordinal))
                {
                    Flush();
                    blocks.Add(new AttributionBlock(AttributionBlockKind.Include, line.Substring("@include".Length).Trim()));
                }
                else
                {
                    if (para.Length > 0) para.Append('\n');
                    para.Append(line.TrimStart());
                }
            }
            Flush();
            return new AttributionDocument(blocks);
        }

        /// <summary>Resource paths of every <c>@include</c>, in order.</summary>
        public List<string> Includes()
        {
            var r = new List<string>();
            foreach (var b in m_Blocks) if (b.Kind == AttributionBlockKind.Include) r.Add(b.Text);
            return r;
        }

        /// <summary>Everything the screen shows, as plain text (headings, paragraphs and resolved includes, one blank
        /// line between blocks). <paramref name="resolveInclude"/> returns the text of a resource path, or null when
        /// it is missing (then the path itself is written, so a test can see it).</summary>
        public string VisibleText(Func<string, string> resolveInclude)
        {
            var sb = new StringBuilder();
            foreach (var b in m_Blocks)
            {
                if (sb.Length > 0) sb.Append("\n\n");
                if (b.Kind == AttributionBlockKind.Include)
                    sb.Append((resolveInclude != null ? resolveInclude(b.Text) : null) ?? ("[missing " + b.Text + "]"));
                else sb.Append(b.Text);
            }
            return sb.ToString();
        }

        /// <summary>Problems that make the document unfit for a build: no content, an empty heading or include path,
        /// a heading with no text under it,
        /// a missing include (<paramref name="resolveInclude"/> returned null), or an unresolved marker
        /// (<see cref="ForbiddenVisibleMarkers"/>) in visible text. Empty list = OK.</summary>
        public List<string> Problems(Func<string, string> resolveInclude)
        {
            var p = new List<string>();
            if (m_Blocks.Count == 0) p.Add("document is empty");
            for (int i = 0; i < m_Blocks.Count; i++)
            {
                var b = m_Blocks[i];
                if (string.IsNullOrWhiteSpace(b.Text)) { p.Add("empty " + b.Kind); continue; }
                if (b.Kind == AttributionBlockKind.Entry || b.Kind == AttributionBlockKind.Section)
                {
                    // A heading must be followed by content: an entry by a paragraph or include, a section by anything
                    // but another section (ADR 0230: no empty attribution entries on screen).
                    var next = i + 1 < m_Blocks.Count ? m_Blocks[i + 1].Kind : (AttributionBlockKind?)null;
                    bool empty = b.Kind == AttributionBlockKind.Entry
                        ? next != AttributionBlockKind.Paragraph && next != AttributionBlockKind.Include
                        : next == null || next == AttributionBlockKind.Section;
                    if (empty) p.Add("heading without text: " + b.Kind + ": " + b.Text);
                }
                if (b.Kind == AttributionBlockKind.Include)
                {
                    if (resolveInclude != null && resolveInclude(b.Text) == null) p.Add("missing include " + b.Text);
                    continue;
                }
                foreach (var m in ForbiddenVisibleMarkers)
                    if (b.Text.IndexOf(m, StringComparison.Ordinal) >= 0) p.Add("visible marker " + m + " in " + b.Kind + ": " + b.Text);
            }
            return p;
        }

        /// <summary>Splits a long text into pieces of at most <paramref name="maxChars"/> characters at line breaks
        /// (a longer single line is cut hard). <c>string.Join("\n", Chunk(t, n)) == t</c> for any text without
        /// over-long lines.</summary>
        public static List<string> Chunk(string text, int maxChars)
        {
            if (maxChars < 1) throw new ArgumentOutOfRangeException(nameof(maxChars));
            var r = new List<string>();
            if (string.IsNullOrEmpty(text)) return r;
            var sb = new StringBuilder();
            bool open = false;                                  // sb holds at least one line (possibly empty)
            foreach (string raw in text.Replace("\r\n", "\n").Split('\n'))
            {
                string line = raw;
                while (line.Length > maxChars)                 // a single over-long line: hard cut
                {
                    if (open) { r.Add(sb.ToString()); sb.Clear(); open = false; }
                    r.Add(line.Substring(0, maxChars));
                    line = line.Substring(maxChars);
                    if (line.Length == 0) break;
                }
                if (line.Length == 0 && raw.Length > 0) continue;   // exact multiple of maxChars: nothing left
                if (open && sb.Length + 1 + line.Length > maxChars) { r.Add(sb.ToString()); sb.Clear(); open = false; }
                if (open) sb.Append('\n');
                sb.Append(line);
                open = true;
            }
            if (open) r.Add(sb.ToString());
            return r;
        }
    }
}
