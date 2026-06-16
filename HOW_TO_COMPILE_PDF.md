# How to compile `R14922020.tex` → `R14922020.pdf`

The report is written in XeLaTeX with `xeCJK` for Chinese characters. The two
straightforward options are below.

## Option A — Overleaf (no install, recommended)

1. Go to <https://www.overleaf.com> and sign in.
2. **New Project → Upload Project** → select a zip of this repository
   (or just `R14922020.tex` on its own — the figure is inlined).
3. Overleaf reads the `% !TEX program = xelatex` magic comment at the top
   of the file and switches the compiler automatically. If for any reason
   it doesn't, open **Menu (top-left) → Compiler** and select **XeLaTeX**.
4. Click **Recompile**.
5. Download the PDF and rename it to `R14922020.pdf`.

Compile takes about 10–15 seconds on Overleaf.

## Option B — Local install (one-time, then offline)

```bash
# macOS, requires sudo (MacTeX is ~4 GB; BasicTeX is ~100 MB and enough)
brew install --cask basictex
eval "$(/usr/libexec/path_helper)"

# After install, add the packages we need:
sudo tlmgr update --self
sudo tlmgr install xecjk ctex booktabs enumitem fancyhdr hyperref tikz pgf fontspec

# Compile (run twice to get the table-of-contents references right):
xelatex R14922020.tex
xelatex R14922020.tex
```

If the system does not have the Noto CJK fonts, install them:

```bash
brew install --cask font-noto-sans-cjk-tc
```

…or change the `\setCJKmainfont{...}` line in `R14922020.tex` to a font you
have, e.g. `PingFang TC` on macOS.

## Sanity check

When the compile succeeds you will see `R14922020.pdf` (about 10 pages,
including the architecture figure on page 4).
