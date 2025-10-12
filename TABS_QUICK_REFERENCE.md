# TABS Quick Reference Card

## Copy-Paste Ready Code

```python
# simple_extractor.py - TABS dictionary
TABS = {
    "Intake": 1366958616,      # Initial participation survey (28 responses)
    "CEO": 1242252865,         # CEO assessment + contacts (3 responses)
    "Tech": 1545410106,        # Tech Lead survey (2 responses)
    "Staff": 377168987,        # Staff survey (4 responses)
    "Questions": 513349220,    # Question bank (67 questions)
    "Key": 1000323612,         # Organization reference (6 entries)
}
```

## Sheet Identification

| Sheet | GID | Structure | Purpose |
|-------|-----|-----------|---------|
| **Intake** | 1366958616 | General questions, no IDs | Initial participation survey |
| **CEO** | 1242252865 | Contact fields + C-* questions | CEO assessment + contact collection |
| **Tech** | 1545410106 | TL-* question IDs | Tech Lead infrastructure survey |
| **Staff** | 377168987 | S-* question IDs | Staff experience survey |
| **Questions** | 513349220 | Question ID → Text mapping | Master question reference |
| **Key** | 1000323612 | Name → URL mapping | Organization lookup |

## Question ID Prefixes

```
C-*   = CEO Survey (25 questions)
TL-*  = Tech Lead Survey (19 questions)
S-*   = Staff Survey (22 questions)
```

## Question Categories

All surveys assess these areas:
- **PT** - Performance Tracking
- **BS** - Business Systems
- **D** - Data Management
- **I** - Infrastructure
- **OC** - Organizational Capacity
- **CTC/TC** - Technology Challenges
- **TIP** - Investment Priorities
- **FC** - Final Comments

## Key Evidence

### Intake (1366958616)
- ✓ AI usage questions
- ✓ Participation readiness
- ✓ No question ID pattern
- ✓ 28 responses (highest)

### CEO (1242252865)
- ✓ "CEO Organization", "CEO Email", "CEO Role" columns
- ✓ "Tech Lead First/Last/Email" columns
- ✓ "Staff 1-5 First/Last/Email" columns
- ✓ C-* question IDs
- ✓ 3 responses

### Tech (1545410106)
- ✓ TL-I-1 through TL-I-14 (Infrastructure)
- ✓ TL-OC-1 through TL-OC-4 (Org Capacity)
- ✓ 2 responses

### Staff (377168987)
- ✓ S-PT-*, S-BS-*, S-D-*, S-I-*, S-OC-* columns
- ✓ Employee perspective questions
- ✓ 4 responses

### Questions (513349220)
- ✓ Columns: Question ID, QUESTION, Answer 1-7
- ✓ 67 questions total
- ✓ Reference table for all surveys

### Key (1000323612)
- ✓ Columns: Name, URL
- ✓ 6 organization entries
- ✓ Lookup/reference table

## Processing Notes

1. **Load Order:** Key → Questions → Intake → CEO → Tech → Staff
2. **Intake:** Process standalone (no question ID mapping needed)
3. **CEO:** Extract contacts + map C-* questions
4. **Tech/Staff:** Map TL-*/S-* questions to question bank
5. **Questions:** Load as reference table first
6. **Key:** Load as organization lookup
7. **Summary (GID 0):** Skip or process separately

## Response Stats

```
Intake:  28 responses ████████████████████████████ (100%)
CEO:      3 responses ███                          (10.7%)
Tech:     2 responses ██                           (7.1%)
Staff:    4 responses ████                         (14.3%)
```

**Insight:** High initial interest, low detailed assessment completion

---

*Quick reference for tab mapping - see MAPPING_RESULTS.md for full analysis*
