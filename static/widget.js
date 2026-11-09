// Capture the script element before DOMContentLoaded.
const widgetScript = document.currentScript;
const clinicId = widgetScript?.dataset?.clinicId || "clinic_001";

if (!widgetScript?.dataset?.clinicId) {
    console.warn("Chat widget: data-clinic-id is missing; using clinic_001.");
}

// Give each browser visitor a separate conversation ID.
let userId = localStorage.getItem("autoclinics_chat_user_id");

if (!userId) {
    userId = (window.crypto && crypto.randomUUID)
        ? crypto.randomUUID()
        : "visitor_" + Date.now() + "_" + Math.random().toString(36).slice(2);

    localStorage.setItem("autoclinics_chat_user_id", userId);
}

window.addEventListener("DOMContentLoaded", function () {

    console.log("WIDGET SCRIPT LOADED");
    console.log("Clinic ID:", clinicId);

    // Create floating button
    const button = document.createElement("div");

    button.innerHTML = `
        <svg width="28" height="28" viewBox="0 0 24 24" fill="white">
            <rect x="4" y="6" width="16" height="12" rx="4"/>
            <circle cx="9" cy="12" r="1.6" fill="#16a34a"/>
            <circle cx="15" cy="12" r="1.6" fill="#16a34a"/>
            <rect x="11" y="3" width="2" height="3" rx="1"/>
        </svg>
    `;

    button.style.background = "linear-gradient(135deg,#1d4ed8,#0891b2)";
    button.style.boxShadow = "0 10px 25px rgba(0,0,0,0.25)";
    button.style.fontSize = "26px";
    button.style.position = "fixed";
    button.style.bottom = "20px";
    button.style.right = "20px";
    button.style.width = "60px";
    button.style.height = "60px";
    button.style.borderRadius = "50%";
    button.style.color = "white";
    button.style.border = "none";
    button.style.display = "flex";
    button.style.alignItems = "center";
    button.style.justifyContent = "center";
    button.style.cursor = "pointer";
    button.style.zIndex = "9999";

    document.body.appendChild(button);

    // Create chat box
    const chatBox = document.createElement("div");

    chatBox.style.display = "none";
    chatBox.style.pointerEvents = "none";
    chatBox.style.zIndex = "999999";
    chatBox.style.position = "fixed";
    chatBox.style.bottom = "90px";
    chatBox.style.right = "20px";
    chatBox.style.width = "350px";
    chatBox.style.height = "460px";
    chatBox.style.background = "white";
    chatBox.style.flexDirection = "column";
    chatBox.style.overflow = "hidden";
    chatBox.style.boxShadow =
        "0 30px 80px rgba(0,0,0,0.25), 0 10px 30px rgba(0,0,0,0.12)";
    chatBox.style.borderRadius = "18px";

    document.body.appendChild(chatBox);

    // HEADER
    const header = document.createElement("div");

    header.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;">
            <div style="
                width:28px;
                height:28px;
                background:white;
                border-radius:51%;
                display:flex;
                align-items:center;
                justify-content:center;
            ">
                <img
                    src="https://cdn.shopify.com/s/files/1/0930/3893/6393/files/AutoClinicsLogo3.png?v=1773200243"
                    style="width:20px;height:20px;object-fit:contain;"
                >
            </div>

            <div style="display:flex;flex-direction:column;">
                <span id="botTitle" style="font-size:16px;font-weight:605;">
                    Digitaler Praxisassistent
                </span>

                <span id="botStatus" style="font-size:12px;font-weight:600;">
                    0-24 Erreichbar
                </span>
            </div>
        </div>
    `;

    console.log("SCRIPT START");

    header.style.display = "flex";
    header.style.justifyContent = "space-between";
    header.style.alignItems = "center";

    const langSelect = document.createElement("select");

    langSelect.innerHTML = `
        <option value="de">🇩🇪 DE</option>
        <option value="en">🇬🇧 EN</option>
        <option value="hun">🇭🇺 HUN</option>
    `;

    langSelect.style.border = "none";
    langSelect.style.borderRadius = "8px";
    langSelect.style.padding = "4px 8px";
    langSelect.style.fontSize = "12px";
    langSelect.style.cursor = "pointer";
    langSelect.style.outline = "none";

    header.style.padding = "14px";
    header.style.fontWeight = "bold";
    header.style.background = "linear-gradient(135deg,#2bb673,#16a085)";
    header.style.color = "white";
    header.style.borderBottom = "none";

    header.appendChild(langSelect);
    chatBox.appendChild(header);

    // MESSAGES
    const messages = document.createElement("div");

    messages.style.flex = "1";
    messages.style.padding = "10px";
    messages.style.overflowY = "auto";
    messages.style.display = "flex";
    messages.style.flexDirection = "column";
    messages.style.alignItems = "flex-start";

    chatBox.appendChild(messages);

    const trust = document.createElement("div");

    trust.style.padding = "8px 10px";
    trust.style.fontSize = "12px";
    trust.style.borderBottom = "1px solid #eee";

    trust.innerHTML = `
        <a
            href="https://www.google.com/search?sca_esv=9ce3d57fdcda1de3&sxsrf=ANbL-n6DqEvg87iOMZDz8WdC93wH-W_8OQ:1772814769449&si=AL3DRZEsmMGCryMMFSHJ3StBhOdZ2-6yYkXd_doETEE1OR-qOeTzmr5ms6dri2xHS6PT5qGUkyImPz6oNxudOTDwZplGuyPPvLRL3OLCOUYQxi1mwsxPg547vODwAiXmTSVpvbbR9Ate_QQfF0VbyBxThtd3jSot7iCSa42bJiW3U4D1hEWr7TaecTIAnoYvmFRC0TY8zwQdsRicRibUo10T25n_-YeYTA%3D%3D&q=Zahnarzt+Berlin+Sch%C3%B6neberg+-+Dental21+%28ehemals+Dentalzentrum+Plus%29+Reviews&sa=X&ved=2ahUKEwjyqdfU2YuTAxW-1wIHHe3KAOIQ0bkNegQINBAH&biw=1280&bih=593&dpr=1.5"
            target="_blank"
            style="
                display:flex;
                align-items:center;
                gap:8px;
                text-decoration:none;
                font-family:Arial, sans-serif;
            "
        >
            <span style="font-size:12px;color:#666;">Google</span>

            <span style="
                color:#f59e0b;
                font-size:14px;
                letter-spacing:1px;
            ">★★★★★</span>

            <span style="
                font-weight:600;
                color:#111;
                font-size:13px;
            ">4.9</span>

            <span style="color:#666;font-size:12px;">
                (3,600 reviews)
            </span>
        </a>
    `;

    trust.style.background = "#ecfdf5";
    trust.style.color = "#15803d";
    trust.style.fontWeight = "500";
    trust.style.fontSize = "12px";
    trust.style.padding = "8px 12px";
    trust.style.borderBottom = "1px solid #e5e7eb";

    chatBox.insertBefore(trust, messages);

    // INPUT AREA
    const inputArea = document.createElement("div");

    inputArea.style.display = "flex";
    inputArea.style.alignItems = "center";
    inputArea.style.padding = "12px";
    inputArea.style.gap = "10px";
    inputArea.style.borderTop = "1px solid #e5e7eb";
    inputArea.style.background = "white";

    const input = document.createElement("input");

    input.placeholder = "Type a message...";

    const translations = {
        de: {
            title: "Digitaler Praxisassistent",
            status: "0-24 Erreichbar",
            placeholder: "Nachricht schreiben..."
        },

        en: {
            title: "Digital Practice Assistant",
            status: "Available 24/7",
            placeholder: "Type a message..."
        },

        hun: {
            title: "Digitális Asszisztens",
            status: "Elérhető 24/7",
            placeholder: "Írj egy üzenetet..."
        }
    };

    let currentLanguage = localStorage.getItem("lang") || "de";

    if (!translations[currentLanguage]) {
        currentLanguage = "de";
    }

    let typingBubble = null;

    function applyLanguage(lang) {

        if (!translations[lang]) {
            lang = "de";
        }

        localStorage.setItem("lang", lang);

        document.getElementById("botTitle").innerText =
            translations[lang].title;

        document.getElementById("botStatus").innerText =
            translations[lang].status;

        input.placeholder =
            translations[lang].placeholder;

        currentLanguage = lang;
    }

    langSelect.value = currentLanguage;

    applyLanguage(currentLanguage);

    // API helper
    async function sendChatRequest(message) {

        const res = await fetch(
            "https://bot.automationclinics.com/chat",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    clinic_id: clinicId,
                    user_id: userId,
                    message: message,
                    language: currentLanguage
                })
            }
        );

        const data = await res.json();

        if (!res.ok) {
            throw new Error(
                data.error || `Server error: ${res.status}`
            );
        }

        return data;
    }

    // Add bot message
    function addBotMessage(reply) {

        const botMsg = document.createElement("div");

        botMsg.style.display = "flex";
        botMsg.style.alignItems = "flex-start";
        botMsg.style.gap = "8px";
        botMsg.style.margin = "8px 0";

        const avatar = document.createElement("img");

        avatar.src =
            "https://cdn.shopify.com/s/files/1/0930/3893/6393/files/AutoClinicsLogo3.png?v=1773200243";

        avatar.style.width = "28px";
        avatar.style.height = "28px";
        avatar.style.borderRadius = "50%";
        avatar.style.objectFit = "contain";
        avatar.style.flexShrink = "0";

        const bubble = document.createElement("div");

        bubble.style.background = "#f1f3f7";
        bubble.style.padding = "10px 14px";
        bubble.style.borderRadius = "16px";
        bubble.style.border = "1px solid #e5e7eb";
        bubble.style.color = "black";
        bubble.style.maxWidth = "100%";
        bubble.style.fontSize = "14px";
        bubble.style.lineHeight = "1.4";

        // Use textContent to safely display server response.
        bubble.textContent = reply || "No response.";

        botMsg.appendChild(avatar);
        botMsg.appendChild(bubble);

        messages.appendChild(botMsg);
        messages.scrollTop = messages.scrollHeight;
    }

    // Language selector
    langSelect.addEventListener("change", async (e) => {

        applyLanguage(e.target.value);

        messages.innerHTML = "";

        try {
            const data = await sendChatRequest("");

            addBotMessage(data.reply || "No response.");

        } catch (err) {
            console.error("Welcome message error:", err);
            addBotMessage("Unable to connect to the assistant.");
        }
    });

    // Input styling
    input.style.flex = "1";
    input.style.height = "50px";
    input.style.borderRadius = "25px";
    input.style.border = "2px solid #34d399";
    input.style.padding = "0 16px";
    input.style.fontSize = "14px";
    input.style.outline = "none";

    input.addEventListener("keydown", function(e) {

        if (e.key === "Enter") {
            sendMessage();
        }
    });

    // Send button
    const sendBtn = document.createElement("button");

    sendBtn.innerHTML = "➤";

    sendBtn.style.width = "50px";
    sendBtn.style.height = "50px";
    sendBtn.style.borderRadius = "50%";
    sendBtn.style.border = "none";
    sendBtn.style.background = "#34d399";
    sendBtn.style.color = "white";
    sendBtn.style.fontSize = "18px";
    sendBtn.style.cursor = "pointer";
    sendBtn.style.display = "flex";
    sendBtn.style.alignItems = "center";
    sendBtn.style.justifyContent = "center";

    sendBtn.addEventListener("click", sendMessage);

    inputArea.appendChild(input);
    inputArea.appendChild(sendBtn);

    chatBox.appendChild(inputArea);

    let welcomeLoaded = false;
    let isOpen = false;

    // Open / close chat
    button.addEventListener("click", async function () {

        isOpen = !isOpen;

        if (isOpen) {

            chatBox.style.display = "flex";
            chatBox.style.pointerEvents = "auto";

            // FIRST TIME WELCOME MESSAGE
            if (!welcomeLoaded) {

                welcomeLoaded = true;

                try {
                    const data = await sendChatRequest("");

                    addBotMessage(data.reply || "No response.");

                } catch (err) {
                    console.error("Welcome message error:", err);
                    addBotMessage("Unable to connect to the assistant.");
                }
            }

        } else {

            chatBox.style.display = "none";
            chatBox.style.pointerEvents = "none";
        }
    });

    // Typing indicator
    function showTyping() {

        typingBubble = document.createElement("div");

        typingBubble.innerHTML =
            "AI is typing<span>.</span><span>.</span><span>.</span>";

        typingBubble.style.fontSize = "13px";
        typingBubble.style.alignSelf = "flex-end";
        typingBubble.style.margin = "8px 0";
        typingBubble.style.padding = "8px 12px";
        typingBubble.style.borderRadius = "16px";
        typingBubble.style.background = "#e5e5ea";
        typingBubble.style.fontStyle = "italic";
        typingBubble.style.opacity = "0.7";

        messages.appendChild(typingBubble);
        messages.scrollTop = messages.scrollHeight;
    }

    function removeTyping() {

        if (typingBubble) {
            typingBubble.remove();
            typingBubble = null;
        }
    }

    // Suggestions
    function showSuggestions(items) {

        const wrapper = document.createElement("div");

        wrapper.style.marginTop = "8px";
        wrapper.style.display = "flex";
        wrapper.style.flexWrap = "wrap";
        wrapper.style.gap = "6px";

        items.forEach(text => {

            const btn = document.createElement("button");

            btn.innerText = text;

            btn.style.border = "2px solid #e5e7eb";
            btn.style.background = "#f9fafb";
            btn.style.color = "#374151";
            btn.style.fontSize = "12px";
            btn.style.padding = "6px 10px";
            btn.style.borderRadius = "14px";
            btn.style.cursor = "pointer";

            btn.onmouseenter = () => {
                btn.style.background = "#34d399";
                btn.style.borderColor = "#34d399";
                btn.style.color = "white";
            };

            btn.onmouseleave = () => {
                btn.style.background = "#f9fafb";
                btn.style.borderColor = "#e5e7eb";
                btn.style.color = "#374151";
            };

            btn.onclick = () => {
                input.value = text;
                sendMessage();
            };

            wrapper.appendChild(btn);
        });

        messages.appendChild(wrapper);
        messages.scrollTop = messages.scrollHeight;
    }

    // Send message
    async function sendMessage() {

        const text = input.value.trim();

        if (!text) return;

        const userMsg = document.createElement("div");

        userMsg.innerText = text;

        userMsg.style.display = "inline-block";
        userMsg.style.alignSelf = "flex-end";
        userMsg.style.padding = "10px 14px";
        userMsg.style.borderRadius = "18px";
        userMsg.style.margin = "6px 0";
        userMsg.style.color = "white";
        userMsg.style.background =
            "linear-gradient(135deg,#1d4ed8,#3b82f6)";
        userMsg.style.maxWidth = "70%";
        userMsg.style.width = "fit-content";
        userMsg.style.wordBreak = "break-word";

        messages.appendChild(userMsg);

        input.value = "";

        messages.scrollTop = messages.scrollHeight;

        showTyping();

        sendBtn.disabled = true;

        try {

            const data = await sendChatRequest(text);

            removeTyping();

            const reply = data.reply || "No response.";

            addBotMessage(reply);

            if (
                data.suggestions &&
                Array.isArray(data.suggestions) &&
                data.suggestions.length > 0
            ) {
                showSuggestions(data.suggestions);
            }

            messages.scrollTop = messages.scrollHeight;

        } catch (err) {

            removeTyping();

            console.error("Chat request error:", err);

            addBotMessage(
                "Sorry, something went wrong. Please try again."
            );

        } finally {

            sendBtn.disabled = false;
        }
    }

});