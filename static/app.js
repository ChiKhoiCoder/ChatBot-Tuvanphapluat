const form = document.querySelector("#question-form");
const input = document.querySelector("#question-input");
const submitButton = document.querySelector("#submit-button");
const submitLabel = document.querySelector(".submit-label");
const answerSection = document.querySelector("#answer-section");
const answerText = document.querySelector("#answer-text");
const questionEcho = document.querySelector("#question-echo");
const answerTime = document.querySelector("#answer-time");
const loadingCard = document.querySelector("#loading-card");
const errorMessage = document.querySelector("#error-message");
const errorCopy = document.querySelector(".error-copy");
const historyList = document.querySelector("#history-list");
const clearHistoryButton = document.querySelector("#clear-history");
const characterCount = document.querySelector("#character-count");
const sidebar = document.querySelector("#sidebar");
const mobileMenu = document.querySelector("#mobile-menu");
const sidebarBackdrop = document.querySelector("#sidebar-backdrop");
const copyButton = document.querySelector("#copy-answer");

function showError(message) {
  errorCopy.textContent = message;
  errorMessage.hidden = false;
}

function hideError() {
  errorMessage.hidden = true;
  errorCopy.textContent = "";
}

function formatDate(value) {
  if (!value) return "Vừa xong";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Vừa xong";
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function closeMobileSidebar() {
  sidebar.classList.remove("open");
  sidebarBackdrop.classList.remove("visible");
  mobileMenu.setAttribute("aria-expanded", "false");
  document.body.classList.remove("sidebar-open");
}

function appendInlineText(container, text) {
  const inlinePattern = /(\*\*[^*]+\*\*|__[^_]+__|`[^`]+`)/g;
  let cursor = 0;

  for (const match of text.matchAll(inlinePattern)) {
    container.append(document.createTextNode(text.slice(cursor, match.index)));
    const marker = match[0];
    const element = document.createElement(
      marker.startsWith("`") ? "code" : "strong",
    );
    element.textContent = marker.startsWith("`")
      ? marker.slice(1, -1)
      : marker.slice(2, -2);
    container.append(element);
    cursor = match.index + marker.length;
  }

  container.append(document.createTextNode(text.slice(cursor)));
}

function getAnswerHeading(line) {
  const markdownHeading = line.match(/^#{1,3}\s+(.+)$/);
  const content = (markdownHeading ? markdownHeading[1] : line)
    .replace(/\*\*/g, "")
    .replace(/__/g, "")
    .trim();
  const numberedHeading = content.match(/^(\d+)[.)]\s+(.+)$/);
  const title = numberedHeading ? numberedHeading[2].trim() : content;
  const isKnownSection =
    /^(?:trả lời(?:\s+ngắn gọn)?|căn cứ(?:\s+pháp lý)?|cơ sở pháp lý|lưu ý|bước tiếp theo|kết luận|phân tích|điều kiện|thủ tục|quyền và nghĩa vụ)(?:\s|:|$)/i.test(
      title,
    );
  const isLabel = /:\s*$/.test(title) && title.length <= 90;

  if (!markdownHeading && !isKnownSection && !isLabel) return null;
  const category = /căn cứ|cơ sở pháp lý/i.test(title)
    ? "legal"
    : /lưu ý|bước tiếp theo/i.test(title)
      ? "note"
      : "general";
  return {
    number: numberedHeading?.[1] || "",
    title: title.replace(/:\s*$/, ""),
    category,
  };
}

function renderAnswer(rawAnswer) {
  answerText.replaceChildren();
  answerText.dataset.rawAnswer = rawAnswer;

  let activeContainer = answerText;
  let paragraphLines = [];
  let activeList = null;

  function flushParagraph() {
    if (paragraphLines.length === 0) return;
    const paragraph = document.createElement("p");
    paragraph.className = "answer-paragraph";
    appendInlineText(paragraph, paragraphLines.join(" "));
    activeContainer.append(paragraph);
    paragraphLines = [];
  }

  function flushList() {
    activeList = null;
  }

  for (const rawLine of rawAnswer.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || /^[-*_]{3,}$/.test(line)) {
      flushParagraph();
      flushList();
      continue;
    }

    const heading = getAnswerHeading(line);
    if (heading) {
      flushParagraph();
      flushList();

      const section = document.createElement("section");
      section.className = `answer-part answer-part--${heading.category}`;
      const title = document.createElement("h3");
      title.className = "answer-part-title";
      if (heading.number) {
        const number = document.createElement("span");
        number.className = "answer-part-number";
        number.textContent = heading.number.padStart(2, "0");
        title.append(number);
      } else {
        const marker = document.createElement("span");
        marker.className = "answer-part-marker";
        marker.setAttribute("aria-hidden", "true");
        marker.textContent = "✳";
        title.append(marker);
      }

      const label = document.createElement("span");
      label.textContent = heading.title;
      title.append(label);
      section.append(title);

      const body = document.createElement("div");
      body.className = "answer-part-body";
      section.append(body);
      answerText.append(section);
      activeContainer = body;
      continue;
    }

    const listItem = line.match(/^(?:[-*•]\s+|(\d+)[.)]\s+)(.+)$/);
    if (listItem) {
      flushParagraph();
      const listType = listItem[1] ? "ol" : "ul";
      if (!activeList || activeList.tagName.toLowerCase() !== listType) {
        activeList = document.createElement(listType);
        activeList.className = "answer-list";
        activeContainer.append(activeList);
      }
      const item = document.createElement("li");
      appendInlineText(item, listItem[2]);
      activeList.append(item);
      continue;
    }

    flushList();
    paragraphLines.push(line.replace(/^>\s?/, ""));
  }

  flushParagraph();
  flushList();
}

