async function sendAiQuestion(){
    const userQuestion = document.getElementById("aiInput").value.trim();
    if(!userQuestion){
        alert("请输入你的问题！");
        return;
    }
    const resultBox = document.getElementById("aiResult");

    // 本地知识库优先检索
    const localAnswer = searchKnowledge(userQuestion);
    if(localAnswer !== null){
        resultBox.innerText = `【本地知识库】\n${localAnswer}`;
        return;
    }

    resultBox.innerText = "AI正在思考中……";
   try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 12000);

        const res = await fetch("http://127.0.0.1:5002/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: userQuestion }),
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        // 非流式：直接解析 JSON
        const data = await res.json();
        if (data.content) {
            resultBox.innerText = data.content;
        } else {
            resultBox.innerText = "（AI 返回为空）";
        }

    } catch (err) {
        if (err.name === "AbortError") {
            resultBox.innerText = " 请求超时，请检查后端服务或网络";
        } else {
            resultBox.innerText = " 请求失败：" + err.message;
            console.error(err);
        }
    }
}
