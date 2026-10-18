import httpx

from app.config import GEMINI_API_KEY, GEMINI_API_URL, GEMINI_MODEL

SYSTEM_PROMPT = """
Bạn là trợ lý tra cứu và giải thích pháp luật Việt Nam, trả lời bằng tiếng Việt.
Chỉ cung cấp thông tin tham khảo, không thay thế tư vấn của luật sư.

Nguyên tắc bắt buộc:
- Trả lời đúng trọng tâm, trình bày dễ hiểu và phân biệt rõ quy định với nhận định.
- Nêu tên văn bản, số hiệu, điều/khoản/điểm và ngày hiệu lực khi bạn biết chắc.
- Không tự tạo số hiệu văn bản, điều luật, mức phạt, đường dẫn hoặc trích dẫn.
- Không chép lại nguyên văn đoạn dài từ văn bản hoặc nguồn có bản quyền. Ưu tiên
  tóm tắt, giải thích bằng lời của bạn và nêu điều/khoản để người dùng tự xem
  toàn văn tại nguồn chính thức. Chỉ trích dẫn ngắn khi thực sự cần thiết.
- Nếu không xác định chắc căn cứ hoặc tình trạng hiệu lực, hãy nói rõ điều đó
  và đề nghị người dùng kiểm tra văn bản hiện hành trên Cơ sở dữ liệu quốc gia
  về văn bản pháp luật (vbpl.vn) hoặc Cổng văn bản Chính phủ
  (vanban.chinhphu.vn).
- Lưu ý ngày ban hành và sửa đổi có thể khiến quy định thay đổi; hỏi thêm thông
  tin còn thiếu nếu câu hỏi phụ thuộc vào thời điểm, địa phương hoặc tình tiết.
- Không kết luận chắc chắn về kết quả một vụ việc cụ thể khi chưa đủ dữ kiện.

Trình bày câu trả lời theo các mục phù hợp:
1. Trả lời ngắn gọn
2. Căn cứ pháp lý (chỉ ghi nội dung đã xác minh được; nếu chưa chắc thì nói rõ)
3. Lưu ý / bước tiếp theo
""".strip()


class AIServiceError(Exception):
    """An expected, user-safe error from the AI provider."""

    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


def _provider_error(response: httpx.Response) -> tuple[str, str]:
    try:
        payload = response.json()
    except ValueError:
        return "", ""

    if not isinstance(payload, dict):
        return "", ""
    error = payload.get("error", {})
    if not isinstance(error, dict):
        return "", ""
    status = error.get("status", "")
    message = error.get("message", "")
    return (
        status if isinstance(status, str) else "",
        message.strip()[:400] if isinstance(message, str) else "",
    )


async def answer_legal_question(question: str) -> str:
    if not GEMINI_API_KEY:
        raise AIServiceError(
            "Chưa cấu hình GEMINI_API_KEY. Hãy thêm API key hợp lệ vào tệp .env "
            "rồi khởi động lại máy chủ.",
            status_code=503,
        )
    if not GEMINI_MODEL:
        raise AIServiceError(
            "GEMINI_MODEL đang để trống. Hãy đặt model Gemini hợp lệ trong tệp .env.",
            status_code=503,
        )

    url = GEMINI_API_URL
    payload = {
        "model": GEMINI_MODEL,
        "system_instruction": SYSTEM_PROMPT,
        "input": question,
        "generation_config": {"thinking_level": "low"},
        "store": False,
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                headers={"x-goog-api-key": GEMINI_API_KEY},
                json=payload,
            )
        response.raise_for_status()
        data = response.json()
    except httpx.TimeoutException as exc:
        raise AIServiceError(
            "Gemini phản hồi quá thời gian chờ. Vui lòng thử lại.",
            status_code=504,
        ) from exc
    except httpx.HTTPStatusError as exc:
        provider_status, provider_message = _provider_error(exc.response)
        details = f" Chi tiết từ Gemini: {provider_message}" if provider_message else ""
        if exc.response.status_code == 401 or provider_status == "API_KEY_INVALID":
            raise AIServiceError(
                "Gemini từ chối API key. Hãy kiểm tra GEMINI_API_KEY, quyền truy cập "
                "Generative Language API và giới hạn của API key."
                f"{details}",
                status_code=502,
            ) from exc
        if exc.response.status_code == 429 or provider_status == "RESOURCE_EXHAUSTED":
            raise AIServiceError(
                "Gemini đã hết hạn mức hoặc đang giới hạn số yêu cầu. "
                "Hãy kiểm tra quota/billing trong Google AI Studio rồi thử lại."
                f"{details}",
                status_code=429,
            ) from exc
        if exc.response.status_code == 404:
            raise AIServiceError(
                f"Không tìm thấy model Gemini '{GEMINI_MODEL}'. "
                "Hãy kiểm tra lại GEMINI_MODEL trong tệp .env."
                f"{details}",
                status_code=502,
            ) from exc
        if exc.response.status_code == 400:
            if any(
                term in provider_message.casefold()
                for term in ("copyright", "recitation")
            ):
                raise AIServiceError(
                    "Gemini đã chặn yêu cầu vì có thể cần trích nguyên văn nội dung "
                    "được bảo hộ. Hãy hỏi theo hướng tóm tắt hoặc giải thích quy định, "
                    "nêu số hiệu điều luật và không yêu cầu chép toàn văn.",
                    status_code=422,
                ) from exc
            raise AIServiceError(
                "Gemini không chấp nhận yêu cầu. Hãy kiểm tra model và nội dung "
                f"cấu hình.{details}",
                status_code=502,
            ) from exc
        if exc.response.status_code == 403:
            raise AIServiceError(
                "API key không được phép gọi Gemini. Kiểm tra quyền API, project "
                f"và giới hạn key.{details}",
                status_code=502,
            ) from exc
        raise AIServiceError(
            "Dịch vụ Gemini đang gặp sự cố. Vui lòng thử lại sau."
            f"{details}",
            status_code=503,
        ) from exc
    except httpx.HTTPError as exc:
        raise AIServiceError(
            "Không thể kết nối tới Gemini. Kiểm tra kết nối Internet/proxy "
            "của máy chủ rồi thử lại.",
            status_code=502,
        ) from exc
    except ValueError as exc:
        raise AIServiceError(
            "Gemini trả về dữ liệu không hợp lệ.",
            status_code=502,
        ) from exc

    steps = data.get("steps", []) if isinstance(data, dict) else []
    answer = "\n".join(
        content["text"]
        for step in steps
        if isinstance(step, dict) and step.get("type") == "model_output"
        for content in step.get("content", [])
        if isinstance(content, dict)
        and content.get("type") == "text"
        and isinstance(content.get("text"), str)
    ).strip()
    if not answer:
        raise AIServiceError(
            "Gemini chưa tạo được câu trả lời cho yêu cầu này. Vui lòng diễn đạt lại.",
            status_code=502,
        )
    return answer
