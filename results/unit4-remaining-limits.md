## What's Still Broken

No committed criterion remains MISSED in the after batch. That is the result of five fixed-scenario tries per criterion, not a guarantee of general reliability.

- **Caption grammar:** After criterion 4 tries 4 and 5 include “Alternatively, would style…” without a clear subject. The captions meet the committed facts/length/ownership checks, but some wording would need editing before posting. I would next revise the prompt for natural complete sentences and add a measurable grammar/usability criterion. I stopped after the one permitted improvement so its effect could be measured separately.
- **Ownership validation:** The caption validator still checks facts, length, and seller phrases; it does not deterministically validate every purchase or possession claim. The revised prompt reduced the observed claims to zero, but future responses could regress. A future change would add a grounded ownership check or a constrained response format and test more listings.
- **Fallback sentence boundaries:** The existing fallback combines listing facts and the first outfit idea. Extra punctuation or several sentences in that idea can produce more than two sentences. It is designed for two sentences, not guaranteed for arbitrary input. I would normalize and check fallback sentence boundaries in a separate improvement; the required invalid-key example stayed readable.
- **Coverage:** The committed model criteria use one tee listing and two fixed wardrobes. Broader descriptions, item categories, and empty-wardrobe captions still need repeated tests. I would tighten future criteria and add those scenarios without altering the original results.

### Submission record

Same repository as Unit 3: [winaung786/ai201-project2-fitfindr-starter-v2026](https://github.com/winaung786/ai201-project2-fitfindr-starter-v2026).

Unit 4 commits follow the milestone order: MCP registration/equality evidence; failure handlers and trace evidence; exact scenarios and logging; before results; diagnoses; one prompt improvement; after results; final write-up. This provides more than the required four new commits. `criteria.md`, `RUNNING.md`, the model/configuration, and both data files retain the Unit 3 contents.

- [x] One tool registered and called through MCP, with typed inputs, dollar units, and an empty-case contract.
- [x] Empty search, empty wardrobe, and model-unavailable cases deliberately triggered and documented.
- [x] Full happy-path and shorter empty-path traces show inputs, results, choices, and the MCP call.
- [x] Five criteria, five tries each, before and after, with actual output for each criterion.
- [x] A verdict for every criterion and a step/mechanism diagnosis for every before miss.
- [x] One prompt change measured with the same agent, data, model, scenarios, and targets.
- [x] Remaining limits and AI use disclosed; no API key included in the repository or evidence.
- [ ] Submit the same repository URL in the course submission page.
