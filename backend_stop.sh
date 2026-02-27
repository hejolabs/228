#!/bin/bash
kill $(lsof -ti:8000) 2>/dev/null && echo "백엔드 종료 완료" || echo "백엔드가 실행 중이 아닙니다"
