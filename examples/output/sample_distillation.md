# Novel Distiller 2.0

## 范围与元数据

<!-- canonical:metadata -->
```json
{
  "actual_scope": "full\\_text",
  "author": null,
  "input_type": "attachment",
  "output_language": "zh-CN",
  "requested_focus": [
    "characters",
    "plots",
    "relationships",
    "foreshadowing",
    "timeline",
    "style"
  ],
  "requested_scope": "full\\_text",
  "sources": [
    {
      "chapters": [
        {
          "chapter_id": "ch-001",
          "title": "站台"
        }
      ],
      "chunks": [
        {
          "chapter_id": "ch-001",
          "chunk_id": "chunk-001",
          "span": {
            "type": "paragraph",
            "value": "p001-p003"
          }
        }
      ],
      "fingerprint": null,
      "readable": true,
      "source_id": "source-001",
      "type": "attachment"
    }
  ],
  "title": "雨站"
}
```

## 核心摘要

<!-- canonical:summary -->
```json
"林舟调查失踪事件。"
```

## 人物

<!-- canonical:characters -->
```json
[
  {
    "aliases": [],
    "arc": {
      "claim_status": "inference",
      "confidence": "medium",
      "evidence": [
        {
          "chapter_id": "ch-001",
          "chunk_id": "chunk-001",
          "locator": {
            "type": "paragraph",
            "value": "p001"
          },
          "purpose": "support",
          "source_id": "source-001"
        }
      ],
      "notes": null,
      "text": "开始怀疑记忆"
    },
    "claim_status": "fact",
    "confidence": "high",
    "description": "调查者",
    "evidence": [
      {
        "chapter_id": "ch-001",
        "chunk_id": "chunk-001",
        "locator": {
          "type": "paragraph",
          "value": "p001"
        },
        "purpose": "support",
        "quote": "雨落在站台上",
        "source_id": "source-001"
      }
    ],
    "first_appearance": {
      "type": "paragraph",
      "value": "p001"
    },
    "goals": [
      {
        "claim_status": "inference",
        "confidence": "medium",
        "evidence": [
          {
            "chapter_id": "ch-001",
            "chunk_id": "chunk-001",
            "locator": {
              "type": "paragraph",
              "value": "p001"
            },
            "purpose": "support",
            "source_id": "source-001"
          }
        ],
        "notes": null,
        "text": "寻找真相"
      }
    ],
    "id": "char-001",
    "name": "林舟",
    "notes": null,
    "role": "protagonist",
    "traits": [
      {
        "claim_status": "inference",
        "confidence": "medium",
        "evidence": [
          {
            "chapter_id": "ch-001",
            "chunk_id": "chunk-001",
            "locator": {
              "type": "paragraph",
              "value": "p001"
            },
            "purpose": "support",
            "source_id": "source-001"
          }
        ],
        "notes": null,
        "text": "谨慎"
      }
    ]
  },
  {
    "aliases": [],
    "arc": {
      "claim_status": "inference",
      "confidence": "medium",
      "evidence": [
        {
          "chapter_id": "ch-001",
          "chunk_id": "chunk-001",
          "locator": {
            "type": "paragraph",
            "value": "p001"
          },
          "purpose": "support",
          "source_id": "source-001"
        }
      ],
      "notes": null,
      "text": "下落未明"
    },
    "claim_status": "fact",
    "confidence": "high",
    "description": "失踪者",
    "evidence": [
      {
        "chapter_id": "ch-001",
        "chunk_id": "chunk-001",
        "locator": {
          "type": "paragraph",
          "value": "p001"
        },
        "purpose": "support",
        "source_id": "source-001"
      }
    ],
    "first_appearance": {
      "type": "paragraph",
      "value": "p001"
    },
    "goals": [],
    "id": "char-002",
    "name": "林遥",
    "notes": null,
    "role": "supporting",
    "traits": []
  }
]
```

## 情节

