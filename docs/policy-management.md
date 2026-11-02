# Policy management

[Back to the README](../README.md)

NorthStar and the bundled policies are fictional. The seed documents cover:

- [AI acceptable use](../documents/northstar-ai-acceptable-use-policy.pdf).
- [Information security and data handling](../documents/northstar-information-security-policy.pdf).
- [Employee handbook](../documents/northstar-employee-handbook.pdf).

## Manage documents

Open **Manage policies** in the header or visit `/policies`.

- Upload one PDF, HTML or UTF-8 text file at a time.
- Read extracted content and download the original file.
- Rename the display title without changing the original filename or stable identity.
- Delete a policy after confirmation to remove it from future answers.
- Inspect chunks, source locations, applied settings and processing status.
- Retry a failed upload or delete it. Duplicate original filenames are rejected.

Previous answers remain historical snapshots. Sample questions requiring a deleted policy disappear.

## Upload limits

| Limit | Value |
| --- | --- |
| File size | 20 MiB |
| PDF pages | 1,000 |
| Extracted text | 2 million characters |
| Chunks per revision | 10,000 |
| Supported files | PDF, HTML/HTM, UTF-8 TXT |

- PDFs must be unencrypted and contain readable text. Scans need OCR beforehand.
- Word documents are not supported.
- HTML is extracted into safe text; scripts are not executed and the original is downloaded as an attachment.

## Chunking

| Strategy | Behaviour |
| --- | --- |
| Character length | Split near whitespace within a character limit |
| Sentences / punctuation | Prefer sentence-ending punctuation |
| Paragraphs | Prefer paragraph boundaries; PDF text blocks preserve separation |
| HTML headings / sections | Group sections up to a chosen heading depth; HTML files only |

- Default: **900 characters**, with **150 characters** of overlap.
- Maximum size: 100–20,000 characters. Overlap must be non-negative and smaller than size.
- Oversized sentences, paragraphs or sections split to fit the size limit.
- Overlap stays within a page or section.
- HTML heading context counts toward the limit; overlap must leave room for it.
- Chunk source spans refer to saved sections. Repeated HTML heading context is recorded separately.

## Preview and apply

1. Select a policy and open **Chunking settings**.
2. Change the strategy, size, overlap or applicable HTML heading depth.
3. Select **Preview chunks** to inspect the proposed result without changing search.
4. Select **Apply changes** to index and activate those exact chunks.

- Editing settings invalidates the preview.
- The previous revision stays searchable while a replacement is indexed.
- Publication activates the new revision and completes the operation atomically.
- Failed or interrupted processing leaves the previous revision active.
- Processing resumes in the UI after a reload; temporary polling failures reconnect automatically.
- Vector writes are batched. OpenAI embedding inputs are bounded and pooled without changing the stored chunk text.

## Storage and backups

- Managed data lives in `data/policies/`, relative to the parent of `VECTOR_STORE_DIR`.
- It contains original files, the SQLite registry/revisions/operations and managed Chroma vectors.
- Back up the whole directory together while the app is stopped.
- The three bundled PDFs are imported once. Deleting a managed seed policy does not re-import it on restart.
- Generated data and credentials are excluded from Git.
- Run one application process. There is no authentication or multi-user permission layer.

For CLI ingestion, providers and API access, see the [development guide](development.md).
