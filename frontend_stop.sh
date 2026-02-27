#!/bin/bash
kill $(lsof -ti:5173) 2>/dev/null && echo "프론트엔드 종료 완료" || echo "프론트엔드가 실행 중이 아닙니다"
