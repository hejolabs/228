현재 작업 상태를 git commit으로 저장해줘.

1. `git status`로 변경사항 확인
2. 변경사항이 있으면 `git add -A` 후 커밋 (Co-Authored-By 줄은 절대 붙이지 마)
3. 커밋 메시지: "$ARGUMENTS" (인자가 없으면 현재 작업 내용을 요약해서 작성)
4. 커밋 후 `git log --oneline -3`으로 최근 3개 커밋을 보여줘
5. 마지막에 아래 형식으로 요약해줘:

```
--- SAVE 완료 ---
커밋 해시: [short hash]
메시지: [커밋 메시지]
브랜치: [현재 브랜치]
롤백 명령: /rollback [short hash]
```
