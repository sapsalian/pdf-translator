import pymupdf  # PyMuPDF를 사용하여 PDF 텍스트 추출
import json
from openai import OpenAI  # OpenAI GPT 호출을 위한 클라이언트
import time
from collections import defaultdict, Counter  # 용어 빈도 계산용
from concurrent.futures import ThreadPoolExecutor, as_completed  # 병렬 처리

client = OpenAI()

# 📄 PDF 문서의 전체 텍스트를 페이지 단위로 추출하는 함수
def extractTextByPage(pdf_path):
    pages_text = []
    with pymupdf.open(pdf_path) as doc:
        for i in range(len(doc)):
            text = doc[i].get_text().strip()
            pages_text.append({"page": i + 1, "text": text})
    return pages_text

# 🧠 번역 품질 향상을 위한 요약 + 용어집 생성 요청 프롬프트 생성 함수
def generateCombinedSystemPrompt(source_language="English", target_language="Korean"):
    return f'''You are an expert assistant whose job is to support high-quality and consistent translation from {source_language} to {target_language}.

You will be given a range of pages from a document. Your task has two parts:

1. 📄 **Summarize** the key content of each page in **no more than 3 sentences per page**.
   - Focus on the main message of the page.
   - Do not include minor details, formatting info, or examples unless they are essential.
   - Write clear, concise, and faithful summaries in {source_language}.
   - The summaries will be used as context for translation.

2. 📘 **Extract a glossary** of terms that require consistent translation.
   - Return a JSON object (`terms`) where:
     - Each **key** is an English term or phrase (can be multiple words) that appears multiple times or has different possible meanings in context.
     - Each **value** is its consistent translation in {target_language}.
   - Include terms that:
     - Might be translated inconsistently depending on context.
     - Are domain-specific technical terms, abstract concepts, or ambiguous expressions.
     - Appear very frequently in the document, even if their meaning is clear, to help enforce translation consistency.

   - For **named entities** (e.g., GPT-4, API, LLM, ChatGPT, OpenAI):
     - **Do not translate them**. Keep them exactly as-is. Their value should equal the key.

3. 🧾 **Output Format**
Return only a JSON object like this (do not include any explanation, commentary, or extra text):

{{
  "terms": {{
    "embedding": "임베딩",
    "language model": "언어 모델",
    "GPT-4": "GPT-4"
  }},
  "summaries": [
    {{ "page": 1, "summary": "..." }},
    {{ "page": 2, "summary": "..." }}
  ]
}}

Do not change the structure.
Do not return anything except a valid JSON object with exactly two top-level keys: `terms` and `summaries`.
'''



# 🤖 GPT 호출: 각 청크에 대해 요약과 용어집을 생성하는 함수
def summarizeChunkWithTerms(pages, source_language="English", target_language="Korean"):
    system_prompt = generateCombinedSystemPrompt(source_language, target_language)
    input_text = "\n\n".join([f"Page {p['page']}:\n{p['text']}" for p in pages])

    # GPT 호출 시, JSON 스키마 명시하여 요약 + 용어집 구조 강제
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        # temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "summary_with_terms",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "summaries": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "page": {"type": "integer"},
                                    "summary": {"type": "string"}
                                },
                                "required": ["page", "summary"],
                                "additionalProperties": False
                            }
                        },
                        "terms": {
                            "type": "object",
                            "description": "A glossary mapping English terms to their Korean translations.",
                            "properties": {},
                            "additionalProperties": {"type": "string"}
                        }

                    },
                    "required": ["summaries", "terms"],
                    "additionalProperties": False
                }
            }
        }
    )

    parsed = json.loads(response.choices[0].message.content)
    return parsed["summaries"], parsed["terms"]

# 🧠 청크별로 수집된 용어집을 병합하는 함수 (가장 자주 등장한 번역 선택)
def mergeGlossaries(glossaries):
    term_freq = defaultdict(Counter)
    for glossary in glossaries:
        for key, val in glossary.items():
            term_freq[key][val] += 1
    # 가장 많이 등장한 번역을 선택
    final_terms = {
        key: counter.most_common(1)[0][0] for key, counter in term_freq.items()
    }
    return final_terms

