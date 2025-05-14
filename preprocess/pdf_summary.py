import pymupdf  # PyMuPDF
import json
from openai import OpenAI
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


client = OpenAI()

# 📄 PDF 문서의 전체 텍스트를 페이지 단위로 추출하는 함수
def extractTextByPage(pdf_path):
    """
    pymupdf로 PDF를 열고 각 페이지의 텍스트를 추출하여 리스트로 반환합니다.
    각 항목은 {'page': 페이지 번호, 'text': 텍스트} 형식입니다.
    """
    pages_text = []

    # PDF 문서를 열고 with 문으로 자동 닫기 처리
    with pymupdf.open(pdf_path) as doc:
        for i in range(len(doc)):
            page = doc[i]
            text = page.get_text()  # 기본값 "text"는 줄바꿈 포함된 일반 텍스트
            pages_text.append({
                "page": i + 1,  # 사람 기준의 1-based page 번호
                "text": text.strip()
            })

    return pages_text


def generateSystemPrompt(summary_language="English"):
    """
    시스템 프롬프트를 생성합니다.
    summary_language: 요약 결과 언어 ("English", "Korean" 등)
    """
    return f'''You are a professional assistant designed to generate high-quality contextual summaries for each page of a PDF document. Your goal is to help improve machine translation quality by providing concise, informative summaries that preserve the core meaning of each page.

For each page:
- Read the content carefully and understand the main idea.
- Write a summary in {summary_language} using no more than 3 sentences.
- Focus on conveying the key message, avoiding unnecessary detail or repetition.
- Be clear, concise, and faithful to the original content.

The output should be in JSON format, with the following structure:

{{
  "summaries": [
    {{
      "page": 1,
      "summary": "This page explains..."
    }},
    ...
  ]
}}

- The top-level JSON object must contain a key named "summaries".
- "summaries" must be a list of summary objects.
- Each summary object must include "page" (integer) and "summary" (string).
- Do not include any keys other than "summaries" at the top level.

Do not translate. Do not analyze formatting. Do not paraphrase unnecessarily. Just summarize the core message per page.'''


# 🤖 GPT 모델에게 하나의 청크(예: 10페이지)를 요약 요청하는 함수
def summarizePageChunk(pages, summary_language="English"):
    """
    페이지 리스트를 받아 GPT에게 요청하고, 지정한 언어로 요약을 받습니다.
    응답은 {"summaries": [...]} 형태의 문자열이므로, JSON 파싱 후 summaries 리스트를 반환합니다.
    """
    # 시스템 프롬프트 생성 (요약 언어 지정 포함)
    system_prompt = generateSystemPrompt(summary_language)

    # 페이지별 입력 텍스트 구성
    input_text = "\n\n".join([
        f"Page {p['page']}:\n{p['text']}" for p in pages
    ])

    # GPT 모델 호출
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "summary_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "summaries": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "page": { "type": "integer" },
                                    "summary": { "type": "string" }
                                },
                                "required": ["page", "summary"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["summaries"],
                    "additionalProperties": False
                }
            }
        }
    )

    # 응답의 content는 문자열 형태의 JSON → Python 객체로 파싱
    parsed = json.loads(response.choices[0].message.content)

    # "summaries" 키를 반환
    return parsed["summaries"]




def summarizePdfInChunks(pdf_path, summary_language="English", chunk_size=15):
    """
    전체 PDF 파일을 여러 페이지 단위로 분할하여 GPT 모델에게 요약을 요청합니다.
    - chunk_size 매개변수를 통해 한 번에 몇 페이지씩 요약할지 조절할 수 있습니다.
    - 각 블록에 대해 요약이 일부 누락된 경우, 해당 위치에 빈 summary를 넣습니다.
    
    Returns:
        List[Dict]: {"page": int, "summary": str} 리스트 (page 오름차순)
    """
    all_pages = extractTextByPage(pdf_path)
    all_summaries = []

    for i in range(0, len(all_pages), chunk_size):
        chunk = all_pages[i:i+chunk_size]
        page_numbers = [p["page"] for p in chunk]
        page_range = f"{page_numbers[0]}–{page_numbers[-1]}"
        print(f"📘 Summarizing pages {page_range}...")

        try:
            # GPT 응답 요청
            summaries = summarizePageChunk(chunk, summary_language)
            summary_dict = {item["page"]: item["summary"] for item in summaries}

            # 👉 순서를 보장하며 누락된 페이지는 ""로 채움
            ordered_chunk_summary = []
            for page in page_numbers:
                ordered_chunk_summary.append({
                    "page": page,
                    "summary": summary_dict.get(page, "")
                })

            all_summaries.extend(ordered_chunk_summary)
            print(f"✅ Completed chunk {page_range} with {len(ordered_chunk_summary)} summaries")

        except Exception as e:
            print(f"❌ Failed to summarize pages {page_range}: {e}")
            # 전체 청크 실패 시 전부 빈 summary
            for page in page_numbers:
                all_summaries.append({
                    "page": page,
                    "summary": ""
                })

    return all_summaries



def summarizePdfInChunksParallel(pdf_path, summary_language="English", chunk_size=15, max_workers=30):
    """
    PDF를 chunk 단위로 나누고 각 청크를 병렬로 요약합니다.
    실패한 청크는 각 페이지에 빈 summary를 삽입합니다.

    Parameters:
        pdf_path (str): PDF 파일 경로
        summary_language (str): 요약 언어
        chunk_size (int): chunk 당 페이지 수
        max_workers (int): 병렬 작업 최대 쓰레드 수

    Returns:
        List[Dict]: {"page": int, "summary": str} 리스트
    """
    all_pages = extractTextByPage(pdf_path)

    # chunk 단위로 분할
    chunks = [
        all_pages[i:i+chunk_size]
        for i in range(0, len(all_pages), chunk_size)
    ]

    results = []

    def processChunk(chunk):
        page_numbers = [p["page"] for p in chunk]
        page_range = f"{page_numbers[0]}–{page_numbers[-1]}"
        print(f"📘 [Thread] Summarizing pages {page_range}...")

        try:
            summaries = summarizePageChunk(chunk, summary_language)
            summary_dict = {item["page"]: item["summary"] for item in summaries}
            ordered_chunk_summary = [
                {"page": page, "summary": summary_dict.get(page, "")}
                for page in page_numbers
            ]
            print(f"✅ [Thread] Completed pages {page_range}")
            return ordered_chunk_summary

        except Exception as e:
            print(f"❌ [Thread] Failed pages {page_range}: {e}")
            return [{"page": page, "summary": ""} for page in page_numbers]

    # 병렬 실행
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(processChunk, chunk) for chunk in chunks]

        for future in as_completed(futures):
            results.extend(future.result())

    # 정렬 보장
    return sorted(results, key=lambda x: x["page"])





def summarizeTest(pdf_path, summary_language="English"):
    pages = extractTextByPage(pdf_path)
    summaries = summarizePageChunk(pages, summary_language)
    
    for item in summaries:
        page = item["page"]
        summary = item["summary"]
        print(f"\n✅ Page {page}")
        print(f"   {summary}")
        