# Unit 4 MCP verification

- Unit 3 baseline commit: `637569bfb423a7abfafcf81044f87c5ca33e571e`
- Criteria SHA256: `e0c23c191dffa83722910db3a82c663db8ca7c784dbb69c00f6bddea8a11dbba`
- Only `search_listings` moves onto MCP. Both model-calling tools stay direct.

## Environment check
```text

AI201 environment check
------------------------------------------------------------
[PASS] Python version
         3.12.14 on Linux
[PASS] Virtual environment
         /workspace/scratch/02be30af1424/fitfindr-audit/.venv
[PASS] Pinned packages
         all 5 import cleanly
[PASS] Free disk space
         27.0 GB
[PASS] Memory
         9.7 GB
[PASS] Key hygiene
         .env is ignored by git
[PASS] API key
         loaded, 53 characters
[PASS] MCP
         server and client both import
[PASS] Project data
         40 listings, 10 wardrobe items
[PASS] Model call
         gemini-3.5-flash-lite replied "Ready"
------------------------------------------------------------
10 passed, 0 failed, 0 to look at, 0 skipped

You're set. See you in class.


```
## Before the MCP move
```text

  Found:    Graphic Tee — 2003 Tour Bootleg Style — $24.0 on depop

  Outfit:   1) Graphic Tee — 2003 Tour Bootleg Style layered under a Black cropped zip hoodie with Baggy straight-leg jeans, dark wash and Chunky white sneakers
2) Graphic Tee — 2003 Tour Bootleg Style paired with Wide-leg khaki trousers and Black combat boots

  Fit card: Scored this amazing secondhand Graphic Tee — 2003 Tour Bootleg Style for just $24.00 on depop, and it is so versatile to style. Layered it under a black cropped zip hoodie with baggy straight-leg jeans and chunky white sneakers for a chill vibe. For a different look, it looks equally cool paired with wide-leg khaki trousers and black combat boots.

2 model calls this session, 322 prompt + 144 output tokens

```
## MCP registration
```text
Asking mcp_server.py what it offers…

  search_listings
    Search secondhand listings by description (string), optional size (string), and optional inclusive max_price (number in US dollars); return ranked listing dictionaries, or [] when nothing matches.
    - description: string
    - size: string  (optional)
    - max_price: number  (optional)


```
## Direct versus MCP search results
```json
[
  {
    "inputs": {
      "description": "vintage graphic tee",
      "size": "M",
      "max_price": 30.0
    },
    "direct_ids": [
      "lst_002"
    ],
    "mcp_ids": [
      "lst_002"
    ],
    "equal": true
  },
  {
    "inputs": {
      "description": "vintage graphic tee",
      "size": null,
      "max_price": 30.0
    },
    "direct_ids": [
      "lst_006",
      "lst_033",
      "lst_002"
    ],
    "mcp_ids": [
      "lst_006",
      "lst_033",
      "lst_002"
    ],
    "equal": true
  },
  {
    "inputs": {
      "description": "designer ballgown",
      "size": "XXS",
      "max_price": 5.0
    },
    "direct_ids": [],
    "mcp_ids": [],
    "equal": true
  }
]
```
- All three native lists matched exactly, including the empty list.
- See `unit4-mcp-and-prehandler.json` for the live full query after the move and the invalid-key trigger before adding the required failure message.
