// In your frontend JavaScript (chat.js or script.js)
async function sendMessage(message) {
    try {
        const response = await fetch('http://localhost:5000/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: message })
        });
        
        const data = await response.json();
        return data.answer;
    } catch (error) {
        console.error('Error sending message:', error);
        return "Gabim në lidhje me serverin.";
    }
}