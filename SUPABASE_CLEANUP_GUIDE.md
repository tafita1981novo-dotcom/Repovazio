# Guia: Deletar Edge Functions Orfãs no Supabase
## 85 funções para deletar → liberar slots → deploy novos EF

### LINK DIRETO:
https://supabase.com/dashboard/project/tpjvalzwkqwttvmszvie/functions

### MANTER (não deletar):
- cases-bootstrap
- cases-researcher
- cerebro-autonomo
- daniela-admin
- daniela-app
- daniela-chat
- github-run-logs
- github-workflow-status
- piloto-prepare
- render-trigger
- social-publisher
- video-generator
- videos-page-publisher
- youtube-publisher

### DELETAR (85 funções):
 1. add-browser
 2. analytics-collector
 3. app-runtime
 4. assemble-and-commit-v10
 5. assemble-v10
 6. audit-youtube
 7. commit-chat
 8. commit-chatia
 9. commit-chatia-v3
10. commit-executor-v7
11. commit-from-cache
12. commit-from-chunks
13. commit-ia-executor
14. commit-ia-v6
15. commit-learn
16. commit-route
17. commit-route-final
18. commit-skills
19. commit-v10-final
20. commit-v10-final2
21. commit-v10-now
22. commit-v8-route
23. commit-v9-runner
24. commit-v9d
25. connectors-api
26. create-vercel-project
27. debug-envs
28. debug-sbk
29. debug-secret-key
30. deploy-v9
31. do-commit-v10
32. do-commit-v9
33. exec-sql
34. fix-and-upgrade
35. fix-browser-route
36. fix-chat-upload2
37. fix-cron-route
38. fix-monitor-now
39. gh-commit
40. github-commit
41. github-commits
42. github-job-log
43. github-secrets-setup
44. github-secrets-setup-all
45. github-step-log
46. github-workflow-fix
47. github-workflow-yaml
48. github-yaml-view
49. intelligence-engine
50. mp4-upload
51. read-file
52. render-one
53. run-now
54. store-v6-p1
55. test-b64-len
56. test-pat
57. trigger
58. trigger-commit
59. upgrade-chat-upload
60. v10-assemble-commit
61. v10-chunk-test
62. v10-commit-pat
63. v10-commit-real
64. v10-final-commit
65. v10-go
66. v10-p0
67. v10-trigger
68. v11-assemble-commit
69. v11-commit-chunks
70. v11-debug
71. v11-final-commit
72. v11-fix-parts
73. v11-fix-together
74. v12-all-inserter
75. v12-assemble-commit
76. v12-ins-01
77. v12-insert-p4p9
78. v12-insert-p7
79. v12-insert-p7-exact
80. v12-kv-store
81. v12-micro-p0
82. v12-p7-final
83. v12-p7-native
84. v12-p7-v2
85. v12-p8-fn

### COMO DELETAR:
1. Abrir link acima no browser
2. Clicar em cada função da lista DELETAR
3. Settings → Delete Function
4. Confirmar

OU via CLI Supabase:
```bash
supabase functions delete <nome> --project-ref tpjvalzwkqwttvmszvie
```

### DEPOIS DE DELETAR:
- Vai liberar ~65 slots
- Executar: python3 scripts/gumroad_publisher.py (após GUMROAD_ACCESS_TOKEN)
- GitHub Actions voltam a fazer deploy automático
