import json
import os
import requests
from google import genai
from google.genai import types

class T2NProcessor:
    def __init__(self):
        # Allow connecting to local Ollama instance (default to the Shared-Schema env variable)
        env_url = os.environ.get("LOCAL_LLM_API_URL")
        self.ollama_api_url = env_url if env_url else "http://localhost:11434/api/generate"

        # Setup Gemini Client
        self.gemini_keys = os.environ.get("GEMINI_API_KEYS", "").split(",")
        self.current_key_idx = 0
        if self.gemini_keys and self.gemini_keys[0]:
            self.gemini_client = genai.Client(api_key=self.gemini_keys[self.current_key_idx].strip())
        else:
            self.gemini_client = None

        self.system_prompt = """
        You are the Textbook2Notes (T2N) preprocessor.
        Analyze the following educational text. Extract key concepts and assign the correct 108 Curriculum 'eds_x_code'.
        You MUST output ONLY a valid JSON object with the following schema:
        {
            "title": "String",
            "is_out_of_matrix": Boolean,
            "nodes": [
                {
                    "concept": "String",
                    "details": "String",
                    "eds_x_code": "String (e.g. Bc-Ⅳ-3)"
                }
            ]
        }
        """

    def process_text(self, text_input: str, engine: str = "auto") -> dict:
        """
        Main entry point for UI. Handles routing and fallbacks based on engine selection.
        engine options: 'auto' (Gemini -> Ollama -> Sim), 'gemini', 'ollama', 'simulation'
        """
        if engine in ["auto", "gemini"]:
            if self.gemini_keys and self.gemini_keys[0]:
                print("[T2N] Attempting Gemini API...")
                result = self.invoke_gemini_llm(text_input)
                if result:
                    return result
                if engine == "gemini":
                    return self.simulate_llm_parsing(text_input) # Fallback to sim if strictly gemini requested but failed
            elif engine == "gemini":
                print("[T2N] Gemini API Key not configured. Falling back to simulation.")
                return self.simulate_llm_parsing(text_input)

        if engine in ["auto", "ollama"]:
            print("[T2N] Attempting Ollama Local API...")
            result = self.invoke_ollama_llm(text_input)
            if result:
                return result

        print("[T2N] Falling back to Simulation.")
        return self.simulate_llm_parsing(text_input)

    def invoke_gemini_llm(self, text_input: str) -> dict:
        """Integration with Google Gemini API, including key rotation retry."""
        if not self.gemini_client:
            return None

        max_retries = len(self.gemini_keys) if self.gemini_keys else 1

        for attempt in range(max_retries):
            try:
                response = self.gemini_client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=text_input,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_prompt,
                        response_mime_type="application/json",
                    ),
                )
                return json.loads(response.text)

            except Exception as e:
                print(f"[Gemini API Error - Attempt {attempt+1}/{max_retries}] {e}")
                # Rotate key on ResourceExhausted (429)
                if "429" in str(e) and len(self.gemini_keys) > 1:
                    print("Rate limit hit. Rotating to next key and retrying...")
                    self.current_key_idx = (self.current_key_idx + 1) % len(self.gemini_keys)
                    self.gemini_client = genai.Client(api_key=self.gemini_keys[self.current_key_idx].strip())
                else:
                    # Break on other errors (e.g., auth failure, bad request)
                    break

        return None

    def invoke_ollama_llm(self, text_input: str, model_name: str = "llama3") -> dict:
        """
        Real integration with local Ollama LLM API (Phase 4).
        It forces the model to output the JSON schema.
        """
        prompt = self.system_prompt + f"\n\nText to analyze:\n{text_input}"

        try:
            response = requests.post(
                self.ollama_api_url,
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False
                },
                timeout=10
            )
            if response.status_code == 200:
                result_text = response.json().get('response', '{}')
                return json.loads(result_text)
            else:
                print(f"LLM API Error: {response.status_code}")
                return self.simulate_llm_parsing(text_input)
        except Exception as e:
            print(f"Failed to connect to Local LLM at {self.ollama_api_url}: {e}. Falling back to simulation.")
            return None

    def simulate_llm_parsing(self, text_input: str) -> dict:
        """
        Simulates the T2N LLM process. It assumes the LLM has used `matrix_parser`
        to attach the correct `eds_x_code` and output JSON.
        """
        # In reality, this would be an API call to an LLM enforcing a JSON schema.
        # For now, we simulate the structured output based on the new spec.
        is_out_of_matrix = "大學" in text_input or "微積分" in text_input

        simulated_output = {
            "title": "光合作用筆記",
            "is_out_of_matrix": is_out_of_matrix,
            "nodes": [
                {
                    "concept": "光反應",
                    "details": "在葉綠餅發生，需要光，產生ATP與NADPH。",
                    "eds_x_code": "Bc-IV-3"
                },
                {
                    "concept": "碳反應(暗反應)",
                    "details": "在葉綠體基質發生，不需要光，利用ATP與NADPH將CO2轉為葡萄糖。",
                    "eds_x_code": "Bc-IV-3"
                }
            ]
        }
        return simulated_output

    def render_markdown(self, json_data: dict) -> str:
        """
        Converts the T2N JSON output into a beautifully rendered Markdown string.
        """
        md_lines = []
        md_lines.append(f"# {json_data.get('title', 'T2N 學習筆記')}")

        if json_data.get('is_out_of_matrix'):
            md_lines.append("> ⚠️ **注意**：部分內容已超出 108 課綱範圍。")

        md_lines.append("\n## 核心概念拆解\n")

        for node in json_data.get('nodes', []):
            code_badge = f"`{node['eds_x_code']}`" if node.get('eds_x_code') else "`無對應代碼`"
            md_lines.append(f"### {node.get('concept', '未命名概念')} {code_badge}")
            md_lines.append(f"{node.get('details', '')}\n")

        return "\n".join(md_lines)

    def render_html(self, json_data: dict) -> str:
        """
        Converts the T2N JSON output into a styled HTML string.
        """
        title = json_data.get('title', 'T2N 學習筆記')
        html_lines = [
            f"<div style='font-family: sans-serif; padding: 20px; border-radius: 8px; background-color: #f9f9f9; color: #333;'>",
            f"  <h1 style='color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;'>{title}</h1>"
        ]

        if json_data.get('is_out_of_matrix'):
            html_lines.append("  <div style='background-color: #fff3cd; color: #856404; padding: 10px; border-left: 5px solid #ffeeba; margin-bottom: 15px;'>⚠️ <b>注意</b>：部分內容已超出 108 課綱範圍。</div>")

        html_lines.append("  <h2 style='color: #2980b9; margin-top: 20px;'>核心概念拆解</h2>")
        html_lines.append("  <ul style='list-style-type: none; padding-left: 0;'>")

        for node in json_data.get('nodes', []):
            concept = node.get('concept', '未命名概念')
            code = node.get('eds_x_code', '')
            details = node.get('details', '')

            code_badge = f"<span style='background-color: #e8f4f8; color: #117a8b; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; margin-left: 10px;'>{code}</span>" if code else ""

            html_lines.append(f"    <li style='background: white; margin-bottom: 15px; padding: 15px; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>")
            html_lines.append(f"      <h3 style='margin-top: 0; color: #34495e;'>{concept} {code_badge}</h3>")
            html_lines.append(f"      <p style='margin-bottom: 0; line-height: 1.6;'>{details}</p>")
            html_lines.append(f"    </li>")

        html_lines.append("  </ul>")
        html_lines.append("</div>")

        return "\n".join(html_lines)

    def generate_quiz(self, json_data: dict) -> str:
        """
        Generates a post-study quiz based on the extracted JSON nodes.
        """
        # In a real app, this would query an LLM to generate distractor options
        # based on the concept and details.
        quiz_lines = ["# 課後小測驗\n"]
        for i, node in enumerate(json_data.get('nodes', [])):
            concept = node.get('concept', '')
            details = node.get('details', '')
            code = node.get('eds_x_code', '')

            quiz_lines.append(f"**Q{i+1} [{code}] 關於「{concept}」，下列敘述何者錯誤？**")
            quiz_lines.append(f"- (A) {details} (這是正確敘述，請AI生成錯誤選項做為B,C,D)")
            quiz_lines.append("- (B) ...")
            quiz_lines.append("- (C) ...")
            quiz_lines.append("- (D) ...\n")

        return "\n".join(quiz_lines)

    def generate_mindmap(self, json_data: dict) -> str:
        """
        Converts the T2N JSON nodes into Mermaid.js mindmap syntax (Phase 6-B).
        """
        title = json_data.get('title', 'Central Concept')
        mermaid_lines = ["```mermaid", "mindmap", f"  root(({title}))"]

        for node in json_data.get('nodes', []):
            concept = node.get('concept', '')
            code = node.get('eds_x_code', '')
            # Clean up concept for mermaid syntax
            clean_concept = concept.replace("(", " ").replace(")", " ")
            mermaid_lines.append(f"    {clean_concept}")
            if code:
                mermaid_lines.append(f"      ({code})")

        mermaid_lines.append("```")
        return "\n".join(mermaid_lines)

if __name__ == "__main__":
    processor = T2NProcessor()

    # 1. Simulate Parsing
    print("=== 1. T2N JSON Output ===")
    json_result = processor.simulate_llm_parsing("光合作用分為光反應與暗反應...")
    print(json.dumps(json_result, indent=2, ensure_ascii=False))

    # 2. Render Markdown
    print("\n=== 2. T2N Markdown Rendering ===")
    print(processor.render_markdown(json_result))

    # 3. Generate Quiz
    print("\n=== 3. T2N Quiz Generation ===")
    print(processor.generate_quiz(json_result))

    # 4. Generate Mind Map
    print("\n=== 4. T2N Mind Map (Mermaid) ===")
    print(processor.generate_mindmap(json_result))
