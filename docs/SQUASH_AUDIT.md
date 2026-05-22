# Squash audit: `646eb01` vs `pre-rebase` chain

Audit date: 2026-05-23  
Branches referenced: `pre-rebase` (unsquashed tip), `main` (contains squash)

## Summary

On **2026-05-16**, seven commits above `4ab3876` were reset and replaced by a single squash commit on `main`:

| Item | Result |
|------|--------|
| Squash commit on `main` | `646eb01f9aa827d050fcc7b123b21a18da0ac741` |
| Unsquashed tip (`pre-rebase`) | `b7e92dc207265da777ad6429c115c274ec767684` |
| Squash base (parent of both) | `4ab3876f195c088beeba9c3325a17a860e007679` |
| Tree at unsquashed tip vs squash | **Identical** — `8fe372392b7922508214b5c48c78ea341eee66b3` |
| Cumulative code/config patch (`4ab3876..tip`, excl. LFS/binaries) | **Identical** (172 534-byte patch; 114 paths, +2622/−452) |
| `*.py` / `*.js` / `*.html` patch only | **Identical** (170 558 bytes) |

**Conclusion:** All non-LFS code and text/config changes from the seven squashed commits are fully represented in `646eb01`. The squash only collapsed history; it did not drop py/js/html/md/json/toml/csv/lock/hook changes. The ~92 PDB/STL paths are the intentional LFS divergence (pointers vs inline blobs), not missing application code.

## Reflog (how the squash happened)

```
646eb01  HEAD@{2026-05-16 16:37:58 +0300}: commit: Squash post-structures history; PDB/STL via Git LFS only
4ab3876  HEAD@{2026-05-16 16:32:59 +0300}: reset: moving to 4ab3876
b7e92dc  HEAD@{2026-05-16 16:14:15 +0300}: pull: Fast-forward   ← last tip before reset/squash
```

Workflow: tip was `b7e92dc` → hard reset to `4ab3876` → commit `646eb01` with the same tree as `b7e92dc`.

## Divergence tree (commit graph)

Same **tree** at the fork; different **commits** after `4ab3876`. `main` continued for 12 commits after the squash (report work, sharing fixes, etc.).

```
df0d81147167c3b1b10fa0165a4ba3a1c1f62c3e  better alpha_fold_resolution
    |
4ab3876f195c088beeba9c3325a17a860e007679  pdbs and progressbar  ◄── squash base
    |
    +--- pre-rebase (7 commits, abandoned on main) ----------------+
    |                                                              |
    |   5e32567632bc87fec3bcdd30ad13bcee5ba7ace2  structures      |
    |        |                                                      |
    |   a7e4b3f2b559e13fd94e146f331552c69da07742  ui improvement   |
    |        |                                                      |
    |   c5da1e13676b3d0bd2a0b96021be9918b17a11c2  proper stl of 3d models
    |        |                                                      |
    |   cd1e17f6c2b9aa55619fe94d11166ae7a0141a8b  agents.md update on protein models
    |        |                                                      |
    |   741028895396485fd11daf0f64521a516adff389  Switch PDB/STL to Git LFS…
    |        |                                                      |
    |   abb45f0ac5aa325473d4e3e5e3f89568d6d2230c  sharing added     |
    |        |                                                      |
    |   b7e92dc207265da777ad6429c115c274ec767684  added sharing     |
    |        |                                                      |
    |        +---- tree 8fe372392b7922508214b5c48c78ea341eee66b3 --+
    |                                                              |
    +--- main (squash + post-squash history) ---------------------+
             |
    646eb01f9aa827d050fcc7b123b21a18da0ac741  Squash post-structures history; PDB/STL via Git LFS only
             |                                  (same tree 8fe37239…)
    b53fdb3  Youtube link
    850acde  fixing sharing
    d1deabd  3D features
    a7d10a8  Sharing fix
    15ad569  Squashed fixes
    …        (report / 3Dmol / preview commits)
    335d31ee58f747f7e718afd87e2969cdcfcdcd32  Report migration update and stale web removal  ◄── main tip (at audit)
```

`646eb01` is an ancestor of current `main` (13 commits below tip at time of audit).

## Squashed commits (full hashes)

