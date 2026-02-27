지정한 git 커밋으로 롤백해줘.

대상: $ARGUMENTS

1. 먼저 `git log --oneline -10`으로 최근 커밋 목록을 보여줘
2. 인자가 있으면 해당 해시로, 없으면 직전 커밋(HEAD~1)으로 롤백
3. `git reset --hard [대상 해시]`로 롤백 실행
4. 롤백 후 `git log --oneline -3`과 `git status`를 보여줘
5. 마지막에 아래 형식으로 요약해줘:

```
--- ROLLBACK 완료 ---
롤백 대상: [해시]
현재 HEAD: [short hash]
메시지: [현재 HEAD 커밋 메시지]
브랜치: [현재 브랜치]
```

주의: 롤백하면 이후 변경사항이 모두 사라짐을 사용자에게 알려줘.
