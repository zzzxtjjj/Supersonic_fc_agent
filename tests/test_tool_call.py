from agent.core.agent_loop import run_agent


question = "张谢童甲25-26赛季射手榜排第几？"

answer = run_agent(question)

print("=== Question ===")
print(question)

print("=== Answer ===")
print(answer)