| Short | Full hash | Date (author) | Subject |
|-------|-----------|---------------|---------|
| `5e32567` | `5e32567632bc87fec3bcdd30ad13bcee5ba7ace2` | 2026-05-11 19:23 | structures |
| `a7e4b3f` | `a7e4b3f2b559e13fd94e146f331552c69da07742` | 2026-05-11 19:33 | ui improvement |
| `c5da1e1` | `c5da1e13676b3d0bd2a0b96021be9918b17a11c2` | 2026-05-12 01:09 | proper stl of 3d models |
| `cd1e17f` | `cd1e17f6c2b9aa55619fe94d11166ae7a0141a8b` | 2026-05-12 01:35 | agents.md update on protein models |
| `7410288` | `741028895396485fd11daf0f64521a516adff389` | 2026-05-12 02:06 | Switch PDB and STL assets to Git LFS, move STLs to assets/stl/ |
| `abb45f0` | `abb45f0ac5aa325473d4e3e5e3f89568d6d2230c` | 2026-05-12 04:36 | sharing added |
| `b7e92dc` | `b7e92dc207265da777ad6429c115c274ec767684` | 2026-05-12 04:43 | added sharing |

**Squash replacement on `main`:** `646eb01f9aa827d050fcc7b123b21a18da0ac741` — parent `4ab3876`, message *Squash post-structures history; PDB/STL via Git LFS only*.

## Verification commands

Reproduce the audit (from repo root):

```bash
BASE=4ab3876f195c088beeba9c3325a17a860e007679
SQUASH=646eb01f9aa827d050fcc7b123b21a18da0ac741
TIP=b7e92dc207265da777ad6429c115c274ec767684
EX=':(exclude)*.pdb:(exclude)*.stl:(exclude)*.png:(exclude)*.jpg:(exclude)*.webp:(exclude)*.gif'

# 1) Same tree at fork
git rev-parse "$TIP^{tree}" "$SQUASH^{tree}"

# 2) Cumulative non-LFS patch identical
git diff "$BASE" "$TIP" -- . "$EX" | wc -c
git diff "$BASE" "$SQUASH" -- . "$EX" | wc -c
git diff --shortstat "$BASE..$TIP" -- . "$EX"
git diff --shortstat "$BASE..$SQUASH" -- . "$EX"

# 3) No file-level drift (code/config only)
comm -3 \
  <(git diff --name-only "$BASE..$TIP" -- . "$EX" | sort) \
  <(git diff --name-only "$BASE..$SQUASH" -- . "$EX" | sort)

# 4) py / js / html only
git diff "$BASE..$TIP" -- '*.py' '*.js' '*.html'
git diff "$BASE..$SQUASH" -- '*.py' '*.js' '*.html'
```

Expected: matching tree SHAs, equal byte counts, empty `comm` output, empty diffs for (4).

## Changed paths by kind (cumulative `4ab3876..tip`)

| Kind | Count | Notes |
|------|------:|-------|
| `.stl` | 46 | Git LFS on `main`; reason for squash/rebase |
| `.pdb` | 46 | Git LFS on `main` |
| `.py` | 8 | Included in squash |
| `.md` | 3 | Included (e.g. AGENTS/CLAUDE) |
| `.js` | 1 | Included |
| `.csv` | 1 | Included |
| `pyproject.toml`, `uv.lock` | 1 each | Included |
| `.gitattributes`, LFS hooks | several | Included |
| `share.jpg` | 1 | Binary; same in both trees |

## Per-commit notes

- **`5e32567`**: Deletes `data/input/structures/.gitignore`; file absent at both `b7e92dc` and `646eb01` (net change preserved).
- **`7410288`**: Moves PDB/STL to LFS — largest path churn; content equivalent at tree level, history differs (blob vs pointer).
- **Post-squash `main`**: Twelve commits after `646eb01` are **not** part of this squash; they exist only on the `main` line after `335d31e` (etc.).

## Branches

| Branch | Role |
|--------|------|
| `pre-rebase` | Preserves unsquashed chain ending at `b7e92dc` |
| `main` | Contains `646eb01` squash + subsequent development |

To restore the granular history locally: `git checkout pre-rebase` or `git reset --hard b7e92dc` on a safety branch.

# LLM prompt: recover commit lost above `pre-rebase` (local reflog)

Copy everything below the line into your LLM chat (Cursor, ChatGPT, etc.) **after** `cd` into your local clone of **materialized-enhancements**. Do not paste secrets or `.env` contents.

---

## Prompt (start)

You are helping me recover **one or more Git commits** that I believe were **lost during a rebase** on my machine. The work was allegedly on top of the **`pre-rebase`** branch chain—not inside the seven commits that were later squashed into `646eb01` on `main` (those are already audited as fully preserved).

