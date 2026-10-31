# AI TOP 100 Kakao bot

Google Cloud Run에서 카카오톡 봇 웹훅을 수신하고 OpenAI 답변을 카카오 콜백 API로 보냅니다.

## 환경 변수

- `OPENAI_API_KEY`: OpenAI API 키
- `OPENAI_MODEL`: 선택 사항. 기본값 `gpt-4.1-mini`
- `KAKAO_BOT_TOKEN`: 카카오 봇 인증 토큰
- `KAKAO_WEBHOOK_SECRET`: 직접 생성한 긴 임의의 비밀값

카카오 앱 관리의 **카카오톡 봇 > 봇 > 웹훅**에 다음을 등록합니다.

- 방식: POST
- URL: `https://<Cloud Run 도메인>/webhook`
- 헤더 Key: `X-Kakao-Webhook-Secret`
- 헤더 Value: `KAKAO_WEBHOOK_SECRET`과 같은 값

`/health`는 서버 상태 확인용입니다. 웹훅은 헤더가 일치하지 않으면 401을 반환합니다. `MESSAGE_CREATE` 이벤트만 답변하며 다른 이벤트는 204로 접수합니다.

Cloud Run은 204 응답 후 백그라운드에서 AI 생성과 카카오 콜백을 처리하므로 **CPU를 요청 외 시간에도 할당(인스턴스 기반 결제)**하도록 설정해야 합니다. 서비스에서 `OPENAI_API_KEY`, `KAKAO_BOT_TOKEN`, `KAKAO_WEBHOOK_SECRET`을 설정하지 않으면 실제 답변이 동작하지 않습니다.

카카오 규격: [웹훅](https://developers.kakao.com/docs/ko/bot/webhook), [메시지 콜백](https://developers.kakao.com/docs/ko/bot/rest-api#callback-msg)