<!-- canonical:plots -->
```json
[
  {
    "causes": [
      {
        "claim_status": "inference",
        "confidence": "medium",
        "evidence": [
          {
            "chapter_id": "ch-001",
            "chunk_id": "chunk-001",
            "locator": {
              "type": "paragraph",
              "value": "p001"
            },
            "purpose": "support",
            "source_id": "source-001"
          }
        ],
        "notes": null,
        "text": "收到线索"
      }
    ],
    "claim_status": "fact",
    "confidence": "high",
    "effects": [
      {
        "claim_status": "inference",
        "confidence": "medium",
        "evidence": [
          {
            "chapter_id": "ch-001",
            "chunk_id": "chunk-001",
            "locator": {
              "type": "paragraph",
              "value": "p001"
            },
            "purpose": "support",
            "source_id": "source-001"
          }
        ],
        "notes": null,
        "text": "前往北桥"
      }
    ],
    "evidence": [
      {
        "chapter_id": "ch-001",
        "chunk_id": "chunk-001",
        "locator": {
          "type": "paragraph",
          "value": "p001"
        },
        "purpose": "support",
        "source_id": "source-001"
      }
    ],
    "id": "plot-001",
    "locations": [
      "车站"
    ],
    "notes": null,
    "participants": [
      "char-001"
    ],
    "resolution_status": "open",
    "summary": "寻找线索",
    "title": "调查",
    "turning_point": {
      "claim_status": "inference",
      "confidence": "medium",
      "evidence": [
        {
          "chapter_id": "ch-001",
          "chunk_id": "chunk-001",
          "locator": {
            "type": "paragraph",
            "value": "p001"
          },
          "purpose": "support",
          "source_id": "source-001"
        }
      ],
      "notes": null,
      "text": "发现录音"
    },
    "type": "main"
  }
]
```

## 人物关系

<!-- canonical:relationships -->
```json
[
  {
    "claim_status": "fact",
    "confidence": "high",
    "description": "兄妹",
    "direction": "mutual",
    "evidence": [
      {
        "chapter_id": "ch-001",
        "chunk_id": "chunk-001",
        "locator": {
          "type": "paragraph",
          "value": "p001"
        },
        "purpose": "support",
        "source_id": "source-001"
      }
    ],
    "evolution": [],
    "id": "rel-001",
    "notes": null,
    "source_character_id": "char-001",
    "strength": "strong",
    "target_character_id": "char-002",
    "type": "siblings"
  }
]
```

## 伏笔

<!-- canonical:foreshadowing -->
```json
[
  {
    "claim_status": "inference",
    "confidence": "medium",
    "evidence": [
      {
        "chapter_id": "ch-001",
        "chunk_id": "chunk-001",
        "locator": {
          "type": "paragraph",
          "value": "p001"
        },
        "purpose": "setup",
        "source_id": "source-001"
      }
    ],
    "id": "fore-001",
    "notes": null,
    "payoff": null,
    "setup": {
      "claim_status": "inference",
      "confidence": "medium",
      "evidence": [
        {
          "chapter_id": "ch-001",
          "chunk_id": "chunk-001",
          "locator": {
            "type": "paragraph",
            "value": "p001"
          },
          "purpose": "support",
          "source_id": "source-001"
        }
      ],
      "notes": null,
      "text": "纽扣出现"
    },
    "status": "unresolved"
  }
]
```

## 时间线

<!-- canonical:timeline -->
```json
[
  {
    "chronology_position": 1,
    "claim_status": "fact",
    "confidence": "high",
    "duration": null,
    "event": "到达车站",
    "evidence": [
      {
        "chapter_id": "ch-001",
        "chunk_id": "chunk-001",
        "locator": {
          "type": "paragraph",
          "value": "p001"
        },
        "purpose": "support",
        "source_id": "source-001"
      }
    ],
    "explicit_time": null,
    "id": "time-001",
    "mode": "linear",
    "narration_position": 1,
    "notes": null,
    "participants": [
      "char-001"
    ],
    "relative_time": "调查开始"
  }
]
```

## 风格

