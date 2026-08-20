import json

from langchain_core.messages import AIMessage


def safety_json_output(ai_content: AIMessage) -> AIMessage:
    raw_content = ai_content.content


    if isinstance(raw_content, list):
        text_parts = []
        for block in raw_content:
            if isinstance(block, dict):
                text_parts.append(str(block.get("text", block.get("content", ""))))
            elif isinstance(block, str):
                text_parts.append(block)
            else:
                text_parts.append(str(block))
        text = " ".join(text_parts)
    elif isinstance(raw_content, str):
        text = raw_content
    elif raw_content is None:
        text = ""
    else:
        text = str(raw_content)

    safe_fallback = '{"final_intent": "UNKNOWN", "final_sentiment": "neutral", "extracted_entities": {}, "is_misunderstanding": true}'

    if not text.strip():
        return AIMessage(content=safe_fallback)


    brackets = 0
    start_idx = -1

    for i, char in enumerate(text):
        if char == '{':
            if brackets == 0: start_idx = i
            brackets += 1
        elif char == '}':
            brackets -= 1
            if brackets == 0 and start_idx != -1:
                candidate = text[start_idx:i + 1]
                if '"final_intent"' in candidate:
                    try:
                        json.loads(candidate)
                        return AIMessage(content=candidate)
                    except json.JSONDecodeError:
                        pass

    return AIMessage(content=safe_fallback)



