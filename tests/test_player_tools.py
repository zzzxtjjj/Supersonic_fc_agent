from agent.tools.player_tools import (
    get_player_profile,
    get_player_goals,
)


print("=== Test 1 ===")
print(get_player_profile("张谢童甲"))

print("=== Test 2 ===")
print(get_player_goals("干宸浩", "25-26"))

print("=== Test 3 ===")
print(get_player_profile("梅西"))

print("=== Test 4 ===")
print(get_player_goals("张谢童甲", "24-25"))