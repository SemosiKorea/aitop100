# 교동마을 산지직송 카카오톡 CS 에이전트

기존 카카오톡 `MESSAGE_CREATE` 웹훅을 수신하고, 정책 지식과 AI TOP 100 액션 API를 사용해 조회·요청 접수를 수행한 뒤 카카오 콜백으로 답합니다. `POST` 액션은 대회 시스템에서 **접수**만 기록하므로 고객에게 지급·변경 완료라고 말하지 않습니다.

## 설정

Cloud Run 서비스에 다음 환경 변수를 설정합니다. 값은 GitHub에 저장하지 않습니다.

| 변수 | 설명 |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI API 키 |
| `OPENAI_MODEL` | 선택, 기본 `gpt-4.1` |
| `KAKAO_BOT_TOKEN` | 카카오 봇 콜백 인증 토큰 |
| `KAKAO_WEBHOOK_SECRET` | 웹훅 `X-Bot-Secret` 헤더 검증 비밀값 |
| `AITOP100_ACTION_TOKEN` | 참가자 개인 액션 API 토큰 |

카카오 봇 웹훅은 `POST https://<Cloud Run 도메인>/webhook`, 헤더 `X-Bot-Secret: <KAKAO_WEBHOOK_SECRET>`으로 설정합니다. `/health`는 서비스와 액션 토큰 설정 여부만 반환합니다. Cloud Run은 204 반환 뒤 응답을 생성하므로 요청 외 CPU 할당과 최소 인스턴스 1개를 권장합니다.

대회 응답 규격에 맞게 한 번에 `SimpleText` 말풍선 하나, 490자 이내로 답합니다.

평가 TC ID는 메시지의 `L-11` 같은 텍스트 또는 웹훅 페이로드의 `test_case_id`/`testCaseId`에서 읽습니다. 같은 발신자의 후속 대화 동안 유지합니다. API 호출에는 `Authorization: Bearer ...`와 `X-Aitop100-Test-Case-Id`를 넣습니다. 공개 TC 외 ID는 대회 측이 평가 기간에 제공해야 합니다.

`actions.json`은 대회 OpenAPI 명세이고, `knowledge.md`는 제공받은 가상 시나리오 자료를 요약한 배포용 근거입니다. 대화 원본, 개인 토큰, 고객 연락처는 저장소에 포함하지 않습니다. `/api/action-data/reset`은 도구 허용 목록에서 제외했습니다.

## 로컬 실행

```powershell
python -m pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8080
```

보안상 개인 거래 처리에는 인입 계정과 주문 귀속을 확인해야 합니다. 현재 세션 맥락은 인스턴스 메모리에만 저장되므로 배포 재시작·다중 인스턴스에서는 이어지지 않습니다. 평가 기간에는 인스턴스 1개를 유지하거나 영속 세션 저장소를 연결해야 합니다.
