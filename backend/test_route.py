import asyncio
from app.mcp.intent_classifier import IntentResult
from app.mcp.router import route_to_tools

async def main():
    intent = IntentResult(
        intent="nearby_clinic",
        entities={"location": "nearby clinic location"},
        raw_transcript="can you give some details of nearby clinic location"
    )
    # mock redis
    class MockRedis: pass
    outputs = await route_to_tools(intent, MockRedis(), MockRedis(), "123")
    print(outputs[0].model_dump())

if __name__ == "__main__":
    asyncio.run(main())
