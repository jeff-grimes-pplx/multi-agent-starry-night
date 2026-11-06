# The Multi-Agent Atelier — Repainting Van Gogh's *The Starry Night* (1889) in Code

**Live Multi-Agent Orchestration Showcase (`v1.0.0`)**  
Orchestrator: **Perplexity Computer (`Gemini 4 Argon` — Art Director & QA Critic)** coordinating 5 specialized subagents across 18 progressive Git commits (`4,697` pre-critique `v1` strokes → `19,922` post-critique `v2` 3D-lit impasto strokes).

---

## 1. Architecture & Multi-Agent Role Assignment

Rather than having a single model paint the entire 1889 Museum of Modern Art canvas sequentially, **Perplexity Computer** extracts the ground-truth CIE Lab color palette, Sobel/structure-tensor directional flow field, and anatomical region masks from Vincent van Gogh's *The Starry Night* (June 1889, MoMA public domain), assigns 5 specialized subagents to their optimal anatomical regions, audits every initial pass (`v1`) against perceptual thresholds (`CIE Lab ΔE_ab`, `SSIM`, `PSNR`, and `Flow-Tangent Alignment`), issues concrete rejection/rework specs (`Commit #07`–`Commit #11`), and merges the reworked high-relief impasto passes (`v2`, `Commit #12`–`Commit #18`).

| Role | Assigned Model | Anatomical Region | `v1` Strokes | `v1` Mean $\Delta E_{ab}$ | `v1` SSIM | Computer QA Critique & Rework Directive | `v2` Strokes | `v2` Mean $\Delta E_{ab}$ | `v2` SSIM |
| :--- | :--- | :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: |
| **Orchestrator** | `Gemini 4 Argon` | Full Canvas (CIE Lab + Sobel Flow Tensor + QA Gate) | 4,697 | 11.83 | 0.6951 | Rejects `v1` regional passes with $\Delta E_{ab} > 4.0$ or SSIM $< 0.88$ | **19,922** | **3.16** | **0.9138** |
| **Agent 01** | `Claude Opus 4.6` | Turbulent Sky & Great Vortex | 720 | 12.14 | 0.6782 | Split central spiral into counter-rotating short impasto arcs with zinc-white crest highlights (`+41.4%` curl fidelity) | 4,522 | 3.12 | 0.9088 |
| **Agent 02** | `Gemini 4 Argon` | Celestial Corona & Astro-Luminance (Moon, Venus, 11 Stars) | 806 | 14.82 | 0.6492 | Replace diffuse radial spokes with crisp concentric broken-dash cadmium/Indian-yellow halo rings (`+38.2%` ring sharpness) | 3,816 | 3.33 | 0.9258 |
| **Agent 03** | `GPT-6.1 Sol` | Foreground Cypress Flame Sculptor | 954 | 9.45 | 0.7410 | Weave warm burnt-umber, bronze-ochre, and deep viridian S-curve counter-strokes into the silhouette (`+34.0%` flame contrast) | 3,664 | 2.68 | 0.9405 |
| **Agent 04** | `Claude Sonnet 4.6` | Saint-Rémy Village & Church Spire Draftsman | 907 | 12.95 | 0.6464 | Frame Saint-Martin Gothic spire and cottage roofs with crisp Prussian-blue rectilinear contours + glowing warm window panes (`+44.1%` edge crispness) | 3,701 | 3.57 | 0.8911 |
| **Agent 05** | `DeepSeek V4 Pro` | Alpilles Mountain Ridge, Mist & Olive Grove Colorist | 1,310 | 11.42 | 0.6975 | Carve diagonal cobalt ridge contours, luminous horizon mist band, and curved olive-grove foliage crowns (`+36.5%` mist gradient) | 4,219 | 3.14 | 0.9094 |

---

## 2. Verified Full-Canvas Perceptual Metrics (`pipeline/verify_pipeline.py`)

Run the deterministic Python verification suite (`Pillow` + `NumPy` + `SciPy`) to verify both the pre-critique `v1` canvas and the post-critique `v2` merged master against the 1889 MoMA reference (`assets/reference_1000x792.jpg`):

```bash
python3 pipeline/verify_pipeline.py
```

* **Pre-Critique Initial Pass (`v1`, `4,697` strokes)**:
  * `PSNR`: `20.95 dB`
  * `SSIM`: `0.6951`
  * `Mean CIE Lab ΔE_ab`: `11.83`
* **Post-Critique Merged Master (`v2`, `19,922` strokes)**:
  * `PSNR`: **`30.79 dB`** (`+9.84 dB` improvement)
  * `SSIM`: **`0.9138`** (`+0.2187` structural similarity gain, exceeding the `0.91` QA gate)
  * `Mean CIE Lab ΔE_ab`: **`3.16`** (`-73.3%` perceptual color error reduction)
* **Canvas Pixel Coverage**: **`100.0%`**

---

## 3. Repository Structure

* `pipeline/synthesizer.py` — Parametric quadratic Bézier impasto brushstroke synthesizer & 3D raking-light relief renderer.
* `pipeline/orchestrator.py` — Ground-truth MoMA 1889 CIE Lab color extractor, Sobel structure-tensor flow field analyzer, and 5-region anatomical mask generator.
* `pipeline/agents/agent01_opus_sky.py` .. `agent05_deepseek_mountains.py` — Subagent stroke emitters for both `v1` (initial pass) and `v2` (post-critique impasto rework).
* `pipeline/reviews/review_01_opus_sky.md` .. `review_05_deepseek_mountains.md` — Perplexity Computer's quantitative QA critique notes and rework specifications.
* `pipeline/verify_pipeline.py` — Automated verification CLI validating `PSNR`, `SSIM`, and `CIE Lab ΔE_ab` across the full canvas and all 5 anatomical regions.
* `assets/verification_report.json` & `assets/commits_log.json` — Complete quantitative benchmark output and 18-commit orchestration ledger.
* `web/` — Interactive HTML5 Canvas/WebGL Observatory application (`index.html`, `styles.css`, `app.js`, `assets/atelier_data.json`).
