# UI captures

These images and the video were captured with Playwright on 2026-11-02 against the
real NorthStar Policy Desk. The question used the configured OpenAI provider and
returned four source references across two synthetic policies. No API responses
were mocked. The video is silent, 1440×1000, approximately 15 seconds, in WebM/VP9.
`capture-summary.json` records the result and successful browser playback check.

- `policy-desk-light.png`: completed live answer and evidence.
- `policy-desk-dark.png`: the same answer in dark mode.
- `policy-desk-mobile-dark.png`: the same page at 390×844.
- `manage-policies-light.png`: actual policy library and chunking controls.
- `live-question-demo.webm`: original Playwright recording, with no time edits.
- `live-question-preview.gif`: lower-resolution animated preview for GitHub Markdown.
- `live-demo-poster.png`: a decoded final frame from the recording.

## Reproduce

Use the project's existing pinned dependencies and build the frontend first. Run
the app on port 8001 with a working backend OpenAI configuration, then from the
repository root:

```sh
node frontend/tooling/capture-demo.mjs
node frontend/tooling/validate-demo.mjs
```

**Capture sends one real question and its retrieved sample context to OpenAI.** It
is opt-in and never part of CI. Before sending it, the script checks that the app
contains exactly the three public sample filenames and that their originals match
this repository's PDFs byte-for-byte. Credentials remain on the backend.

Validation uses no paid API. It serves the local video temporarily on loopback,
checks decoding, playback, dimensions and seeking with Playwright, then generates
the poster and GIF using the existing pinned Pillow installation. The temporary
server and frame files are removed afterwards. Playwright's already-installed
FFmpeg binary handles recording; no additional packages are installed.

The README uses an animated image and a full-resolution video link so the demo
remains usable in Markdown viewers that do not embed video players. Download the
WebM if your viewer does not offer inline playback.
