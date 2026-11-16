using UnityEngine;

namespace Game.Controls
{
    public enum NavDir { Up, Down, Left, Right }

    /// <summary>
    /// Explicit pad / keyboard navigation order of a menu laid out in columns of rows (ADR 0265). Pure, no allocation:
    /// the caller describes the menu by the number of items in every row of every column and asks for the neighbour of an
    /// item. Rules (predictable, unlike Unity's automatic nearest-in-direction search on mixed button widths):
    /// up / down = previous / next row of the same column, item at the same relative position (no wrap);
    /// left / right = previous / next item of the row; past the row's end into the neighbouring column at the row with
    /// the same relative height, entering at its near end. Empty rows are skipped.
    /// </summary>
    public static class MenuNavGrid
    {
        /// <summary>Neighbour of item (<paramref name="col"/>, <paramref name="row"/>, <paramref name="idx"/>) in
        /// <paramref name="dir"/>; false = none (the selection stays).</summary>
        public static bool Neighbour(int[][] rows, int col, int row, int idx, NavDir dir, out int nCol, out int nRow, out int nIdx)
        {
            nCol = col; nRow = row; nIdx = idx;
            if (rows == null || col < 0 || col >= rows.Length || rows[col] == null || row < 0 || row >= rows[col].Length) return false;
            int len = rows[col][row];
            switch (dir)
            {
                case NavDir.Up:
                case NavDir.Down:
                {
                    int step = dir == NavDir.Up ? -1 : 1;
                    for (int r = row + step; r >= 0 && r < rows[col].Length; r += step)
                    {
                        int l = rows[col][r];
                        if (l <= 0) continue;
                        nRow = r; nIdx = MapIndex(idx, len, l);
                        return true;
                    }
                    return false;
                }
                default:
                {
                    int step = dir == NavDir.Left ? -1 : 1;
                    if (idx + step >= 0 && idx + step < len) { nIdx = idx + step; return true; }
                    int c = col + step;
                    if (c < 0 || c >= rows.Length || rows[c] == null) return false;
                    int target = MapIndex(row, rows[col].Length, rows[c].Length);
                    // nearest non-empty row to the mapped one
                    for (int d = 0; d < rows[c].Length; d++)
                    {
                        for (int s = -1; s <= 1; s += 2)
                        {
                            int r = target + (s < 0 ? -d : d);
                            if (r < 0 || r >= rows[c].Length || rows[c][r] <= 0) continue;
                            nCol = c; nRow = r; nIdx = step > 0 ? 0 : rows[c][r] - 1;
                            return true;
                        }
                    }
                    return false;
                }
            }
        }

        /// <summary>Same relative position in a row / column of another length.</summary>
        public static int MapIndex(int i, int fromLen, int toLen)
        {
            if (toLen <= 1 || fromLen <= 1) return 0;
            return Mathf.Clamp(Mathf.RoundToInt(i * (toLen - 1) / (float)(fromLen - 1)), 0, toLen - 1);
        }
    }
}
