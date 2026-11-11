# Summary: AI adoption survey (Example Org (fictional), synthetic data)

- Source: `survey_export_synthetic.csv`
- Respondents: 200 completed of 210 started
- Mapping: 19 fields, 0 warnings (see mapping.md)
- Departments not shown (n<5): Legal (n=3)

## Key figures

|                                       | Value   |
|:--------------------------------------|:--------|
| n                                     | 200     |
| Uses AI at work (monthly or more)     | 62%     |
| Uses AI weekly or more                | 47%     |
| Uses AI daily or more                 | 27%     |
| Mean minutes saved per week (users)   | 93      |
| Median minutes saved per week (users) | 96      |
| Only positive feelings                | 36%     |
| Agrees: worried about own job         | 47%     |
| Persona: Champion                     | 12%     |
| Persona: Pragmatist                   | 35%     |
| Persona: Curious starter              | 18%     |
| Persona: Sceptic                      | 34%     |

## Themes (mean 1-7)

| Theme   |   Mean (1-7) |
|:--------|-------------:|
| Skills  |         3.47 |
| Support |         3.46 |
| Value   |         3.52 |

## Statements

| Theme   | Item   | Statement                                |   n |   Mean (1-7) |   % agree (5-7) |
|:--------|:-------|:-----------------------------------------|----:|-------------:|----------------:|
| Skills  | s1     | I know how to use AI tools safely        | 200 |         3.46 |            0.28 |
| Skills  | s2     | I can judge whether AI output is correct | 200 |         3.48 |            0.24 |
| Support | s3     | My manager encourages me to try AI tools | 200 |         4.06 |            0.38 |
| Support | s4     | Our guidelines on AI use are clear       | 200 |         2.79 |            0.16 |
| Support | s5     | I have enough time to learn new tools    | 200 |         3.52 |            0.26 |
| Value   | s6     | AI improves the quality of my work       | 200 |         3.56 |            0.25 |
| Value   | s7     | AI saves me time on routine work         | 200 |         3.48 |            0.26 |

## Significance tests

| Test                                 |   chi2 |   df | p      |   cramers_v |   share_expected_below_5 |   n | Left out (n<5)   |
|:-------------------------------------|-------:|-----:|:-------|------------:|-------------------------:|----:|:-----------------|
| Department x weekly use (chi-square) | 23.007 |    4 | <0.001 |       0.342 |                        0 | 197 | Legal (n=3)      |

| Item   |   Mean weekly+ |   Mean less often |   n1 |   n2 |      U | p      | p (BH)   |     r |
|:-------|---------------:|------------------:|-----:|-----:|-------:|:-------|:---------|------:|
| s1     |          3.883 |             3.085 |   94 |  106 | 6484.5 | <0.001 | <0.001   | 0.302 |
| s2     |          3.989 |             3.028 |   94 |  106 | 6906   | <0.001 | <0.001   | 0.386 |
| s3     |          4.553 |             3.613 |   94 |  106 | 6807   | <0.001 | <0.001   | 0.366 |
| s4     |          3.223 |             2.406 |   94 |  106 | 6773   | <0.001 | <0.001   | 0.359 |
| s5     |          3.989 |             3.113 |   94 |  106 | 6624.5 | <0.001 | <0.001   | 0.33  |
| s6     |          3.926 |             3.236 |   94 |  106 | 6296   | 0.001  | 0.001    | 0.264 |
| s7     |          3.83  |             3.16  |   94 |  106 | 6119.5 | 0.005  | 0.005    | 0.228 |

## Per department

|                                       |   Operations |   Finance |    IT |    HR |   Sales |
|:--------------------------------------|-------------:|----------:|------:|------:|--------:|
| n                                     |        66    |     41    | 37    | 23    |   30    |
| Uses AI at work (monthly or more)     |         0.48 |      0.59 |  0.84 |  0.43 |    0.87 |
| Uses AI weekly or more                |         0.3  |      0.46 |  0.76 |  0.35 |    0.6  |
| Uses AI daily or more                 |         0.12 |      0.24 |  0.51 |  0.22 |    0.4  |
| Mean minutes saved per week (users)   |       100.38 |     87.65 | 84    | 72.4  |  109    |
| Median minutes saved per week (users) |       101    |    104    | 86    | 66    |  108    |
| Only positive feelings                |         0.36 |      0.34 |  0.35 |  0.3  |    0.43 |
| Agrees: worried about own job         |         0.52 |      0.49 |  0.43 |  0.43 |    0.4  |
| Persona: Champion                     |         0.05 |      0.2  |  0.19 |  0.09 |    0.1  |
| Persona: Pragmatist                   |         0.26 |      0.27 |  0.57 |  0.26 |    0.5  |
| Persona: Curious starter              |         0.26 |      0.2  |  0.11 |  0.26 |    0.07 |
| Persona: Sceptic                      |         0.44 |      0.34 |  0.14 |  0.39 |    0.33 |
| Theme: Skills                         |         3.28 |      3.55 |  3.68 |  3.33 |    3.6  |
| Theme: Support                        |         3.25 |      3.56 |  3.64 |  3.61 |    3.41 |
| Theme: Value                          |         3.33 |      3.72 |  3.74 |  3.46 |    3.37 |

## Persona profile (illustrative rules)

| Persona         |   n |   Skills |   Support |   Value | Top barriers                                                         |
|:----------------|----:|---------:|----------:|--------:|:---------------------------------------------------------------------|
| Champion        |  24 |     4.92 |      5.04 |    5.58 | Lack of time (10); Lack of training (8); Output is not reliable (8)  |
| Pragmatist      |  70 |     3.6  |      3.54 |    3.29 | Lack of training (25); Unclear rules (21); No access to tools (20)   |
| Curious starter |  37 |     4.09 |      3.99 |    4.47 | Lack of training (14); Lack of time (11); Data privacy concerns (10) |
| Sceptic         |  69 |     2.5  |      2.54 |    2.51 | Data privacy concerns (25); Lack of time (25); Unclear rules (20)    |

## Benchmark (synthetic, matching questions only)

| Measure                                |   Survey % |   Survey n |   Benchmark % |   Benchmark n |
|:---------------------------------------|-----------:|-----------:|--------------:|--------------:|
| Uses AI weekly or more                 |      0.47  |        200 |         0.458 |           600 |
| Agrees: guidelines on AI use are clear |      0.155 |        200 |         0.296 |           493 |
| Agrees: worried about own job          |      0.47  |        198 |         0.525 |           600 |

Not compared: manager_support_yesno (yes/no question in benchmark, 7-point statement (s3) in survey)
