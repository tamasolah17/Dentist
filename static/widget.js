window.addEventListener("DOMContentLoaded", function () {

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
    button.style.fontSize = "26px";

    button.style.border = "none";

    button.style.display = "flex";
    button.style.alignItems = "center";
    button.style.justifyContent = "center";
    button.style.borderRadius = "50%";
    button.style.cursor = "pointer";


    button.style.zIndex = "9999";
    document.body.appendChild(button);

    // Create chat box
    const chatBox = document.createElement("div");
    chatBox.style.position = "fixed";
    chatBox.style.bottom = "90px";
    chatBox.style.right = "20px";
    chatBox.style.width = "350px";
    chatBox.style.height = "460px";
    chatBox.style.background = "white";

    chatBox.style.display = "none";
    chatBox.style.flexDirection = "column";
    chatBox.style.overflow = "hidden";
    chatBox.style.zIndex = "9999";
    chatBox.style.display = "none";
    chatBox.style.display = "flex";
    chatBox.style.visibility = "hidden";
    chatBox.style.boxShadow =
     "0 30px 80px rgba(0,0,0,0.25), 0 10px 30px rgba(0,0,0,0.12)";
    chatBox.style.borderRadius = "18px";

    document.body.appendChild(chatBox);

    // HEADER
    const header = document.createElement("div");
    header.innerHTML = `
        <div style="display:flex;flex-direction:column;">
        <span style="font-size:15px;font-weight:600;">🦷 Dental Booking Assistant</span>
        <span style="font-size:11px;opacity:0.8;">Online now</span>
        </div>
        `;
    header.style.display = "flex";

    header.style.padding = "12px";
    header.style.fontWeight = "bold";
    header.style.background = "linear-gradient(135deg,#2bb673,#16a085)";
    header.style.color = "white";
    header.style.padding = "14px";
    header.style.borderBottom = "none";
    chatBox.appendChild(header);

    // MESSAGES
    const messages = document.createElement("div");
    messages.style.flex = "1";
    messages.style.padding = "10px";
    messages.style.overflowY = "auto";
    messages.style.flex = "1";
    messages.style.display = "flex";
    messages.style.flexDirection = "column";


    chatBox.appendChild(messages);
    const trust = document.createElement("div");
    trust.style.padding = "8px 10px";
    trust.style.fontSize = "12px";
    trust.style.borderBottom = "1px solid #eee";



    trust.innerHTML = `
    <a href="https://www.google.com/search?sca_esv=9ce3d57fdcda1de3&sxsrf=ANbL-n6DqEvg87iOMZDz8WdC93wH-W_8OQ:1772814769449&si=AL3DRZEsmMGCryMMFSHJ3StBhOdZ2-6yYkXd_doETEE1OR-qOeTzmr5ms6dri2xHS6PT5qGUkyImPz6oNxudOTDwZplGuyPPvLRL3OLCOUYQxi1mwsxPg547vODwAiXmTSVpvbbR9Ate_QQfF0VbyBxThtd3jSot7iCSa42bJiW3U4D1hEWr7TaecTIAnoYvmFRC0TY8zwQdsRicRibUo10T25n_-YeYTA%3D%3D&q=Zahnarzt+Berlin+Sch%C3%B6neberg+-+Dental21+%28ehemals+Dentalzentrum+Plus%29+Reviews&sa=X&ved=2ahUKEwjyqdfU2YuTAxW-1wIHHe3KAOIQ0bkNegQINBAH&biw=1280&bih=593&dpr=1.5"
    target="_blank"
    style="
    display:flex;
    align-items:center;
    gap:8px;
    text-decoration:none;
    font-family:Arial, sans-serif;
    ">

    <span style="
    font-size:12px;
    color:#666;
    ">
    Google
    </span>

    <span style="
    color:#f59e0b;
    font-size:14px;
    letter-spacing:1px;
    ">
    ★★★★★
    </span>

    <span style="
    font-weight:600;
    color:#111;
    font-size:13px;
    ">
    4.9
    </span>

    <span style="
    color:#666;
    font-size:12px;
    ">
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
    inputArea.style.borderTop = "1px solid #ddd";

    const input = document.createElement("input");
    input.placeholder = "Type a message...";
    input.style.flex = "1";
    input.style.padding = "10px";
    input.style.border = "none";
    input.style.outline = "none";
    input.style.borderRadius = "20px";
    input.style.border = "1px solid #e5e7eb";
    input.style.padding = "10px 14px";
    input.style.fontSize = "14px";
    input.style.outline = "none";
    input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            sendMessage();
        }
    });


    const sendBtn = document.createElement("button");
    sendBtn.addEventListener("click", sendMessage);
    sendBtn.innerText = "Send";
    sendBtn.style.background = "#007bff";
    sendBtn.style.color = "white";
    sendBtn.style.border = "none";
    sendBtn.style.padding = "10px 15px";
    sendBtn.style.cursor = "pointer";
    sendBtn.style.background = "#22c55e";

    inputArea.appendChild(input);
    inputArea.appendChild(sendBtn);
    chatBox.appendChild(inputArea);



    let welcomeLoaded = false;

    button.addEventListener("click", async function () {

        const opening = chatBox.style.visibility === "hidden";

        if (opening) {
            chatBox.style.visibility = "visible";

            if (!welcomeLoaded) {
                welcomeLoaded = true;

                const res =  await fetch("https://bot.automationclinics.com/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        user_id: "demo_user",
                        message: ""
                    })
                });

                const data = await res.json();

                const botMsg = document.createElement("div");
                botMsg.innerText = data.reply || "No response.";
                botMsg.style.margin = "8px 0";
                botMsg.style.padding = "8px 12px";
                botMsg.style.borderRadius = "16px";
                botMsg.style.background = "#f1f3f7";
                botMsg.style.border = "1px solid #e5e7eb";
                botMsg.style.color = "black";
                messages.appendChild(botMsg);
                messages.scrollTop = messages.scrollHeight;

            }

        } else {
            chatBox.style.visibility = "hidden";
        }
    });

    function showTyping() {
        typingBubble = document.createElement("div");
        typingBubble.innerHTML = "AI is typing<span>.</span><span>.</span><span>.</span>";
        typingBubble.style.fontSize = "13px";

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

    function showSuggestions(items) {
        const wrapper = document.createElement("div");
        wrapper.style.marginTop = "8px";
        wrapper.style.display = "flex";
        wrapper.style.flexWrap = "wrap";
        wrapper.style.gap = "6px";

        items.forEach(text => {
            const btn = document.createElement("button");
            btn.innerText = text;

            btn.style.borderRadius = "14px";
            btn.style.border = "1px solid #ddd";



            btn.style.border = "1px solid #e5e7eb";
            btn.style.background = "#f9fafb";
            btn.style.color = "#374151";
            btn.style.fontSize = "12px";
            btn.style.padding = "6px 10px";
            btn.style.borderRadius = "14px";


            btn.style.cursor = "pointer";

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

    const userMsg = document.createElement("div");userMsg.innerText = text;

    userMsg.style.display = "inline-block";
    userMsg.style.alignSelf = "flex-end";

    userMsg.style.padding = "10px 14px";
    userMsg.style.borderRadius = "18px";

    userMsg.style.margin = "6px 0";

    userMsg.style.color = "white";

    userMsg.style.background = "linear-gradient(135deg,#1d4ed8,#3b82f6)";

    userMsg.style.maxWidth = "70%";
    userMsg.style.width = "fit-content";

    userMsg.style.wordBreak = "break-word";


    messages.appendChild(userMsg);

    input.value = "";
    messages.scrollTop = messages.scrollHeight;

    showTyping();

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: "demo_user",
                message: text
            })
        });

        const data = await res.json();

        removeTyping();

        const botMsg = document.createElement("div");
        botMsg.innerText = data.reply || "No response.";
        botMsg.style.margin = "8px 0";
        botMsg.style.padding = "8px 12px";
        botMsg.style.borderRadius = "16px";
        botMsg.style.background = "#f1f3f7";
        botMsg.style.border = "1px solid #e5e7eb";
        botMsg.style.color = "black";

        messages.appendChild(botMsg);

        if (data.suggestions && data.suggestions.length > 0) {
            showSuggestions(data.suggestions);
        }

        messages.scrollTop = messages.scrollHeight;

    } catch (err) {
        removeTyping();
        console.error(err);
    }
}
});

