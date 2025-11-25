from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("training/model/saved_model")

def evaluate(code, concept):
    code_emb = model.encode(code)
    conc_emb = model.encode(concept)
    score = util.cos_sim(code_emb, conc_emb)
    return float(score)

if __name__ == "__main__":
    score = evaluate("def add(a,b): return a+b", "function, addition, parameters")
    print("Similarity Score:", score)