### Repository context (read first)

Open `docs/SQUASH_AUDIT.md` in the repo if present. Key facts:

| Role | Full hash | Short | Notes |
|------|-----------|-------|-------|
| Squash base | `4ab3876f195c088beeba9c3325a17a860e007679` | `4ab3876` | Parent of squashed chain |
| Known unsquashed tip (`pre-rebase`) | `b7e92dc207265da777ad6429c115c274ec767684` | `b7e92dc` | *added sharing* — end of 7-commit chain |
| Squash on `main` | `646eb01f9aa827d050fcc7b123b21a18da0ac741` | `646eb01` | Same **tree** as `b7e92dc`: `8fe372392b7922508214b5c48c78ea341eee66b3` |
| Squashed commits (already accounted for) | `5e32567` → `a7e4b3f` → `c5da1e1` → `cd1e17f` → `7410288` → `abb45f0` → `b7e92dc` | | See audit doc |

**What I am looking for:** a commit (or small stack) that was **`b7e92dc^..?` strictly *after* `b7e92dc`** on my machine—local WIP, cherry-picks, or unpushed commits—then disappeared after `rebase`, `reset`, `pull --rebase`, or branch checkout. My **local reflog** should still list it even if it is not on any branch.

**What I am *not* looking for:** the seven squashed commits above `4ab3876`; those are documented as equivalent to `646eb01` for all non-LFS code.

### Your task

1. **Confirm repo and current state** (run commands; show output summaries):
   - `git status -sb`
   - `git branch -vv`
   - `git log -1 --oneline pre-rebase 2>/dev/null || git log -1 --oneline`
   - `git merge-base --is-ancestor b7e92dc HEAD 2>/dev/null; echo "b7e92dc ancestor of HEAD: $?"`

2. **Mine local reflog** for orphaned tips above the pre-rebase chain:
   - `git reflog --date=iso | head -200`
   - `git reflog show pre-rebase --date=iso 2>/dev/null | head -80`
   - `git reflog show main --date=iso 2>/dev/null | head -80`
   - Look for entries **after** any checkout/reset/rebase where HEAD was **not** `b7e92dc` but was **descended from** `b7e92dc` or had a **different tree** than `8fe372392b7922508214b5c48c78ea341eee66b3`.
   - Pay special attention to: `rebase`, `reset`, `checkout`, `pull`, `commit (amend)`, `cherry-pick`.

3. **List candidate lost commits** (hash, date, subject, reflog line):
   - For each candidate `C`, run:
     - `git log -1 --format='%H %ci %an %s' C`
     - `git merge-base --is-ancestor b7e92dc C && echo on-top-of-pre-rebase-tip`
     - `git branch -a --contains C` (empty = unreachable from branches)
     - `git diff --stat b7e92dc C -- ':(exclude)*.pdb' ':(exclude)*.stl'` (focus on py/js/html/md/json/toml/csv/lock)

4. **Deduplicate false positives:**
   - Ignore commits that are ancestors of current `main` / `pre-rebase` / `646eb01` unless they add *unique* diff vs `b7e92dc`.
   - Ignore the seven squashed hashes unless my diff vs `b7e92dc` is non-empty.

5. **Recommend recovery** (safest first):
   - `git branch recover/lost-<short-hash> <hash>`
   - Or `git cherry-pick <hash>` onto current branch after I confirm.
   - **Never** `git push --force` without explicit confirmation.
   - If multiple commits: order oldest-first for cherry-pick.

6. **Report** in this structure:
   - **Found / not found**
   - **Best candidate hash(es)** with reflog evidence (copy the exact `HEAD@{n}` line)
   - **Files changed** vs `b7e92dc` (code only, no PDB/STL)
   - **Recovery commands** I should run manually
   - **If not found:** what else to try (`git fsck --unreachable`, search `refs/stash`, other branch reflogs, approximate date/subject I should add)

### Constraints

- Run real `git` commands in my repo; do not guess hashes.
- Prefer **read-only** investigation until recovery branch is agreed.
- Large **LFS** blobs (`.pdb`, `.stl`) may differ between old and new history; prioritize **py, js, html, css, md, json, toml, csv, lock, sh**.
- I may have uncommitted work; warn before any `reset --hard`.

### Optional hints I can fill in (edit before sending)

- Approximate date of rebase: ___________
- Branch I was on: ___________
- Subject or file I remember in the lost commit: ___________
- Last thing I remember doing: ___________

## Prompt (end)
