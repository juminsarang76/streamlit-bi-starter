#!/bin/bash
# Claude Code 세션을 시작하여 /loop를 설정
# PC 시작 시 launchd(macOS) 또는 systemd(Linux)로 호출하는 것을 상정

WORK_DIR="$HOME/info-collector"
cd "$WORK_DIR"

# reports 디렉토리가 없으면 생성
mkdir -p reports

echo "정보 수집 루프를 시작합니다"