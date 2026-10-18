# Luật Việt — Trợ lý tra cứu pháp luật

Ứng dụng tham khảo pháp luật Việt Nam sử dụng FastAPI, Gemini Interactions API, SQLite và giao diện HTML/CSS/JavaScript.

## Yêu cầu

- Python 3.10+
- Gemini API key

## Cài đặt và chạy

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Mở `.env`, điền `GEMINI_API_KEY` lấy từ [Google AI Studio](https://aistudio.google.com/apikey), sau đó chạy:

```powershell
uvicorn app.main:app --reload
```

Mở [http://127.0.0.1:8000](http://127.0.0.1:8000). Tài liệu API tương tác có tại [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## API

| Phương thức | Đường dẫn          | Chức năng                           |
| -------------- | ---------------------- | ------------------------------------- |
| `GET`        | `/api/health`        | Kiểm tra trạng thái                |
| `POST`       | `/api/consultations` | Tra cứu (`{"question":"..."}`)     |
| `GET`        | `/api/consultations` | Lấy tối đa 20 câu hỏi gần nhất |
| `DELETE`     | `/api/consultations` | Xóa toàn bộ lịch sử              |

SQLite tự tạo tại `data/legal_assistant.db`. Có thể đặt biến môi trường `DATABASE_PATH` để chọn nơi lưu khác. Lịch sử được lưu trên máy chủ; không gửi thông tin cá nhân hoặc dữ liệu nhạy cảm vào câu hỏi.

## Lưu ý

- Câu trả lời do AI tạo, chỉ phục vụ tham khảo và có thể thiếu cập nhật hoặc sai căn cứ. Luôn kiểm tra văn bản gốc tại [Cơ sở dữ liệu quốc gia về văn bản pháp luật](https://vbpl.vn/) hoặc [Cổng văn bản Chính phủ](https://vanban.chinhphu.vn/).
- API key chỉ cấu hình ở phía máy chủ, không đưa vào JavaScript hoặc kho mã nguồn.
- Không bắt buộc huấn luyện mô hình hay GPU. Ứng dụng cần kết nối Internet và Gemini API key để tra cứu.
- Ứng dụng gọi Gemini Interactions API với model mặc định `gemini-3.8-flash`; mỗi yêu cầu đặt `store=false` để không lưu interaction phía Gemini.

## Khắc phục lỗi Gemini

- Sau khi sửa `.env`, khởi động lại `uvicorn` để nạp lại API key.
- Nếu ứng dụng báo API key không được phép gọi Gemini, kiểm tra key trong [Google AI Studio](https://aistudio.google.com/apikey), quyền gọi Generative Language API và giới hạn của key. Theo [hướng dẫn API key của Google](https://ai.google.dev/gemini-api/docs/api-key), các standard key không giới hạn đã bị từ chối từ ngày 28/05/2026; hãy tạo authorization key hoặc giới hạn standard key cho Gemini API.
- Nếu ứng dụng báo hết quota, kiểm tra hạn mức và billing của project Google Cloud gắn với key.
- `304 Not Modified` cho CSS/JavaScript là phản hồi cache của trình duyệt, không phải lỗi tra cứu. Ứng dụng hiện gửi `Cache-Control: no-store`; khởi động lại máy chủ và tải lại trang để nhận mã mới.
