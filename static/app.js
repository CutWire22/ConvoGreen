const chatContainer = document.getElementById("chat-container");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const debateBtn = document.getElementById("btn-debate");

let debateRunning = false;
let uploadedFiles = { a: [], b: [] };

// Temperature slider display
document.getElementById("a-temp").addEventListener("input", (e) => {
    document.getElementById("a-temp-val").textContent = e.target.value;
});
document.getElementById("b-temp").addEventListener("input", (e) => {
    document.getElementById("b-temp-val").textContent = e.target.value;
});

// Enter to send
userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Drag and drop setup
["a", "b"].forEach((side) => {
    const dropZone = document.getElementById(`${side}-drop`);
    const fileInput = document.getElementById(`${side}-file`);

    dropZone.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("dragover"); });
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        handleFiles(side, e.dataTransfer.files);
    });
    fileInput.addEventListener("change", () => handleFiles(side, fileInput.files));
});

async function handleFiles(side, files) {
    const container = document.getElementById(`${side}-files`);
    for (const file of files) {
        const formData = new FormData();
        formData.append("file", file);
        try {
            const resp = await fetch(`/api/upload/${side}`, { method: "POST", body: formData });
            const data = await resp.json();
            const div = document.createElement("div");
            div.textContent = `✓ ${data.filename}`;
            container.appendChild(div);
            uploadedFiles[side].push(file.name);
        } catch (err) {
            console.error("Upload failed:", err);
        }
    }
}

function getProfile(side) {
    return {
        persona_name: document.getElementById(`${side}-name`).value,
        system_prompt: document.getElementById(`${side}-system`).value,
        temperature: parseFloat(document.getElementById(`${side}-temp`).value),
        api_endpoint: document.getElementById(`${side}-endpoint`).value,
        auth_key: document.getElementById(`${side}-key`).value,
        model_name: document.getElementById(`${side}-model`).value,
    };
}

async function saveProfile(side) {
    const config = getProfile(side);
    await fetch(`/api/profile/${side}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
    });
    updateButtonLabels();
}

function updateButtonLabels() {
    const aName = document.getElementById("a-name").value;
    const bName = document.getElementById("b-name").value;
    document.getElementById("btn-model-a").textContent = `Let ${aName} Answer`;
    document.getElementById("btn-model-b").textContent = `Let ${bName} Answer`;
}

function renderMessage(entry) {
    const div = document.createElement("div");
    div.className = entry.role === "user" ? "msg-user pl-3" : "msg-assistant pl-3";

    const label = document.createElement("div");
    label.className = "text-[#63857e] text-xs mb-1";
    label.textContent = `${entry.name} Responded at ${entry.timestamp}:`;

    const text = document.createElement("div");
    text.className = "text-[#ecf2f0] text-xs whitespace-pre-wrap leading-relaxed";
    text.textContent = entry.text;

    div.appendChild(label);
    div.appendChild(text);
    chatContainer.appendChild(div);
    requestAnimationFrame(() => { chatContainer.scrollTop = chatContainer.scrollHeight; });
}

function setLoading(loading) {
    sendBtn.disabled = loading;
    sendBtn.textContent = loading ? "..." : "Send";
    sendBtn.classList.toggle("opacity-50", loading);
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;
    userInput.value = "";
    setLoading(true);

    try {
        const resp = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: text,
                profile_a: getProfile("a"),
                profile_b: getProfile("b"),
            }),
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || "Server error");
        renderMessage(data.user_entry);
        for (const r of data.responses) renderMessage(r);
    } catch (err) {
        renderMessage({ role: "user", name: "User", text: text, timestamp: "—" });
        renderMessage({ role: "assistant", name: "Error", text: err.message, timestamp: "—" });
    }
    setLoading(false);
}

async function singleModel(target) {
    const text = userInput.value.trim();
    setLoading(true);

    if (text) {
        const ts = new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }).replace(/,/g, "") + " " + new Date().toLocaleDateString("en-US", { month: "numeric", day: "numeric", year: "numeric" });
        renderMessage({ role: "user", name: "User", text: text, timestamp: ts });
        userInput.value = "";
    }

    try {
        const resp = await fetch("/api/chat/single", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                target,
                message: text,
                profile_a: getProfile("a"),
                profile_b: getProfile("b"),
            }),
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || "Server error");
        if (data.user_entry) renderMessage(data.user_entry);
        renderMessage(data);
    } catch (err) {
        renderMessage({ role: "assistant", name: "Error", text: err.message, timestamp: "—" });
    }
    setLoading(false);
}

async function toggleDebate() {
    if (debateRunning) {
        debateRunning = false;
        debateBtn.textContent = "Start Debate";
        return;
    }

    debateRunning = true;
    debateBtn.textContent = "Stop Debate";
    renderMessage({ role: "assistant", name: "System", text: "Continuous debate started.", timestamp: new Date().toLocaleTimeString() });

    while (debateRunning) {
        try {
            const resp = await fetch("/api/chat/single", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    target: "a",
                    profile_a: getProfile("a"),
                    profile_b: getProfile("b"),
                }),
            });
            if (!debateRunning) break;
            renderMessage(await resp.json());

            await new Promise((r) => setTimeout(r, 1500));
            if (!debateRunning) break;

            const resp2 = await fetch("/api/chat/single", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    target: "b",
                    profile_a: getProfile("a"),
                    profile_b: getProfile("b"),
                }),
            });
            if (!debateRunning) break;
            renderMessage(await resp2.json());

            await new Promise((r) => setTimeout(r, 2000));
        } catch (err) {
            renderMessage({ role: "assistant", name: "Error", text: err.message, timestamp: "—" });
            debateRunning = false;
            debateBtn.textContent = "Start Debate";
        }
    }
    debateBtn.textContent = "Start Debate";
}

async function newChat() {
    await fetch("/api/chat/new", { method: "POST" });
    chatContainer.innerHTML = "";
    uploadedFiles = { a: [], b: [] };
    document.getElementById("a-files").innerHTML = "";
    document.getElementById("b-files").innerHTML = "";
}

function clearUI() {
    chatContainer.innerHTML = "";
}

async function exportChat() {
    const resp = await fetch("/api/export");
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "convogreen_export.md";
    a.click();
    URL.revokeObjectURL(url);
}

// Init
updateButtonLabels();