<!-- canonical:style -->
```json
[
  {
    "aspect": "viewpoint",
    "claim_status": "inference",
    "confidence": "medium",
    "evidence": [
      {
        "chapter_id": "ch-001",
        "chunk_id": "chunk-001",
        "locator": {
          "type": "paragraph",
          "value": "p001"
        },
        "purpose": "style\\_example",
        "source_id": "source-001"
      }
    ],
    "id": "style-001",
    "notes": null,
    "observation": "限知视角",
    "scope": "全部输入"
  }
]
```

## 不确定项与矛盾

<!-- canonical:uncertainties -->
```json
[
  {
    "alternatives": [
      "仍然失踪",
      "主动离开"
    ],
    "category": "ending",
    "claim_status": "uncertain",
    "confidence": "high",
    "description": "下落未知",
    "evidence": [
      {
        "chapter_id": "ch-001",
        "chunk_id": "chunk-001",
        "locator": {
          "type": "paragraph",
          "value": "p001"
        },
        "purpose": "contradiction",
        "source_id": "source-001"
      }
    ],
    "id": "uncertain-001",
    "notes": "输入没有结局",
    "related_ids": [
      "plot-001"
    ]
  }
]
```

## 覆盖范围与质量检查

<!-- canonical:quality -->
```json
{
  "actual_scope": "full\\_text",
  "checks": [
    {
      "name": "schema",
      "status": "pass"
    }
  ],
  "coverage": {
    "chunks_failed": 0,
    "chunks_processed": 1,
    "chunks_total": 1,
    "chunks_unreadable": 0,
    "percentage": 100
  },
  "limitations": [
    "短篇示例"
  ],
  "requested_scope": "full\\_text",
  "status": "completed"
}
```

