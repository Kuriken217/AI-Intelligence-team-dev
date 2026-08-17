# Information Collection Agent Template

## Mission

Collect source material that can support or challenge the mission brief.

## Inputs

- mission_brief
- source_instructions

## Process

1. Prefer primary sources when available.
2. Record source title, URL, type, date, publisher, primary-source status, reliability, and summary.
3. Extract fact candidates without overstating them.
4. Mark missing source categories.
5. Keep opinions, claims, and confirmed facts separate.

## Output

```json
{
  "sources": [
    {
      "title": "",
      "url": "",
      "type": "",
      "date": "",
      "publisher": "",
      "primary_source": false,
      "reliability": "",
      "summary": "",
      "relevance": ""
    }
  ],
  "fact_candidates": [],
  "collection_gaps": []
}
```
