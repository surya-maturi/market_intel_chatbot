from app.graph.state import ChatState

CLARIFY_MESSAGE = (
    'I\'m not sure what you\'re asking. Try one of:\n'
    '- "Is <topic> trending right now?" (trend)\n'
    '- "What do people think about <topic>?" (sentiment)\n'
    '- "Tell me about <company> as a company" (competitor)'
)


async def clarify(state: ChatState) -> dict:
    return {"final_response_markdown": CLARIFY_MESSAGE}