# 📘 전체 PDF를 순차적으로 요약하고 용어집을 추출하는 함수
def summarizePdfInChunks(pdf_path, chunk_size=7, source_language="English", target_language="Korean"):
    # PDF에서 모든 페이지의 텍스트를 추출
    all_pages = extractTextByPage(pdf_path)
    all_summaries = []  # 전체 요약 저장용 리스트
    all_glossaries = []  # 전체 용어집 저장용 리스트

    # chunk_size만큼 페이지를 잘라서 반복 처리
    for i in range(0, len(all_pages), chunk_size):
        chunk = all_pages[i:i + chunk_size]  # 현재 청크
        page_numbers = [p["page"] for p in chunk]  # 청크 내 페이지 번호 목록
        page_range = f"{page_numbers[0]}–{page_numbers[-1]}"
        print(f"📘 Summarizing pages {page_range}...")

        try:
            # GPT로 요약과 용어집 생성 요청
            summaries, glossary = summarizeChunkWithTerms(chunk, source_language, target_language)
            summary_dict = {item["page"]: item["summary"] for item in summaries}  # 페이지 번호 기반 딕셔너리 구성

            # 순서 유지하며 누락된 페이지는 빈 문자열로 처리
            ordered = [{"page": page, "summary": summary_dict.get(page, "")} for page in page_numbers]
            all_summaries.extend(ordered)
            all_glossaries.append(glossary)
        except Exception as e:
            # 에러 발생 시 모든 페이지에 빈 요약 할당
            print(f"❌ Failed to summarize pages {page_range}: {e}")
            all_summaries.extend([{"page": page, "summary": ""} for page in page_numbers])

    # 청크별 용어집 병합 (중복 키는 가장 빈도 높은 번역 선택)
    merged_glossary = mergeGlossaries(all_glossaries)

    # 정렬된 요약과 최종 용어집 반환
    return {"term_dict": merged_glossary, "summaries": sorted(all_summaries, key=lambda x: x["page"])}

# ⚡ 전체 PDF를 병렬로 처리하며 요약과 용어집을 생성하는 함수
def summarizePdfInChunksParallel(pdf_path, chunk_size=7, max_workers=30, source_language="English", target_language="Korean"):
    all_pages = extractTextByPage(pdf_path)  # 모든 페이지 텍스트 추출
    chunks = [all_pages[i:i + chunk_size] for i in range(0, len(all_pages), chunk_size)]  # 청크 단위로 분할
    results = []  # 병렬 결과 수집용 리스트
    all_glossaries = []  # 병렬 생성된 용어집 리스트

    # 개별 청크를 처리하는 내부 함수
    def processChunk(chunk):
        page_numbers = [p["page"] for p in chunk]
        page_range = f"{page_numbers[0]}–{page_numbers[-1]}"
        print(f"📘 [Thread] Summarizing pages {page_range}...")

        try:
            # GPT 호출: 요약 및 용어집 생성
            summaries, glossary = summarizeChunkWithTerms(chunk, source_language, target_language)
            summary_dict = {item["page"]: item["summary"] for item in summaries}
            ordered = [{"page": page, "summary": summary_dict.get(page, "")} for page in page_numbers]
            all_glossaries.append(glossary)
            return ordered
        except Exception as e:
            # 실패 시 빈 요약으로 대체
            print(f"❌ [Thread] Failed pages {page_range}: {e}")
            return [{"page": page, "summary": ""} for page in page_numbers]

    # ThreadPoolExecutor를 사용하여 병렬 처리 수행
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(processChunk, chunk) for chunk in chunks]  # 작업 제출
        for future in as_completed(futures):  # 완료된 작업부터 결과 수집
            results.extend(future.result())

    # 전체 용어집 병합
    merged_glossary = mergeGlossaries(all_glossaries)

    # 정렬된 요약과 용어집 반환
    return {"term_dict": merged_glossary, "summaries": sorted(results, key=lambda x: x["page"])}





def summarizeTest(pdf_path, source_language="English", target_language="Korean"):
    # 전체 PDF를 병렬로 처리하여 요약 및 용어집 생성
    result = summarizePdfInChunksParallel(
        pdf_path,
        chunk_size=7,
        max_workers=30,
        source_language=source_language,
        target_language=target_language
    )

    summaries = result["summaries"]
    terms = result["term_dict"]

    # 요약 결과 출력
    for item in summaries:
        page = item["page"]
        summary = item["summary"]
        print(f"\n✅ Page {page}")
        print(f"   {summary}")

    # 용어집 출력
    print("\n📘 Glossary Terms")
    for term, translation in terms.items():
        print(f" - {term} → {translation}")


        