function displayAnswer(item) {
  questionEcho.textContent = item.question;
  renderAnswer(item.answer);
  answerTime.textContent = formatDate(item.created_at);
  answerSection.hidden = false;
  loadingCard.hidden = true;
  hideError();
  closeMobileSidebar();
  answerSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderHistory(items) {
  historyList.replaceChildren();
  clearHistoryButton.hidden = items.length === 0;

  if (items.length === 0) {
    const empty = document.createElement("p");
    empty.className = "history-empty";
    empty.textContent = "Các câu hỏi gần đây của bạn sẽ hiển thị tại đây.";
    historyList.append(empty);
    return;
  }

  for (const item of items) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "history-item";
    button.setAttribute("aria-label", `Mở câu hỏi: ${item.question}`);
    if (item.question === questionEcho.textContent) {
      button.classList.add("active");
      button.setAttribute("aria-current", "true");
    }

    const label = document.createElement("span");
    label.textContent = item.question;
    button.append(label);
    button.title = item.question;
    button.addEventListener("click", () => displayAnswer(item));
    historyList.append(button);
  }
}

async function loadHistory() {
  const response = await fetch("/api/consultations");
  if (!response.ok) throw new Error("Không tải được lịch sử tra cứu.");
  renderHistory(await response.json());
}

input.addEventListener("input", () => {
  characterCount.textContent = `${input.value.length}/2000`;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (question.length < 5) {
    showError("Vui lòng nhập câu hỏi có ít nhất 5 ký tự.");
    input.focus();
    return;
  }

  submitButton.disabled = true;
  form.setAttribute("aria-busy", "true");
  submitLabel.textContent = "Đang tra cứu";
  hideError();
  answerSection.hidden = true;
  loadingCard.hidden = false;

  try {
    const response = await fetch("/api/consultations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Không thể tra cứu lúc này.");
    displayAnswer(data);
    await loadHistory();
  } catch (error) {
    loadingCard.hidden = true;
    showError(error.message || "Không thể kết nối tới máy chủ.");
  } finally {
    submitButton.disabled = false;
    form.removeAttribute("aria-busy");
    submitLabel.textContent = "Tra cứu";
  }
});

document.querySelector("#new-search").addEventListener("click", () => {
  input.value = "";
  characterCount.textContent = "0/2000";
  answerSection.hidden = true;
  loadingCard.hidden = true;
  hideError();
  closeMobileSidebar();
  input.focus();
  window.scrollTo({ top: 0, behavior: "smooth" });
});

document.querySelectorAll(".suggestion-chip").forEach((button) => {
  button.addEventListener("click", () => {
    const topic = button.querySelector("strong").textContent;
    const examples = {
      "Lao động": "Tôi muốn tìm hiểu quy định pháp luật về lao động: ",
      "Đất đai & nhà ở": "Tôi muốn tìm hiểu quy định pháp luật về đất đai và nhà ở: ",
      "Hôn nhân & gia đình": "Tôi muốn tìm hiểu quy định pháp luật về hôn nhân và gia đình: ",
    };
    input.value = examples[topic] || `Tôi muốn tìm hiểu về ${topic}: `;
    characterCount.textContent = `${input.value.length}/2000`;
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
  });
});

clearHistoryButton.addEventListener("click", async () => {
  clearHistoryButton.disabled = true;
  try {
    const response = await fetch("/api/consultations", { method: "DELETE" });
    if (!response.ok) throw new Error("Không thể xóa lịch sử tra cứu.");
    renderHistory([]);
  } catch (error) {
    showError(error.message || "Không thể xóa lịch sử tra cứu.");
  } finally {
    clearHistoryButton.disabled = false;
  }
});

mobileMenu.addEventListener("click", () => {
  const isOpen = sidebar.classList.toggle("open");
  sidebarBackdrop.classList.toggle("visible", isOpen);
  mobileMenu.setAttribute("aria-expanded", String(isOpen));
  document.body.classList.toggle("sidebar-open", isOpen);
});

sidebarBackdrop.addEventListener("click", closeMobileSidebar);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeMobileSidebar();
});

copyButton.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(
      answerText.dataset.rawAnswer || answerText.textContent,
    );
    const label = copyButton.querySelector("span:last-child");
    label.textContent = "Đã sao chép";
    window.setTimeout(() => {
      label.textContent = "Sao chép";
    }, 1800);
  } catch {
    showError("Trình duyệt không cho phép sao chép. Hãy chọn và sao chép nội dung thủ công.");
  }
});

loadHistory().catch((error) => {
  showError(error.message || "Không thể tải lịch sử tra cứu.");
});