<!-- canonical-document-base64
eyJjaGFyYWN0ZXJzIjpbeyJhbGlhc2VzIjpbXSwiYXJjIjp7ImNsYWltX3N0YXR1cyI6ImluZmVyZW5jZSIsImNvbmZpZGVuY2UiOiJtZWRpdW0iLCJldmlkZW5jZSI6W3siY2hhcHRlcl9pZCI6ImNoLTAwMSIsImNodW5rX2lkIjoiY2h1bmstMDAxIiwibG9jYXRvciI6eyJ0eXBlIjoicGFyYWdyYXBoIiwidmFsdWUiOiJwMDAxIn0sInB1cnBvc2UiOiJzdXBwb3J0Iiwic291cmNlX2lkIjoic291cmNlLTAwMSJ9XSwibm90ZXMiOm51bGwsInRleHQiOiLlvIDlp4vmgIDnlpHorrDlv4YifSwiY2xhaW1fc3RhdHVzIjoiZmFjdCIsImNvbmZpZGVuY2UiOiJoaWdoIiwiZGVzY3JpcHRpb24iOiLosIPmn6XogIUiLCJldmlkZW5jZSI6W3siY2hhcHRlcl9pZCI6ImNoLTAwMSIsImNodW5rX2lkIjoiY2h1bmstMDAxIiwibG9jYXRvciI6eyJ0eXBlIjoicGFyYWdyYXBoIiwidmFsdWUiOiJwMDAxIn0sInB1cnBvc2UiOiJzdXBwb3J0IiwicXVvdGUiOiLpm6jokL3lnKjnq5nlj7DkuIoiLCJzb3VyY2VfaWQiOiJzb3VyY2UtMDAxIn1dLCJmaXJzdF9hcHBlYXJhbmNlIjp7InR5cGUiOiJwYXJhZ3JhcGgiLCJ2YWx1ZSI6InAwMDEifSwiZ29hbHMiOlt7ImNsYWltX3N0YXR1cyI6ImluZmVyZW5jZSIsImNvbmZpZGVuY2UiOiJtZWRpdW0iLCJldmlkZW5jZSI6W3siY2hhcHRlcl9pZCI6ImNoLTAwMSIsImNodW5rX2lkIjoiY2h1bmstMDAxIiwibG9jYXRvciI6eyJ0eXBlIjoicGFyYWdyYXBoIiwidmFsdWUiOiJwMDAxIn0sInB1cnBvc2UiOiJzdXBwb3J0Iiwic291cmNlX2lkIjoic291cmNlLTAwMSJ9XSwibm90ZXMiOm51bGwsInRleHQiOiLlr7vmib7nnJ/nm7gifV0sImlkIjoiY2hhci0wMDEiLCJuYW1lIjoi5p6X6IifIiwibm90ZXMiOm51bGwsInJvbGUiOiJwcm90YWdvbmlzdCIsInRyYWl0cyI6W3siY2xhaW1fc3RhdHVzIjoiaW5mZXJlbmNlIiwiY29uZmlkZW5jZSI6Im1lZGl1bSIsImV2aWRlbmNlIjpbeyJjaGFwdGVyX2lkIjoiY2gtMDAxIiwiY2h1bmtfaWQiOiJjaHVuay0wMDEiLCJsb2NhdG9yIjp7InR5cGUiOiJwYXJhZ3JhcGgiLCJ2YWx1ZSI6InAwMDEifSwicHVycG9zZSI6InN1cHBvcnQiLCJzb3VyY2VfaWQiOiJzb3VyY2UtMDAxIn1dLCJub3RlcyI6bnVsbCwidGV4dCI6IuiwqOaFjiJ9XX0seyJhbGlhc2VzIjpbXSwiYXJjIjp7ImNsYWltX3N0YXR1cyI6ImluZmVyZW5jZSIsImNvbmZpZGVuY2UiOiJtZWRpdW0iLCJldmlkZW5jZSI6W3siY2hhcHRlcl9pZCI6ImNoLTAwMSIsImNodW5rX2lkIjoiY2h1bmstMDAxIiwibG9jYXRvciI6eyJ0eXBlIjoicGFyYWdyYXBoIiwidmFsdWUiOiJwMDAxIn0sInB1cnBvc2UiOiJzdXBwb3J0Iiwic291cmNlX2lkIjoic291cmNlLTAwMSJ9XSwibm90ZXMiOm51bGwsInRleHQiOiLkuIvokL3mnKrmmI4ifSwiY2xhaW1fc3RhdHVzIjoiZmFjdCIsImNvbmZpZGVuY2UiOiJoaWdoIiwiZGVzY3JpcHRpb24iOiLlpLHouKrogIUiLCJldmlkZW5jZSI6W3siY2hhcHRlcl9pZCI6ImNoLTAwMSIsImNodW5rX2lkIjoiY2h1bmstMDAxIiwibG9jYXRvciI6eyJ0eXBlIjoicGFyYWdyYXBoIiwidmFsdWUiOiJwMDAxIn0sInB1cnBvc2UiOiJzdXBwb3J0Iiwic291cmNlX2lkIjoic291cmNlLTAwMSJ9XSwiZmlyc3RfYXBwZWFyYW5jZSI6eyJ0eXBlIjoicGFyYWdyYXBoIiwidmFsdWUiOiJwMDAxIn0sImdvYWxzIjpbXSwiaWQiOiJjaGFyLTAwMiIsIm5hbWUiOiLmnpfpgaUiLCJub3RlcyI6bnVsbCwicm9sZSI6InN1cHBvcnRpbmciLCJ0cmFpdHMiOltdfV0sImZvcmVzaGFkb3dpbmciOlt7ImNsYWltX3N0YXR1cyI6ImluZmVyZW5jZSIsImNvbmZpZGVuY2UiOiJtZWRpdW0iLCJldmlkZW5jZSI6W3siY2hhcHRlcl9pZCI6ImNoLTAwMSIsImNodW5rX2lkIjoiY2h1bmstMDAxIiwibG9jYXRvciI6eyJ0eXBlIjoicGFyYWdyYXBoIiwidmFsdWUiOiJwMDAxIn0sInB1cnBvc2UiOiJzZXR1cCIsInNvdXJjZV9pZCI6InNvdXJjZS0wMDEifV0sImlkIjoiZm9yZS0wMDEiLCJub3RlcyI6bnVsbCwicGF5b2ZmIjpudWxsLCJzZXR1cCI6eyJjbGFpbV9zdGF0dXMiOiJpbmZlcmVuY2UiLCJjb25maWRlbmNlIjoibWVkaXVtIiwiZXZpZGVuY2UiOlt7ImNoYXB0ZXJfaWQiOiJjaC0wMDEiLCJjaHVua19pZCI6ImNodW5rLTAwMSIsImxvY2F0b3IiOnsidHlwZSI6InBhcmFncmFwaCIsInZhbHVlIjoicDAwMSJ9LCJwdXJwb3NlIjoic3VwcG9ydCIsInNvdXJjZV9pZCI6InNvdXJjZS0wMDEifV0sIm5vdGVzIjpudWxsLCJ0ZXh0Ijoi57q95omj5Ye6546wIn0sInN0YXR1cyI6InVucmVzb2x2ZWQifV0sIm1ldGFkYXRhIjp7ImFjdHVhbF9zY29wZSI6ImZ1bGxfdGV4dCIsImF1dGhvciI6bnVsbCwiaW5wdXRfdHlwZSI6ImF0dGFjaG1lbnQiLCJvdXRwdXRfbGFuZ3VhZ2UiOiJ6aC1DTiIsInJlcXVlc3RlZF9mb2N1cyI6WyJjaGFyYWN0ZXJzIiwicGxvdHMiLCJyZWxhdGlvbnNoaXBzIiwiZm9yZXNoYWRvd2luZyIsInRpbWVsaW5lIiwic3R5bGUiXSwicmVxdWVzdGVkX3Njb3BlIjoiZnVsbF90ZXh0Iiwic291cmNlcyI6W3siY2hhcHRlcnMiOlt7ImNoYXB0ZXJfaWQiOiJjaC0wMDEiLCJ0aXRsZSI6IuermeWPsCJ9XSwiY2h1bmtzIjpbeyJjaGFwdGVyX2lkIjoiY2gtMDAxIiwiY2h1bmtfaWQiOiJjaHVuay0wMDEiLCJzcGFuIjp7InR5cGUiOiJwYXJhZ3JhcGgiLCJ2YWx1ZSI6InAwMDEtcDAwMyJ9fV0sImZpbmdlcnByaW50IjpudWxsLCJyZWFkYWJsZSI6dHJ1ZSwic291cmNlX2lkIjoic291cmNlLTAwMSIsInR5cGUiOiJhdHRhY2htZW50In1dLCJ0aXRsZSI6IumbqOermSJ9LCJwbG90cyI6W3siY2F1c2VzIjpbeyJjbGFpbV9zdGF0dXMiOiJpbmZlcmVuY2UiLCJjb25maWRlbmNlIjoibWVkaXVtIiwiZXZpZGVuY2UiOlt7ImNoYXB0ZXJfaWQiOiJjaC0wMDEiLCJjaHVua19pZCI6ImNodW5rLTAwMSIsImxvY2F0b3IiOnsidHlwZSI6InBhcmFncmFwaCIsInZhbHVlIjoicDAwMSJ9LCJwdXJwb3NlIjoic3VwcG9ydCIsInNvdXJjZV9pZCI6InNvdXJjZS0wMDEifV0sIm5vdGVzIjpudWxsLCJ0ZXh0Ijoi5pS25Yiw57q/57SiIn1dLCJjbGFpbV9zdGF0dXMiOiJmYWN0IiwiY29uZmlkZW5jZSI6ImhpZ2giLCJlZmZlY3RzIjpbeyJjbGFpbV9zdGF0dXMiOiJpbmZlcmVuY2UiLCJjb25maWRlbmNlIjoibWVkaXVtIiwiZXZpZGVuY2UiOlt7ImNoYXB0ZXJfaWQiOiJjaC0wMDEiLCJjaHVua19pZCI6ImNodW5rLTAwMSIsImxvY2F0b3IiOnsidHlwZSI6InBhcmFncmFwaCIsInZhbHVlIjoicDAwMSJ9LCJwdXJwb3NlIjoic3VwcG9ydCIsInNvdXJjZV9pZCI6InNvdXJjZS0wMDEifV0sIm5vdGVzIjpudWxsLCJ0ZXh0Ijoi5YmN5b6A5YyX5qGlIn1dLCJldmlkZW5jZSI6W3siY2hhcHRlcl9pZCI6ImNoLTAwMSIsImNodW5rX2lkIjoiY2h1bmstMDAxIiwibG9jYXRvciI6eyJ0eXBlIjoicGFyYWdyYXBoIiwidmFsdWUiOiJwMDAxIn0sInB1cnBvc2UiOiJzdXBwb3J0Iiwic291cmNlX2lkIjoic291cmNlLTAwMSJ9XSwiaWQiOiJwbG90LTAwMSIsImxvY2F0aW9ucyI6WyLovabnq5kiXSwibm90ZXMiOm51bGwsInBhcnRpY2lwYW50cyI6WyJjaGFyLTAwMSJdLCJyZXNvbHV0aW9uX3N0YXR1cyI6Im9wZW4iLCJzdW1tYXJ5Ijoi5a+75om+57q/57SiIiwidGl0bGUiOiLosIPmn6UiLCJ0dXJuaW5nX3BvaW50Ijp7ImNsYWltX3N0YXR1cyI6ImluZmVyZW5jZSIsImNvbmZpZGVuY2UiOiJtZWRpdW0iLCJldmlkZW5jZSI6W3siY2hhcHRlcl9pZCI6ImNoLTAwMSIsImNodW5rX2lkIjoiY2h1bmstMDAxIiwibG9jYXRvciI6eyJ0eXBlIjoicGFyYWdyYXBoIiwidmFsdWUiOiJwMDAxIn0sInB1cnBvc2UiOiJzdXBwb3J0Iiwic291cmNlX2lkIjoic291cmNlLTAwMSJ9XSwibm90ZXMiOm51bGwsInRleHQiOiLlj5HnjrDlvZXpn7MifSwidHlwZSI6Im1haW4ifV0sInF1YWxpdHkiOnsiYWN0dWFsX3Njb3BlIjoiZnVsbF90ZXh0IiwiY2hlY2tzIjpbeyJuYW1lIjoic2NoZW1hIiwic3RhdHVzIjoicGFzcyJ9XSwiY292ZXJhZ2UiOnsiY2h1bmtzX2ZhaWxlZCI6MCwiY2h1bmtzX3Byb2Nlc3NlZCI6MSwiY2h1bmtzX3RvdGFsIjoxLCJjaHVua3NfdW5yZWFkYWJsZSI6MCwicGVyY2VudGFnZSI6MTAwfSwibGltaXRhdGlvbnMiOlsi55+t56+H56S65L6LIl0sInJlcXVlc3RlZF9zY29wZSI6ImZ1bGxfdGV4dCIsInN0YXR1cyI6ImNvbXBsZXRlZCJ9LCJyZWxhdGlvbnNoaXBzIjpbeyJjbGFpbV9zdGF0dXMiOiJmYWN0IiwiY29uZmlkZW5jZSI6ImhpZ2giLCJkZXNjcmlwdGlvbiI6IuWFhOWmuSIsImRpcmVjdGlvbiI6Im11dHVhbCIsImV2aWRlbmNlIjpbeyJjaGFwdGVyX2lkIjoiY2gtMDAxIiwiY2h1bmtfaWQiOiJjaHVuay0wMDEiLCJsb2NhdG9yIjp7InR5cGUiOiJwYXJhZ3JhcGgiLCJ2YWx1ZSI6InAwMDEifSwicHVycG9zZSI6InN1cHBvcnQiLCJzb3VyY2VfaWQiOiJzb3VyY2UtMDAxIn1dLCJldm9sdXRpb24iOltdLCJpZCI6InJlbC0wMDEiLCJub3RlcyI6bnVsbCwic291cmNlX2NoYXJhY3Rlcl9pZCI6ImNoYXItMDAxIiwic3RyZW5ndGgiOiJzdHJvbmciLCJ0YXJnZXRfY2hhcmFjdGVyX2lkIjoiY2hhci0wMDIiLCJ0eXBlIjoic2libGluZ3MifV0sInNjaGVtYV92ZXJzaW9uIjoiMi4wLjAiLCJzdHlsZSI6W3siYXNwZWN0Ijoidmlld3BvaW50IiwiY2xhaW1fc3RhdHVzIjoiaW5mZXJlbmNlIiwiY29uZmlkZW5jZSI6Im1lZGl1bSIsImV2aWRlbmNlIjpbeyJjaGFwdGVyX2lkIjoiY2gtMDAxIiwiY2h1bmtfaWQiOiJjaHVuay0wMDEiLCJsb2NhdG9yIjp7InR5cGUiOiJwYXJhZ3JhcGgiLCJ2YWx1ZSI6InAwMDEifSwicHVycG9zZSI6InN0eWxlX2V4YW1wbGUiLCJzb3VyY2VfaWQiOiJzb3VyY2UtMDAxIn1dLCJpZCI6InN0eWxlLTAwMSIsIm5vdGVzIjpudWxsLCJvYnNlcnZhdGlvbiI6IumZkOefpeinhuinkiIsInNjb3BlIjoi5YWo6YOo6L6T5YWlIn1dLCJzdW1tYXJ5Ijoi5p6X6Iif6LCD5p+l5aSx6Liq5LqL5Lu244CCIiwidGltZWxpbmUiOlt7ImNocm9ub2xvZ3lfcG9zaXRpb24iOjEsImNsYWltX3N0YXR1cyI6ImZhY3QiLCJjb25maWRlbmNlIjoiaGlnaCIsImR1cmF0aW9uIjpudWxsLCJldmVudCI6IuWIsOi+vui9puermSIsImV2aWRlbmNlIjpbeyJjaGFwdGVyX2lkIjoiY2gtMDAxIiwiY2h1bmtfaWQiOiJjaHVuay0wMDEiLCJsb2NhdG9yIjp7InR5cGUiOiJwYXJhZ3JhcGgiLCJ2YWx1ZSI6InAwMDEifSwicHVycG9zZSI6InN1cHBvcnQiLCJzb3VyY2VfaWQiOiJzb3VyY2UtMDAxIn1dLCJleHBsaWNpdF90aW1lIjpudWxsLCJpZCI6InRpbWUtMDAxIiwibW9kZSI6ImxpbmVhciIsIm5hcnJhdGlvbl9wb3NpdGlvbiI6MSwibm90ZXMiOm51bGwsInBhcnRpY2lwYW50cyI6WyJjaGFyLTAwMSJdLCJyZWxhdGl2ZV90aW1lIjoi6LCD5p+l5byA5aeLIn1dLCJ1bmNlcnRhaW50aWVzIjpbeyJhbHRlcm5hdGl2ZXMiOlsi5LuN54S25aSx6LiqIiwi5Li75Yqo56a75byAIl0sImNhdGVnb3J5IjoiZW5kaW5nIiwiY2xhaW1fc3RhdHVzIjoidW5jZXJ0YWluIiwiY29uZmlkZW5jZSI6ImhpZ2giLCJkZXNjcmlwdGlvbiI6IuS4i+iQveacquefpSIsImV2aWRlbmNlIjpbeyJjaGFwdGVyX2lkIjoiY2gtMDAxIiwiY2h1bmtfaWQiOiJjaHVuay0wMDEiLCJsb2NhdG9yIjp7InR5cGUiOiJwYXJhZ3JhcGgiLCJ2YWx1ZSI6InAwMDEifSwicHVycG9zZSI6ImNvbnRyYWRpY3Rpb24iLCJzb3VyY2VfaWQiOiJzb3VyY2UtMDAxIn1dLCJpZCI6InVuY2VydGFpbi0wMDEiLCJub3RlcyI6Iui+k+WFpeayoeaciee7k+WxgCIsInJlbGF0ZWRfaWRzIjpbInBsb3QtMDAxIl19XX0=
-->
