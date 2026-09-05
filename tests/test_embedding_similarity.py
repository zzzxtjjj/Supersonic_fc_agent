from agent.rag.embedder import embed_text
from agent.rag.similarity import cosine_similarity


text_a = "张谢童甲速度快，擅长边路突破"

text_b = "张谢童甲爆发力出色，经常利用速度突破边路防线"

text_c = "超音速球队文化强调团结和传承"

vector_a = embed_text(text_a)
vector_b = embed_text(text_b)
vector_c = embed_text(text_c)

similarity_ab = cosine_similarity(vector_a, vector_b)

similarity_ac = cosine_similarity(vector_a, vector_c)

print("A-B:", similarity_ab)
print("A-C:", similarity_ac)